from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db import Base, get_db
from app.main import create_app
from app.models.catalog import StandReservation
from app.models.identity import OutboxEvent, User
from app.security.passwords import hash_password
from app.security.tokens import create_access_token, create_service_token
from app.services.catalog_service import expire_overdue_reservations


@pytest.fixture()
def test_env():
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

    with TestingSessionLocal() as db:
        admin = User(
            correo="admin@exponexo.co",
            nombre="Admin Recinto",
            hash_contrasena=hash_password("ClaveSegura!2026"),
            rol="administrador",
            activo=True,
            correo_verificado=True,
        )
        exp1 = User(
            correo="expositor1@empresa.co",
            nombre="Expositor Uno",
            hash_contrasena=hash_password("ClaveSegura!2026"),
            rol="expositor",
            activo=True,
            correo_verificado=True,
        )
        exp2 = User(
            correo="expositor2@otra.co",
            nombre="Expositor Dos",
            hash_contrasena=hash_password("ClaveSegura!2026"),
            rol="expositor",
            activo=True,
            correo_verificado=True,
        )
        visitor = User(
            correo="visitante@correo.co",
            nombre="Visitante Feria",
            hash_contrasena=hash_password("ClaveSegura!2026"),
            rol="visitante",
            activo=True,
            correo_verificado=True,
        )
        db.add_all([admin, exp1, exp2, visitor])
        db.commit()
        tokens = {
            "admin": create_access_token(admin.id, admin.correo, admin.nombre, admin.rol)[0],
            "exp1": create_access_token(exp1.id, exp1.correo, exp1.nombre, exp1.rol)[0],
            "exp2": create_access_token(exp2.id, exp2.correo, exp2.nombre, exp2.rol)[0],
            "visitor": create_access_token(
                visitor.id, visitor.correo, visitor.nombre, visitor.rol
            )[0],
            "service": create_service_token("repartidor")[0],
        }

    with TestClient(app) as client:
        yield client, TestingSessionLocal, tokens


def test_rbac_and_catalog_creation(test_env):
    client, _, tokens = test_env

    # Exhibitor cannot create event (403 Forbidden)
    forbidden = client.post(
        "/v1/admin/eventos",
        headers={"Authorization": f"Bearer {tokens['exp1']}"},
        json={
            "nombre": "Feria de Tecnología 2027",
            "slug": "feria-tecnologia-2027",
            "descripcion": "El encuentro tecnológico del año.",
            "inicio": "2027-05-10T13:00:00Z",
            "fin": "2027-05-14T23:00:00Z",
            "estado": "publicado",
            "precio_entrada": "45000.00",
            "aforo": 5000,
        },
    )
    assert forbidden.status_code == 403

    # Admin creates event, pavilion, and stands
    ev_res = client.post(
        "/v1/admin/eventos",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={
            "nombre": "Feria de Tecnología 2027",
            "slug": "feria-tecnologia-2027",
            "descripcion": "El encuentro tecnológico del año.",
            "inicio": "2027-05-10T13:00:00Z",
            "fin": "2027-05-14T23:00:00Z",
            "estado": "publicado",
            "precio_entrada": "45000.00",
            "aforo": 5000,
        },
    )
    assert ev_res.status_code == 201
    event_id = ev_res.json()["id"]

    pav_res = client.post(
        "/v1/admin/pabellones",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={"nombre": "Pabellón 1 · Innovación", "capacidad_stands": 20},
    )
    assert pav_res.status_code == 201
    pavilion_id = pav_res.json()["id"]

    st_res = client.post(
        "/v1/admin/stands",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={
            "pabellon_id": pavilion_id,
            "codigo": "P1-A01",
            "metros_cuadrados": "18.00",
            "tipo": "esquinero",
            "precio_base": "3200000.00",
            "fila": 1,
            "columna": 1,
        },
    )
    assert st_res.status_code == 201

    # Public listing and detail
    pub_list = client.get("/v1/eventos")
    assert pub_list.status_code == 200
    assert pub_list.json()["total"] == 1

    stands_list = client.get(f"/v1/eventos/{event_id}/stands")
    assert stands_list.status_code == 200
    assert len(stands_list.json()) == 1
    assert stands_list.json()[0]["estado"] == "disponible"


