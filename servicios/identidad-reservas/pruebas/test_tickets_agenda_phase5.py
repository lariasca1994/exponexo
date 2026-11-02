from collections.abc import Generator
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import create_app
from app.models.identity import OutboxEvent, User
from app.security.passwords import hash_password
from app.security.tokens import create_access_token, create_service_token


@pytest.fixture()
def test_db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_db: Session) -> Generator[TestClient, None, None]:
    app = create_app(init_local_db=False)

    def override_get_db() -> Generator[Session, None, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as tc:
        yield tc


def _seed_user(db: Session, email: str, role: str, name: str) -> tuple[User, str]:
    u = User(
        correo=email,
        nombre=name,
        hash_contrasena=hash_password("ClaveSegura!2026"),
        rol=role,
        activo=True,
        correo_verificado=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    token, _ = create_access_token(u.id, u.correo, u.nombre, u.rol)
    return u, token


def test_ticket_qr_lifecycle_and_tamper_protection(client: TestClient, test_db: Session) -> None:
    _, admin_token = _seed_user(test_db, "admin@exponexo.co", "administrador", "Admin Feria")
    _, staff_token = _seed_user(test_db, "puerta@exponexo.co", "personal", "Guardia Puerta")
    _, visitor_token = _seed_user(test_db, "visitante@exponexo.co", "visitante", "Carlos Visitante")
    svc_token, _ = create_service_token("eventos-repartidor")

    now = datetime.now(timezone.utc)
    ev_res = client.post(
        "/v1/admin/eventos",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "nombre": "Feria Industrial QR",
            "slug": "feria-industrial-qr",
            "descripcion": "Feria industrial.",
            "inicio": (now + timedelta(days=2)).isoformat(),
            "fin": (now + timedelta(days=5)).isoformat(),
            "estado": "publicado",
            "precio_entrada": "45000.00",
            "aforo": 2000,
        },
    )
    assert ev_res.status_code == 201
    event_id = ev_res.json()["id"]

    # 1. Visitante compra entrada
    buy_res = client.post(
        f"/v1/eventos/{event_id}/entradas",
        headers={"Authorization": f"Bearer {visitor_token}"},
        json={"tipo": "negocios"},
    )
    assert buy_res.status_code == 201
    ticket_id = buy_res.json()["id"]
    assert buy_res.json()["estado"] == "pendiente_pago"
    assert buy_res.json()["codigo_qr"] is None

    # 2. Repartidor activa la entrada tras pago.aprobado (idempotente)
    act_res = client.post(
        f"/v1/interno/entradas/{ticket_id}/activar",
        headers={"Authorization": f"Bearer {svc_token}"},
        json={"orden_pago_id": "ord-ent-001", "evento_id": "evt-pago-ent-001"},
    )
    assert act_res.status_code == 200
    qr_code = act_res.json()["codigo_qr"]
    assert act_res.json()["estado"] == "activa"
    assert qr_code is not None and qr_code.startswith("EXN1.")

    # Llamada repetida con el mismo evento_id no duplica ni falla
    act_dup = client.post(
        f"/v1/interno/entradas/{ticket_id}/activar",
        headers={"Authorization": f"Bearer {svc_token}"},
        json={"orden_pago_id": "ord-ent-001", "evento_id": "evt-pago-ent-001"},
    )
    assert act_dup.status_code == 200
    assert act_dup.json()["codigo_qr"] == qr_code

    # 3. Intento con QR alterado -> 400
    tampered_qr = qr_code[:-4] + "XXXX"
    bad_scan = client.post(
        "/v1/entradas/validar-qr",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"codigo_qr": tampered_qr, "dispositivo_id": "torniquete-norte-1"},
    )
    assert bad_scan.status_code == 400

    # 4. Primera lectura válida en puerta -> 200
    good_scan = client.post(
        "/v1/entradas/validar-qr",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"codigo_qr": qr_code, "dispositivo_id": "torniquete-norte-1"},
    )
    assert good_scan.status_code == 200
    assert good_scan.json()["estado"] == "usada"

    # 5. Segunda lectura del mismo QR -> 409 Conflict
    second_scan = client.post(
        "/v1/entradas/validar-qr",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"codigo_qr": qr_code, "dispositivo_id": "torniquete-norte-2"},
    )
    assert second_scan.status_code == 409


