from typing import Any

from fastapi import APIRouter

from app.security.tokens import get_jwks


router = APIRouter(tags=["Salud y JWKS"])


@router.get("/salud")
def health_check() -> dict[str, str]:
    return {"estado": "ok", "servicio": "identidad-reservas"}


@router.get("/.well-known/jwks.json")
def jwks_endpoint() -> dict[str, Any]:
    return get_jwks()
