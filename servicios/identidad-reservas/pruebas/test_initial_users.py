import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
import app.models  # noqa: F401
from app.models.identity import MfaFactor, User
from app.security.passwords import verify_password
from app.services.initial_users import ensure_initial_users, parse_initial_users


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        yield session


def test_creates_verified_accounts_with_role_and_email_mfa(db):
    users = parse_initial_users(json.dumps([
        {"correo": "Admin@Ejemplo.co", "nombre": "Administración", "rol": "administrador", "contrasena": "UnaClave123"},
        {"correo": "staff@ejemplo.co", "nombre": "Personal", "rol": "personal", "contrasena": "OtraClave123"},
    ]))
    assert ensure_initial_users(db, users) == 2

    admin = db.scalar(select(User).where(User.correo == "admin@ejemplo.co"))
    assert admin.rol == "administrador" and admin.activo and admin.correo_verificado
    assert verify_password(admin.hash_contrasena, "UnaClave123")
    factor = db.scalar(select(MfaFactor).where(MfaFactor.usuario_id == admin.id))
    assert factor.tipo == "correo" and factor.activo

    # Idempotente: sin cambios no toca nada; un rol o clave nueva se aplica
    assert ensure_initial_users(db, users) == 0
    users[1]["rol"], users[1]["contrasena"] = "administrador", "ClaveNueva456"
    assert ensure_initial_users(db, users) == 1
    staff = db.scalar(select(User).where(User.correo == "staff@ejemplo.co"))
    assert staff.rol == "administrador" and verify_password(staff.hash_contrasena, "ClaveNueva456")


def test_rejects_unknown_roles_and_missing_fields():
    with pytest.raises(ValueError, match="rol inválido"):
        parse_initial_users('[{"correo": "a@b.co", "nombre": "A", "rol": "root", "contrasena": "x"}]')
    with pytest.raises(ValueError, match="faltan campos"):
        parse_initial_users('[{"correo": "a@b.co"}]')
    assert parse_initial_users("") == []