def test_business_appointments_overlap_room_assignment_and_outbox(
    client: TestClient,
    test_db: Session,
) -> None:
    _, admin_token = _seed_user(test_db, "admin2@exponexo.co", "administrador", "Admin Agenda")
    host, host_token = _seed_user(test_db, "anfitrion@empresa.co", "expositor", "Laura Expositora")
    _, vis1_token = _seed_user(test_db, "vis1@comprador.co", "visitante", "Pedro Comprador")
    _, vis2_token = _seed_user(test_db, "vis2@comprador.co", "visitante", "Sofía Compradora")

    base_day = datetime(2026, 11, 15, 14, 0, tzinfo=timezone.utc)
    ev_res = client.post(
        "/v1/admin/eventos",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "nombre": "Rueda de Negocios",
            "slug": "rueda-de-negocios-2026",
            "descripcion": "Citas B2B.",
            "inicio": base_day.isoformat(),
            "fin": (base_day + timedelta(days=2)).isoformat(),
            "estado": "publicado",
            "precio_entrada": "50000.00",
            "aforo": 1500,
        },
    )
    assert ev_res.status_code == 201
    event_id = ev_res.json()["id"]

    pav_res = client.post(
        "/v1/admin/pabellones",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"nombre": "Pabellón Empresarial", "capacidad_stands": 20},
    )
    assert pav_res.status_code == 201
    pav_id = pav_res.json()["id"]

    room_res = client.post(
        f"/v1/pabellones/{pav_id}/salas",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"codigo": "SALA-B1", "capacidad": 6},
    )
    assert room_res.status_code == 201

    # Anfitrión define disponibilidad de 14:00 a 16:00 UTC
    avail_res = client.put(
        f"/v1/eventos/{event_id}/mi-disponibilidad",
        headers={"Authorization": f"Bearer {host_token}"},
        json={
            "bloques": [
                {
                    "desde": base_day.isoformat(),
                    "hasta": (base_day + timedelta(hours=2)).isoformat(),
                }
            ]
        },
    )
    assert avail_res.status_code == 200

    # Dos visitantes proponen citas que se cruzan (14:00-15:00 y 14:30-15:30)
    prop1 = client.post(
        "/v1/citas",
        headers={"Authorization": f"Bearer {vis1_token}"},
        json={
            "evento_id": event_id,
            "anfitrion_id": host.id,
            "inicio": base_day.isoformat(),
            "fin": (base_day + timedelta(hours=1)).isoformat(),
            "mensaje": "Presentación de catálogo logístico",
        },
    )
    assert prop1.status_code == 201
    cita1_id = prop1.json()["id"]

    prop2 = client.post(
        "/v1/citas",
        headers={"Authorization": f"Bearer {vis2_token}"},
        json={
            "evento_id": event_id,
            "anfitrion_id": host.id,
            "inicio": (base_day + timedelta(minutes=30)).isoformat(),
            "fin": (base_day + timedelta(hours=1, minutes=30)).isoformat(),
            "mensaje": "Alianza de distribución",
        },
    )
    assert prop2.status_code == 201
    cita2_id = prop2.json()["id"]

    # Anfitrión acepta la primera -> 200, sala SALA-B1 asignada
    acc1 = client.post(
        f"/v1/citas/{cita1_id}/responder",
        headers={"Authorization": f"Bearer {host_token}"},
        json={"decision": "aceptar"},
    )
    assert acc1.status_code == 200
    assert acc1.json()["estado"] == "aceptada"
    assert acc1.json()["sala_codigo"] == "SALA-B1"

    # Anfitrión intenta aceptar la segunda que se cruza -> 409 Conflict
    acc2 = client.post(
        f"/v1/citas/{cita2_id}/responder",
        headers={"Authorization": f"Bearer {host_token}"},
        json={"decision": "aceptar"},
    )
    assert acc2.status_code == 409

    # Los huecos libres del anfitrión ahora solo muestran de 15:00 a 16:00
    gaps_res = client.get(
        f"/v1/eventos/{event_id}/expositores/{host.id}/huecos",
        headers={"Authorization": f"Bearer {vis1_token}"},
    )
    assert gaps_res.status_code == 200
    gaps = gaps_res.json()
    assert len(gaps) == 1

    # Verificar que cita.aceptada quedó en bandeja_salida
    outbox = test_db.scalar(
        select(OutboxEvent).where(OutboxEvent.tipo == "cita.aceptada")
    )
    assert outbox is not None
