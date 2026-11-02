import pytest
import pyotp
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db import Base, get_db
from app.main import create_app
from app.services.email_sender import clear_dev_outbox, get_last_dev_code


@pytest.fixture()
def client():
    clear_dev_outbox()
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=test_engine)

    app = create_app(init_local_db=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_jwks(client: TestClient):
    res_health = client.get("/salud")
    assert res_health.status_code == 200
    assert res_health.json()["estado"] == "ok"
    assert "X-Correlation-Id" in res_health.headers

    res_jwks = client.get("/.well-known/jwks.json")
    assert res_jwks.status_code == 200
    keys = res_jwks.json()["keys"]
    assert len(keys) == 1
    assert keys[0]["kty"] == "RSA"
    assert keys[0]["alg"] == "RS256"
    assert keys[0]["kid"] == get_settings().jwt_key_id


def test_registration_and_email_confirmation(client: TestClient):
    # Weak password rejected
    weak_res = client.post(
        "/v1/cuentas",
        json={
            "correo": "expositor@feria.co",
            "nombre": "Ana Expositora",
            "contrasena": "corta",
            "rol": "expositor",
        },
    )
    assert weak_res.status_code == 422

    # Valid registration
    reg_res = client.post(
        "/v1/cuentas",
        json={
            "correo": "Expositor@Feria.co",
            "nombre": "Ana Expositora",
            "contrasena": "PasswordFuerte#2026",
            "rol": "expositor",
        },
    )
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert data["correo"] == "expositor@feria.co"
    assert data["rol"] == "expositor"
    assert data["correo_verificado"] is False

    # Duplicate email rejected
    dup_res = client.post(
        "/v1/cuentas",
        json={
            "correo": "expositor@feria.co",
            "nombre": "Otra Persona",
            "contrasena": "PasswordFuerte#2026",
            "rol": "visitante",
        },
    )
    assert dup_res.status_code == 409

    # Confirm email with OTP code sent during registration
    confirm_code = get_last_dev_code("expositor@feria.co", "confirmar_correo")
    assert confirm_code is not None
    conf_res = client.post(
        "/v1/cuentas/confirmar-correo",
        json={"correo": "expositor@feria.co", "codigo": confirm_code},
    )
    assert conf_res.status_code == 200
    assert conf_res.json()["correo_verificado"] is True


def test_full_mfa_totp_flow_and_replay_protection(client: TestClient):
    # 1. Register user
    client.post(
        "/v1/cuentas",
        json={
            "correo": "carlos@empresa.co",
            "nombre": "Carlos Ruiz",
            "contrasena": "ClaveSegura!2026",
            "rol": "expositor",
        },
    )

    # 2. Login Step 1
    step1 = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "carlos@empresa.co", "contrasena": "ClaveSegura!2026"},
    )
    assert step1.status_code == 200
    pass_token = step1.json()["pase_segundo_paso"]

    # 3. Request email OTP for first login
    req_code = client.post(
        "/v1/sesion/codigo-correo",
        headers={"Authorization": f"Bearer {pass_token}"},
    )
    assert req_code.status_code == 200
    email_otp = get_last_dev_code("carlos@empresa.co", "ingreso")
    assert email_otp is not None

    # 4. Complete Step 2 with email OTP
    step2 = client.post(
        "/v1/sesion/segundo-paso",
        headers={"Authorization": f"Bearer {pass_token}"},
        json={"metodo": "correo", "codigo": email_otp},
    )
    assert step2.status_code == 200
    tokens = step2.json()
    access_token = tokens["token_acceso"]
    refresh_token = tokens["token_refresco"]

    # 5. Setup TOTP Authenticator App
    totp_setup = client.post(
        "/v1/perfil/mfa/app",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert totp_setup.status_code == 200
    setup_data = totp_setup.json()
    totp_secret = setup_data["secreto"]
    assert setup_data["qr_datos_url"].startswith("data:image/png;base64,")

    totp = pyotp.TOTP(totp_secret)
    first_code = totp.now()
    confirm_totp = client.post(
        "/v1/perfil/mfa/app/confirmar",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"codigo": first_code},
    )
    assert confirm_totp.status_code == 200
    assert confirm_totp.json()["metodo_preferido"] == "app"

    # 6. Replaying the exact same TOTP code in the same 30s window must fail!
    step1_again = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "carlos@empresa.co", "contrasena": "ClaveSegura!2026"},
    )
    pass_token_2 = step1_again.json()["pase_segundo_paso"]
    replay_attempt = client.post(
        "/v1/sesion/segundo-paso",
        headers={"Authorization": f"Bearer {pass_token_2}"},
        json={"metodo": "app", "codigo": first_code},
    )
    assert replay_attempt.status_code == 401

    # 7. Backup codes generation and single-use verification
    backup_res = client.post(
        "/v1/perfil/codigos-respaldo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert backup_res.status_code == 200
    backup_codes = backup_res.json()["codigos"]
    assert len(backup_codes) == 8

    backup_login = client.post(
        "/v1/sesion/segundo-paso",
        headers={"Authorization": f"Bearer {pass_token_2}"},
        json={"metodo": "respaldo", "codigo": backup_codes[0]},
    )
    assert backup_login.status_code == 200

    # Reusing the same backup code must fail
    backup_reuse = client.post(
        "/v1/sesion/segundo-paso",
        headers={"Authorization": f"Bearer {pass_token_2}"},
        json={"metodo": "respaldo", "codigo": backup_codes[0]},
    )
    assert backup_reuse.status_code == 401

    # 8. Refresh token rotation and logout
    ref_res = client.post(
        "/v1/sesion/refrescar",
        json={"token_refresco": refresh_token},
    )
    assert ref_res.status_code == 200
    new_refresh = ref_res.json()["token_refresco"]
    new_access = ref_res.json()["token_acceso"]

    logout_res = client.post(
        "/v1/sesion/salir",
        headers={"Authorization": f"Bearer {new_access}"},
        json={"token_refresco": new_refresh},
    )
    assert logout_res.status_code == 200

    # Refreshing after logout must fail
    ref_after_logout = client.post(
        "/v1/sesion/refrescar",
        json={"token_refresco": new_refresh},
    )
    assert ref_after_logout.status_code == 401


def test_lockout_after_failed_attempts_and_internal_service_jwt(client: TestClient):
    client.post(
        "/v1/cuentas",
        json={
            "correo": "bloqueo@feria.co",
            "nombre": "Usuario Bloqueo",
            "contrasena": "ClaveSegura!2026",
            "rol": "visitante",
        },
    )

    max_attempts = get_settings().mfa_max_attempts
    for _ in range(max_attempts):
        bad = client.post(
            "/v1/sesion/ingreso",
            json={"correo": "bloqueo@feria.co", "contrasena": "ClaveIncorrecta!1"},
        )
        assert bad.status_code == 401

    # Next attempt (even with right password) must return 429 Too Many Requests
    locked = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "bloqueo@feria.co", "contrasena": "ClaveSegura!2026"},
    )
    assert locked.status_code == 429

    # Internal routes must reject unauthenticated or person tokens, and accept RS256 service tokens
    unauth_internal = client.get("/v1/interno/salud")
    assert unauth_internal.status_code == 401

    svc_res = client.post(
        "/v1/sesion/servicio",
        json={
            "servicio": "repartidor",
            "secreto_interno": get_settings().internal_secret,
        },
    )
    assert svc_res.status_code == 200
    svc_token = svc_res.json()["token_servicio"]

    ok_internal = client.get(
        "/v1/interno/salud",
        headers={"Authorization": f"Bearer {svc_token}"},
    )
    assert ok_internal.status_code == 200
    assert ok_internal.json()["autenticado_como"] == "service:repartidor"