def test_stand_reservation_conflict_expiration_and_paid_flow(test_env):
    client, SessionLocal, tokens = test_env

    # Setup event, pavilion, stand
    ev = client.post(
        "/v1/admin/eventos",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={
            "nombre": "Expo Industrial 2027",
            "slug": "expo-industrial-2027",
            "descripcion": "Feria industrial.",
            "inicio": "2027-08-01T13:00:00Z",
            "fin": "2027-08-05T22:00:00Z",
            "estado": "publicado",
            "precio_entrada": "50000.00",
            "aforo": 3000,
        },
    ).json()
    pav = client.post(
        "/v1/admin/pabellones",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={"nombre": "Pabellón Central", "capacidad_stands": 12},
    ).json()
    stand = client.post(
        "/v1/admin/stands",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
        json={
            "pabellon_id": pav["id"],
            "codigo": "PC-B04",
            "metros_cuadrados": "24.00",
            "tipo": "isla",
            "precio_base": "4800000.00",
            "fila": 2,
            "columna": 4,
        },
    ).json()

    # Visitor cannot reserve a stand (403)
    vis_attempt = client.post(
        "/v1/reservas",
        headers={
            "Authorization": f"Bearer {tokens['visitor']}",
            "Idempotency-Key": "idem-vis-1",
        },
        json={"evento_id": ev["id"], "stand_id": stand["id"]},
    )
    assert vis_attempt.status_code == 403

    # Exhibitor 1 reserves the stand with Idempotency-Key
    res1 = client.post(
        "/v1/reservas",
        headers={
            "Authorization": f"Bearer {tokens['exp1']}",
            "Idempotency-Key": "idem-exp1-stand1",
        },
        json={"evento_id": ev["id"], "stand_id": stand["id"]},
    )
    assert res1.status_code == 201
    res1_data = res1.json()
    assert res1_data["estado"] == "pendiente_pago"
    assert res1_data["monto"] == "4800000.00"

    # Repeating with the exact same Idempotency-Key returns the same reservation
    res1_retry = client.post(
        "/v1/reservas",
        headers={
            "Authorization": f"Bearer {tokens['exp1']}",
            "Idempotency-Key": "idem-exp1-stand1",
        },
        json={"evento_id": ev["id"], "stand_id": stand["id"]},
    )
    assert res1_retry.status_code == 201
    assert res1_retry.json()["id"] == res1_data["id"]

    # Exhibitor 2 tries to reserve the same stand -> 409 Conflict!
    res2_conflict = client.post(
        "/v1/reservas",
        headers={
            "Authorization": f"Bearer {tokens['exp2']}",
            "Idempotency-Key": "idem-exp2-stand1",
        },
        json={"evento_id": ev["id"], "stand_id": stand["id"]},
    )
    assert res2_conflict.status_code == 409

    # Verify outbox event `reserva.creada` was written
    with SessionLocal() as db:
        outbox = db.scalar(
            select(OutboxEvent).where(OutboxEvent.tipo == "reserva.creada")
        )
        assert outbox is not None

        # Simulate expiration of Exhibitor 1's unpaid reservation
        future_cutoff = datetime.now(timezone.utc) + timedelta(
            minutes=get_settings().reservation_expiration_minutes + 5
        )
        expired_count = expire_overdue_reservations(db, cutoff_time=future_cutoff)
        assert expired_count == 1

        expired_row = db.scalar(
            select(StandReservation).where(StandReservation.id == res1_data["id"])
        )
        assert expired_row is not None
        assert expired_row.estado == "vencida"

    # Now that the reservation expired, Exhibitor 2 CAN reserve the stand!
    res2_win = client.post(
        "/v1/reservas",
        headers={
            "Authorization": f"Bearer {tokens['exp2']}",
            "Idempotency-Key": "idem-exp2-after-expiry",
        },
        json={"evento_id": ev["id"], "stand_id": stand["id"]},
    )
    assert res2_win.status_code == 201
    win_id = res2_win.json()["id"]

    # Internal route: Payments queries the reservation amount
    internal_get = client.get(
        f"/v1/interno/reservas/{win_id}",
        headers={"Authorization": f"Bearer {tokens['service']}"},
    )
    assert internal_get.status_code == 200
    assert internal_get.json()["monto"] == "4800000.00"

    # Internal route: Repartidor marks reservation as paid (idempotently)
    paid_res = client.post(
        f"/v1/interno/reservas/{win_id}/pagada",
        headers={"Authorization": f"Bearer {tokens['service']}"},
        json={"orden_pago_id": "ORD-001", "evento_id": "evt-pago-aprobado-1"},
    )
    assert paid_res.status_code == 200
    assert paid_res.json()["estado"] == "pagada"

    # Repeating the exact same event_id does not fail or duplicate outbox events
    paid_dup = client.post(
        f"/v1/interno/reservas/{win_id}/pagada",
        headers={"Authorization": f"Bearer {tokens['service']}"},
        json={"orden_pago_id": "ORD-001", "evento_id": "evt-pago-aprobado-1"},
    )
    assert paid_dup.status_code == 200

    # Stand status in event is now `pagado`
    stands_after = client.get(f"/v1/eventos/{ev['id']}/stands").json()
    assert stands_after[0]["estado"] == "pagado"
