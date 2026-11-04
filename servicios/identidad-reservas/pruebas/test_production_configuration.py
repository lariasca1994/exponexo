from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import Settings


def _production_settings(tmp_path: Path, **overrides) -> Settings:
    key_path = tmp_path / "jwt-private.pem"
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    values = {
        "APP_ENTORNO": "produccion",
        "DATABASE_URL": (
            "mssql+pyodbc:///?odbc_connect="
            "DRIVER%3D%7BODBC%20Driver%2018%20for%20SQL%20Server%7D%3B"
            "SERVER%3Dtcp%3Asql.exponexo.co%2C1433%3B"
            "DATABASE%3Dexponexo%3BUID%3Dapp_user%3BPWD%3Dtest-password%3B"
        ),
        "JWT_EMISOR": "https://identity.exponexo.co",
        "JWT_AUDIENCIA": "exponexo",
        "JWT_CLAVE_ID": "production-key-2026",
        "JWT_CLAVE_PRIVADA_RUTA": str(key_path),
        "MFA_CLAVE_CIFRADO": "a" * 44,
        "ENTRADA_QR_CLAVE_FIRMA": "q" * 48,
        "INTERNO_SECRETO": "s" * 48,
        "SNS_TEMA_EVENTOS_ARN": "arn:aws:sns:us-east-1:000000000000:exponexo-eventos",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_legacy_entorno_alias_is_supported_and_canonical_value_wins(monkeypatch):
    monkeypatch.delenv("APP_ENTORNO", raising=False)
    monkeypatch.setenv("ENTORNO", "desarrollo")
    legacy = Settings(_env_file=None)
    assert legacy.app_environment == "desarrollo"

    monkeypatch.setenv("APP_ENTORNO", "desarrollo")
    monkeypatch.setenv("ENTORNO", "produccion")
    settings = Settings(_env_file=None)
    assert settings.app_environment == "desarrollo"
    assert not settings.is_production


def test_production_accepts_real_sql_server_and_key_material(tmp_path: Path):
    settings = _production_settings(tmp_path)
    assert settings.is_production
    assert settings.sqlalchemy_database_uri.startswith("mssql+pyodbc://")


def test_production_rejects_sqlite_database_url(tmp_path: Path):
    with pytest.raises(ValueError, match="DATABASE_URL debe apuntar a SQL Server"):
        _production_settings(tmp_path, DATABASE_URL="sqlite:///local.db")


def test_production_rejects_missing_sql_server_configuration(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="SQL Server es obligatoria"):
        Settings(_env_file=None, APP_ENTORNO="produccion")


def test_production_requires_existing_rsa_private_key(tmp_path: Path):
    with pytest.raises(ValueError, match="JWT_CLAVE_PRIVADA_RUTA debe apuntar"):
        _production_settings(tmp_path, JWT_CLAVE_PRIVADA_RUTA=str(tmp_path / "missing.pem"))


def test_production_requires_events_topic(tmp_path: Path):
    with pytest.raises(ValueError, match="SNS_TEMA_EVENTOS_ARN"):
        _production_settings(tmp_path, SNS_TEMA_EVENTOS_ARN="")
