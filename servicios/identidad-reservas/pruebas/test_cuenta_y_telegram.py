import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db import Base, get_db
from app.main import create_app
from app.services import telegram_bot
from app.services.email_sender import clear_dev_outbox, get_last_dev_code

CLAVE = "ClaveSegura!2026"
NUEVA = "OtraClave#2027x"


@pytest.fixture()
def client(monkeypatch):
    clear_dev_outbox()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    app = create_app(init_local_db=False)

    def override_get_db():
        db = Local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    enviados: list[tuple[str, str]] = []
    monkeypatch.setattr(telegram_bot, "bot_username", lambda: "ExpoNexoBot")
    monkeypatch.setattr("app.routers.telegram.send_message", lambda chat, texto: enviados.append((chat, texto)) or True)
    with TestClient(app) as test_client:
        test_client.telegram_enviados = enviados
        yield test_client


def _ingresar(client: TestClient, correo: str, clave: str) -> dict:
    paso1 = client.post("/v1/sesion/ingreso", json={"correo": correo, "contrasena": clave})
    assert paso1.status_code == 200, paso1.text
    pase = paso1.json()["pase_segundo_paso"]
    client.post("/v1/sesion/codigo-correo", headers={"Authorization": f"Bearer {pase}"})
    codigo = get_last_dev_code(correo, "ingreso")
    paso2 = client.post(
        "/v1/sesion/segundo-paso",
        headers={"Authorization": f"Bearer {pase}"},
        json={"metodo": "correo", "codigo": codigo},
    )
    assert paso2.status_code == 200, paso2.text
    return paso2.json()


def _registrar(client: TestClient, correo: str) -> None:
    res = client.post("/v1/cuentas", json={"correo": correo, "nombre": "Ana Pérez", "contrasena": CLAVE})
    assert res.status_code == 201


def test_cambio_de_contrasena_cierra_las_otras_sesiones(client: TestClient):
    _registrar(client, "ana@feria.co")
    actual = _ingresar(client, "ana@feria.co", CLAVE)
    otra = _ingresar(client, "ana@feria.co", CLAVE)
    cabecera = {"Authorization": f"Bearer {actual['token_acceso']}"}

    mala = client.put("/v1/perfil/contrasena", headers=cabecera,
                      json={"contrasena_actual": "NoEs!2026xx", "nueva_contrasena": NUEVA})
    assert mala.status_code == 400
    debil = client.put("/v1/perfil/contrasena", headers=cabecera,
                       json={"contrasena_actual": CLAVE, "nueva_contrasena": "solominusculas"})
    assert debil.status_code == 422

    ok = client.put("/v1/perfil/contrasena", headers=cabecera, json={
        "contrasena_actual": CLAVE, "nueva_contrasena": NUEVA, "token_refresco": actual["token_refresco"]})
    assert ok.status_code == 200
    assert ok.json()["sesiones_cerradas"] == 1

    # La sesión del otro dispositivo quedó cerrada; la actual sigue viva
    assert client.post("/v1/sesion/refrescar", json={"token_refresco": otra["token_refresco"]}).status_code == 401
    assert client.post("/v1/sesion/refrescar", json={"token_refresco": actual["token_refresco"]}).status_code == 200
    assert client.post("/v1/sesion/ingreso", json={"correo": "ana@feria.co", "contrasena": NUEVA}).status_code == 200


