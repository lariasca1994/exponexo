from datetime import datetime, timedelta, timezone
import json

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import create_app
from app.models.identity import User
from app.security.passwords import hash_password
from app.security.tokens import create_access_token, create_service_token
from app.services.email_sender import get_last_dev_code


@pytest.fixture()
def e2e_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    app = create_app(init_local_db=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed Admin User
    with TestingSessionLocal() as db:
        admin = User(
            correo="admin.e2e@exponexo.co",
            nombre="Admin E2E",
            hash_contrasena=hash_password("AdminClaveSegura2026!"),
            rol="administrador",
            activo=True,
            correo_verificado=True,
        )
        staff = User(
            correo="staff.e2e@exponexo.co",
            nombre="Personal Puerta E2E",
            hash_contrasena=hash_password("StaffClaveSegura2026!"),
            rol="personal",
            activo=True,
            correo_verificado=True,
        )
        db.add_all([admin, staff])
        db.commit()

    with TestClient(app) as tc:
        yield tc, TestingSessionLocal

    Base.metadata.drop_all(bind=engine)


def test_complete_platform_lifecycle_e2e(e2e_client):
    client, SessionLocal = e2e_client

    # 1. Registro de expositor y visitante
    reg_exp = client.post(
        "/v1/cuentas",
        json={
            "correo": "expositor.tech@empresa.co",
            "nombre": "Ana Robledo",
            "contrasena": "ExpoClave2026!",
            "rol": "expositor",
        },
    )
    assert reg_exp.status_code == 201

    reg_vis = client.post(
        "/v1/cuentas",
        json={
            "correo": "visitante.b2b@comprador.co",
            "nombre": "Mauricio Comprador",
            "contrasena": "VisitaClave2026!",
            "rol": "visitante",
        },
    )
    assert reg_vis.status_code == 201

    # Iniciar sesión paso 1
    step1_exp = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "expositor.tech@empresa.co", "contrasena": "ExpoClave2026!"},
    )
    assert step1_exp.status_code == 200
    mfa_pass_exp = step1_exp.json()["pase_segundo_paso"]

    # Iniciar sesión paso 2: solicitar código por correo y validar
    client.post(
        "/v1/sesion/codigo-correo",
        headers={"Authorization": f"Bearer {mfa_pass_exp}"},
    )
    code_exp = get_last_dev_code("expositor.tech@empresa.co", "ingreso")
    assert code_exp is not None

    step2_exp = client.post(
        "/v1/sesion/segundo-paso",
        headers={"Authorization": f"Bearer {mfa_pass_exp}"},
        json={"metodo": "correo", "codigo": code_exp},
    )
    assert step2_exp.status_code == 200
    exp_token = step2_exp.json()["token_acceso"]

    step1_vis = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "visitante.b2b@comprador.co", "contrasena": "VisitaClave2026!"},
    )
    mfa_pass_vis = step1_vis.json()["pase_segundo_paso"]

    client.post(
        "/v1/sesion/codigo-correo",
        headers={"Authorization": f"Bearer {mfa_pass_vis}"},
    )
    code_vis = get_last_dev_code("visitante.b2b@comprador.co", "ingreso")
    assert code_vis is not None

    step2_vis = client.post(
        "/v1/sesion/segundo-paso",
        headers={"Authorization": f"Bearer {mfa_pass_vis}"},
        json={"metodo": "correo", "codigo": code_vis},
    )
    assert step2_vis.status_code == 200
    vis_token = step2_vis.json()["token_acceso"]

    # Login admin
    with SessionLocal() as db:
        admin_row = db.query(User).filter(User.correo == "admin.e2e@exponexo.co").first()
        admin_token, _ = create_access_token(admin_row.id, admin_row.correo, admin_row.nombre, admin_row.rol)
        staff_row = db.query(User).filter(User.correo == "staff.e2e@exponexo.co").first()
        staff_token, _ = create_access_token(staff_row.id, staff_row.correo, staff_row.nombre, staff_row.rol)
    svc_token, _ = create_service_token("eventos-repartidor")

    # 2. Administrador crea Evento, Pabellón, Stand y Sala de Negocios
    now = datetime.now(timezone.utc)
    ev_res = client.post(
        "/v1/admin/eventos",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "nombre": "Gran Feria de Innovación 2026",
            "slug": "gran-feria-innovacion-2026",
            "descripcion": "El epicentro de los negocios globales.",
            "inicio": (now + timedelta(days=10)).isoformat(),
            "fin": (now + timedelta(days=14)).isoformat(),
            "estado": "publicado",
            "precio_entrada": "45000.00",
            "aforo": 4000,
        },
    )
    assert ev_res.status_code == 201
    event_id = ev_res.json()["id"]

    pav_res = client.post(
        "/v1/admin/pabellones",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"nombre": "Pabellón Principal Tech", "capacidad_stands": 30},
    )
    assert pav_res.status_code == 201
    pav_id = pav_res.json()["id"]

    stand_res = client.post(
        "/v1/admin/stands",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "pabellon_id": pav_id,
            "codigo": "TECH-A01",
            "metros_cuadrados": "24.00",
            "tipo": "isla",
            "precio_base": "5400000.00",
            "fila": 1,
            "columna": 1,
        },
    )
    assert stand_res.status_code == 201
    stand_id = stand_res.json()["id"]

    sala_res = client.post(
        f"/v1/pabellones/{pav_id}/salas",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"codigo": "SALA-VIP-1", "capacidad": 6},
    )
    assert sala_res.status_code == 201

    # 3. Expositor reserva el stand con Idempotency-Key
    res_post = client.post(
        "/v1/reservas",
        headers={
            "Authorization": f"Bearer {exp_token}",
            "Idempotency-Key": "e2e-idem-stand-01",
        },
        json={"evento_id": event_id, "stand_id": stand_id},
    )
    assert res_post.status_code == 201
    reservation_id = res_post.json()["id"]
    assert res_post.json()["estado"] == "pendiente_pago"

    # Repartidor confirma pago de reserva
    paid_res = client.post(
        f"/v1/interno/reservas/{reservation_id}/pagada",
        headers={"Authorization": f"Bearer {svc_token}"},
        json={"orden_pago_id": "ord-pago-e2e-001", "evento_id": "evt-pago-001"},
    )
    assert paid_res.status_code == 200
    assert paid_res.json()["estado"] == "pagada"

    # 4. Visitante compra entrada y Repartidor la activa con QR firmado
    buy_ticket_res = client.post(
        f"/v1/eventos/{event_id}/entradas",
        headers={"Authorization": f"Bearer {vis_token}"},
        json={"tipo": "negocios"},
    )
    assert buy_ticket_res.status_code == 201
    ticket_id = buy_ticket_res.json()["id"]

    act_ticket_res = client.post(
        f"/v1/interno/entradas/{ticket_id}/activar",
        headers={"Authorization": f"Bearer {svc_token}"},
        json={"orden_pago_id": "ord-ticket-001", "evento_id": "evt-ticket-001"},
    )
    assert act_ticket_res.status_code == 200
    qr_token = act_ticket_res.json()["codigo_qr"]
    assert qr_token.startswith("EXN1.")

    # 5. Puerta valida el código QR
    gate_scan = client.post(
        "/v1/entradas/validar-qr",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"codigo_qr": qr_token, "dispositivo_id": "torniquete-sur-e2e"},
    )
    assert gate_scan.status_code == 200
    assert gate_scan.json()["valida"] is True
    assert gate_scan.json()["estado"] == "usada"

    # Reutilización del mismo QR -> 409
    dup_scan = client.post(
        "/v1/entradas/validar-qr",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"codigo_qr": qr_token, "dispositivo_id": "torniquete-sur-e2e"},
    )
    assert dup_scan.status_code == 409

    # 6. Agenda de negocios: expositor publica disponibilidad y visitante propone cita
    slot_time = now + timedelta(days=11, hours=3)
    client.put(
        f"/v1/eventos/{event_id}/mi-disponibilidad",
        headers={"Authorization": f"Bearer {exp_token}"},
        json={
            "bloques": [
                {
                    "desde": slot_time.isoformat(),
                    "hasta": (slot_time + timedelta(hours=3)).isoformat(),
                }
            ]
        },
    )

    with SessionLocal() as db:
        exp_user = db.query(User).filter(User.correo == "expositor.tech@empresa.co").first()
        exp_user_id = exp_user.id

    prop_res = client.post(
        "/v1/citas",
        headers={"Authorization": f"Bearer {vis_token}"},
        json={
            "evento_id": event_id,
            "anfitrion_id": exp_user_id,
            "inicio": slot_time.isoformat(),
            "fin": (slot_time + timedelta(minutes=45)).isoformat(),
            "mensaje": "Acuerdo de distribución en LATAM",
        },
    )
    assert prop_res.status_code == 201
    cita_id = prop_res.json()["id"]

    # Expositor acepta cita -> Asignación de SALA-VIP-1
    acc_res = client.post(
        f"/v1/citas/{cita_id}/responder",
        headers={"Authorization": f"Bearer {exp_token}"},
        json={"decision": "aceptar"},
    )
    assert acc_res.status_code == 200
    assert acc_res.json()["estado"] == "aceptada"
    assert acc_res.json()["sala_codigo"] == "SALA-VIP-1"

    # 7. Resumen consolidado para el tablero del administrador
    summary_res = client.get(
        "/v1/admin/resumen",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert summary_res.status_code == 200
    sum_data = summary_res.json()
    assert sum_data["stands_pagados"] == 1
    assert sum_data["entradas_validadas_puerta"] == 1
    assert sum_data["citas_negocios_aceptadas"] == 1
