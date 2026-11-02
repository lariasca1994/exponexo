from collections.abc import Callable
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ProblemDetailError
from app.models.identity import User
from app.security.tokens import verify_jwt_token


bearer_scheme = HTTPBearer(auto_error=False)


def _extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise ProblemDetailError(
            status=401,
            title="No autenticado",
            detail="Se requiere un token Bearer válido en la cabecera Authorization.",
            problem_type="https://exponexo.co/problemas/no-autenticado",
        )
    return credentials.credentials


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_bearer_token(credentials)
    try:
        payload = verify_jwt_token(token, expected_use="access")
    except jwt.PyJWTError as exc:
        raise ProblemDetailError(
            status=401,
            title="Token inválido o vencido",
            detail="El token de acceso no es válido o ha expirado.",
            problem_type="https://exponexo.co/problemas/token-invalido",
        ) from exc

    user_id = payload.get("sub")
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.activo:
        raise ProblemDetailError(
            status=401,
            title="Cuenta inactiva o inexistente",
            detail="El usuario asociado al token no existe o está deshabilitado.",
            problem_type="https://exponexo.co/problemas/cuenta-inactiva",
        )
    return user


def get_mfa_pass_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_bearer_token(credentials)
    try:
        payload = verify_jwt_token(token, expected_use="mfa_pass")
    except jwt.PyJWTError as exc:
        raise ProblemDetailError(
            status=401,
            title="Pase de segundo paso inválido",
            detail="El pase temporal para el segundo paso no es válido o venció.",
            problem_type="https://exponexo.co/problemas/pase-invalido",
        ) from exc

    user_id = payload.get("sub")
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.activo:
        raise ProblemDetailError(
            status=401,
            title="Cuenta inactiva",
            detail="La cuenta no está activa.",
            problem_type="https://exponexo.co/problemas/cuenta-inactiva",
        )
    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.rol not in allowed_roles:
            raise ProblemDetailError(
                status=403,
                title="Acceso denegado",
                detail="Tu rol no tiene permiso para realizar esta operación.",
                problem_type="https://exponexo.co/problemas/acceso-denegado",
            )
        return current_user

    return dependency


def require_service_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Enforce ADR-016: internal routes only accept RS256 service tokens, never person tokens."""
    token = _extract_bearer_token(credentials)
    try:
        payload = verify_jwt_token(token, expected_use="service")
    except jwt.PyJWTError as exc:
        raise ProblemDetailError(
            status=403,
            title="Acceso interno denegado",
            detail="Esta ruta interna exige un token de servicio válido (RS256).",
            problem_type="https://exponexo.co/problemas/acceso-interno-denegado",
        ) from exc

    if payload.get("rol") != "interno":
        raise ProblemDetailError(
            status=403,
            title="Acceso interno denegado",
            detail="Los tokens de personas no tienen acceso a rutas internas.",
            problem_type="https://exponexo.co/problemas/acceso-interno-denegado",
        )
    return payload