def test_recuperacion_cierra_sesiones_levanta_bloqueo_y_limita_intentos(client: TestClient):
    _registrar(client, "luis@feria.co")
    sesion = _ingresar(client, "luis@feria.co", CLAVE)
    for _ in range(get_settings().mfa_max_attempts):
        client.post("/v1/sesion/ingreso", json={"correo": "luis@feria.co", "contrasena": "Mala!Clave2026"})
    assert client.post("/v1/sesion/ingreso", json={"correo": "luis@feria.co", "contrasena": CLAVE}).status_code == 429

    pedir = client.post("/v1/cuentas/recuperar", json={"correo": "luis@feria.co"})
    assert pedir.status_code == 200
    # La respuesta es la misma aunque la cuenta no exista
    assert client.post("/v1/cuentas/recuperar", json={"correo": "nadie@feria.co"}).json() == pedir.json()
    codigo = get_last_dev_code("luis@feria.co", "recuperar")

    ok = client.post("/v1/cuentas/recuperar", json={"correo": "luis@feria.co", "codigo": codigo, "nueva_contrasena": NUEVA})
    assert ok.status_code == 200
    assert client.post("/v1/sesion/refrescar", json={"token_refresco": sesion["token_refresco"]}).status_code == 401
    assert client.post("/v1/sesion/ingreso", json={"correo": "luis@feria.co", "contrasena": NUEVA}).status_code == 200

    # Un código nuevo deja de servir después de agotar los intentos
    client.post("/v1/cuentas/recuperar", json={"correo": "luis@feria.co"})
    codigo2 = get_last_dev_code("luis@feria.co", "recuperar")
    for _ in range(get_settings().mfa_max_attempts):
        client.post("/v1/cuentas/recuperar", json={"correo": "luis@feria.co", "codigo": "000000", "nueva_contrasena": NUEVA + "1"})
    agotado = client.post("/v1/cuentas/recuperar", json={"correo": "luis@feria.co", "codigo": codigo2, "nueva_contrasena": NUEVA + "1"})
    assert agotado.status_code == 400


def test_vinculacion_de_telegram_y_contactos_internos(client: TestClient):
    _registrar(client, "sofia@feria.co")
    tokens = _ingresar(client, "sofia@feria.co", CLAVE)
    cabecera = {"Authorization": f"Bearer {tokens['token_acceso']}"}

    enlace = client.post("/v1/perfil/telegram", headers=cabecera)
    assert enlace.status_code == 200
    codigo = re.search(r"start=([A-Za-z0-9_-]+)$", enlace.json()["enlace"]).group(1)
    assert enlace.json()["enlace"].startswith("https://t.me/ExpoNexoBot?start=")

    mensaje = {"message": {"chat": {"id": 987654, "type": "private"}, "text": f"/start {codigo}"}}
    # Sin el token secreto del webhook no se vincula nada
    client.post("/v1/telegram/webhook", json=mensaje)
    assert client.get("/v1/perfil/seguridad", headers=cabecera).json()["telegram_vinculado"] is False

    secreto = {"X-Telegram-Bot-Api-Secret-Token": telegram_bot.webhook_secret()}
    assert client.post("/v1/telegram/webhook", json=mensaje, headers=secreto).status_code == 200
    assert client.get("/v1/perfil/seguridad", headers=cabecera).json()["telegram_vinculado"] is True
    assert client.telegram_enviados[-1][0] == "987654"

    # El mismo código no sirve dos veces
    client.post("/v1/telegram/webhook", json={"message": {"chat": {"id": 1, "type": "private"}, "text": f"/start {codigo}"}}, headers=secreto)
    assert "venció" in client.telegram_enviados[-1][1]

    servicio = client.post("/v1/sesion/servicio", json={"servicio": "avisos", "secreto_interno": get_settings().internal_secret})
    token_servicio = servicio.json()["token_servicio"]
    assert client.get("/v1/interno/contactos?correos=sofia@feria.co").status_code == 401
    contactos = client.get("/v1/interno/contactos?correos=SOFIA@feria.co",
                           headers={"Authorization": f"Bearer {token_servicio}"}).json()
    assert contactos[0]["telegram_chat_id"] == "987654"
    assert contactos[0]["nombre"] == "Ana Pérez"

    quitar = client.delete("/v1/perfil/telegram", headers=cabecera)
    assert quitar.json()["telegram_vinculado"] is False
