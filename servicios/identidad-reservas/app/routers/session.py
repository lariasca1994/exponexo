from datetime import datetime, timezone
import secrets

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.errors import ProblemDetailError
from app.models.identity import PasskeyCredential, User
from app.schemas.identity import (
    LoginStep1Request,
    LoginStep1Response,
    LoginStep2Request,
    LogoutRequest,
    PasskeyLoginOptionsRequest,
    PasskeyLoginVerifyRequest,
    PasskeyOptionsResponse,
    RefreshTokenRequest,
    ServiceTokenRequest,
    ServiceTokenResponse,
    TokenPairResponse,
)
from app.security.dependencies import get_current_user, get_mfa_pass_user
from app.security.passkeys import (
    complete_passkey_authentication,
    create_passkey_authentication_options,
)
from app.security.tokens import create_service_token
from app.services.identity_service import (
    issue_session_tokens,
    login_step_one,
    login_step_two,
    refresh_session,
    revoke_session,
    send_login_email_code,
)


router = APIRouter(prefix="/v1/sesion", tags=["Sesión"])


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


@router.post("/ingreso", response_model=LoginStep1Response)
def step_one_login(
    payload: LoginStep1Request,
    request: Request,
    db: Session = Depends(get_db),
) -> LoginStep1Response:
    correlation_id = getattr(request.state, "correlation_id", None)
    return login_step_one(
        db=db,
        email=payload.correo,
        password=payload.contrasena,
        client_ip=_client_ip(request),
        correlation_id=correlation_id,
    )


@router.post("/codigo-correo")
def request_step_two_email_code(
    user: User = Depends(get_mfa_pass_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    send_login_email_code(db=db, user=user)
    return {"mensaje": "Código de verificación enviado al correo registrado."}


@router.post("/segundo-paso", response_model=TokenPairResponse)
def step_two_login(
    payload: LoginStep2Request,
    request: Request,
    user: User = Depends(get_mfa_pass_user),
    db: Session = Depends(get_db),
) -> TokenPairResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    user_agent = request.headers.get("User-Agent")
    return login_step_two(
        db=db,
        user=user,
        method=payload.metodo,
        code=payload.codigo,
        client_ip=_client_ip(request),
        user_agent=user_agent,
        correlation_id=correlation_id,
    )


@router.post("/refrescar", response_model=TokenPairResponse)
def refresh_access_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenPairResponse:
    user_agent = request.headers.get("User-Agent")
    return refresh_session(db=db, refresh_token=payload.token_refresco, user_agent=user_agent)


@router.post("/salir")
def logout_session(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    revoke_session(db=db, user=current_user, refresh_token=payload.token_refresco)
    return {"mensaje": "Sesión cerrada y revocada."}


@router.post("/llave/opciones", response_model=PasskeyOptionsResponse)
def passkey_login_options(
    payload: PasskeyLoginOptionsRequest,
    db: Session = Depends(get_db),
) -> PasskeyOptionsResponse:
    normalized = payload.correo.strip().lower()
    user = db.scalar(select(User).where(User.correo == normalized))
    if user is None or not user.activo or not user.passkeys:
        raise ProblemDetailError(
            status=400,
            title="Sin llaves de acceso registradas",
            detail="Esta cuenta no tiene llaves de acceso registradas.",
            problem_type="https://exponexo.co/problemas/sin-llaves",
        )
    cred_ids = [p.credencial_id for p in user.passkeys]
    options, challenge_token = create_passkey_authentication_options(user.id, cred_ids)
    return PasskeyOptionsResponse(opciones=options, desafio_token=challenge_token)


@router.post("/llave", response_model=TokenPairResponse)
def passkey_login_verify(
    payload: PasskeyLoginVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenPairResponse:
    normalized = payload.correo.strip().lower()
    user = db.scalar(select(User).where(User.correo == normalized))
    if user is None or not user.activo:
        raise ProblemDetailError(
            status=401,
            title="Autenticación fallida",
            detail="No se pudo verificar la llave de acceso.",
            problem_type="https://exponexo.co/problemas/llave-invalida",
        )
    cred_id = payload.credencial.get("id")
    passkey = db.scalar(
        select(PasskeyCredential).where(
            PasskeyCredential.usuario_id == user.id,
            PasskeyCredential.credencial_id == cred_id,
        )
    )
    if passkey is None:
        raise ProblemDetailError(
            status=401,
            title="Llave desconocida",
            detail="La llave de acceso no pertenece a esta cuenta.",
            problem_type="https://exponexo.co/problemas/llave-invalida",
        )

    try:
        new_count = complete_passkey_authentication(
            expected_user_id=user.id,
            challenge_token=payload.desafio_token,
            credential_payload=payload.credencial,
            credential_public_key_b64=passkey.clave_publica,
            current_sign_count=passkey.contador,
        )
    except Exception as exc:
        raise ProblemDetailError(
            status=401,
            title="Verificación de llave fallida",
            detail="La firma de la llave de acceso no es válida.",
            problem_type="https://exponexo.co/problemas/llave-invalida",
        ) from exc

    passkey.contador = new_count
    passkey.ultimo_uso_en = datetime.now(timezone.utc)
    db.commit()
    return issue_session_tokens(db, user, user_agent=request.headers.get("User-Agent"))


@router.post("/servicio", response_model=ServiceTokenResponse)
def issue_internal_service_jwt(payload: ServiceTokenRequest) -> ServiceTokenResponse:
    settings = get_settings()
    if not settings.internal_secret or not secrets.compare_digest(
        payload.secreto_interno, settings.internal_secret
    ):
        raise ProblemDetailError(
            status=401,
            title="Secreto interno inválido",
            detail="Las credenciales de servicio no son válidas.",
            problem_type="https://exponexo.co/problemas/secreto-interno-invalido",
        )
    token, expires_in = create_service_token(payload.servicio)
    return ServiceTokenResponse(token_servicio=token, vence_en_segundos=expires_in)
