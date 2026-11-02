import base64
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import secrets
from typing import Any
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt

from app.config import get_settings


def _int_to_base64url(value: int) -> str:
    byte_length = (value.bit_length() + 7) // 8
    raw = value.to_bytes(byte_length, byteorder="big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


@lru_cache
def _load_or_create_rsa_keys() -> tuple[bytes, bytes, rsa.RSAPublicNumbers]:
    settings = get_settings()
    key_path = settings.resolved_private_key_path
    if key_path.exists():
        private_pem = key_path.read_bytes()
        private_key = serialization.load_pem_private_key(private_pem, password=None)
    else:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        key_path.write_bytes(private_pem)

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_numbers = public_key.public_numbers()
    return private_pem, public_pem, public_numbers


def get_jwks() -> dict[str, Any]:
    settings = get_settings()
    _, _, numbers = _load_or_create_rsa_keys()
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": settings.jwt_key_id,
                "n": _int_to_base64url(numbers.n),
                "e": _int_to_base64url(numbers.e),
            }
        ]
    }


def create_access_token(user_id: str, email: str, name: str, role: str) -> tuple[str, int]:
    settings = get_settings()
    private_pem, _, _ = _load_or_create_rsa_keys()
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=settings.jwt_access_minutes)
    payload = {
        "sub": user_id,
        "correo": email,
        "nombre": name,
        "rol": role,
        "token_use": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(
        payload,
        private_pem,
        algorithm="RS256",
        headers={"kid": settings.jwt_key_id},
    )
    return token, int(expires_delta.total_seconds())


def create_mfa_pass_token(user_id: str, email: str) -> tuple[str, int]:
    settings = get_settings()
    private_pem, _, _ = _load_or_create_rsa_keys()
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=settings.mfa_pass_minutes)
    payload = {
        "sub": user_id,
        "correo": email,
        "token_use": "mfa_pass",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(
        payload,
        private_pem,
        algorithm="RS256",
        headers={"kid": settings.jwt_key_id},
    )
    return token, int(expires_delta.total_seconds())


def create_service_token(service_name: str, expires_minutes: int = 15) -> tuple[str, int]:
    """Issue an RS256 internal service JWT (ADR-016)."""
    settings = get_settings()
    private_pem, _, _ = _load_or_create_rsa_keys()
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=expires_minutes)
    payload = {
        "sub": f"service:{service_name}",
        "rol": "interno",
        "token_use": "service",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(
        payload,
        private_pem,
        algorithm="RS256",
        headers={"kid": settings.jwt_key_id},
    )
    return token, int(expires_delta.total_seconds())


def create_refresh_token_raw() -> str:
    return secrets.token_urlsafe(48)


def verify_jwt_token(token: str, expected_use: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    _, public_pem, _ = _load_or_create_rsa_keys()
    payload = jwt.decode(
        token,
        public_pem,
        algorithms=["RS256"],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
    if expected_use and payload.get("token_use") != expected_use:
        raise jwt.InvalidTokenError(f"Se esperaba token_use={expected_use}")
    return payload
