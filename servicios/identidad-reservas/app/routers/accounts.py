from datetime import datetime, timedelta, timezone
import secrets

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.errors import ProblemDetailError
from app.models.identity import User, VerificationCode
from app.schemas.identity import (
    AccountResponse,
    ConfirmEmailRequest,
    PasswordRecoveryRequest,
    RegisterAccountRequest,
)
from app.security.mfa import generate_email_otp_code
from app.security.passwords import (
    hash_fingerprint,
    hash_password,
    validate_password_strength,
)
from app.services.email_sender import send_verification_email
from app.services.identity_service import confirm_email, register_account


router = APIRouter(prefix="/v1/cuentas", tags=["Cuentas"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: RegisterAccountRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> AccountResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    user = register_account(db=db, payload=payload, correlation_id=correlation_id)
    return AccountResponse.model_validate(user)


@router.post("/confirmar-correo", response_model=AccountResponse)
def confirm_account_email(
    payload: ConfirmEmailRequest,
    db: Session = Depends(get_db),
) -> AccountResponse:
    return confirm_email(db=db, email=payload.correo, code=payload.codigo)


@router.post("/recuperar")
def recover_password(
    payload: PasswordRecoveryRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    normalized = payload.correo.strip().lower()
    user = db.scalar(select(User).where(User.correo == normalized))

    # Step A: request recovery code
    if payload.codigo is None or payload.nueva_contrasena is None:
        if user is not None and user.activo:
            settings = get_settings()
            raw_code = generate_email_otp_code()
            db.add(
                VerificationCode(
                    usuario_id=user.id,
                    proposito="recuperar",
                    huella=hash_fingerprint(raw_code),
                    vence_en=datetime.now(timezone.utc)
                    + timedelta(minutes=settings.mfa_email_code_minutes),
                )
            )
            db.commit()
            send_verification_email(user.correo, user.nombre, raw_code, "recuperar")
        return {
            "mensaje": "Si el correo existe, recibirás un código para restablecer tu contraseña."
        }

    # Step B: confirm recovery code and update password
    strength_error = validate_password_strength(payload.nueva_contrasena)
    if strength_error:
        raise ProblemDetailError(
            status=422,
            title="Contraseña débil",
            detail=strength_error,
            problem_type="https://exponexo.co/problemas/contrasena-debil",
        )

    if user is None:
        raise ProblemDetailError(
            status=400,
            title="Código inválido",
            detail="El código de recuperación es inválido o expiró.",
            problem_type="https://exponexo.co/problemas/codigo-invalido",
        )

    now = datetime.now(timezone.utc)
    verif = db.scalar(
        select(VerificationCode)
        .where(
            VerificationCode.usuario_id == user.id,
            VerificationCode.proposito == "recuperar",
            VerificationCode.usado_en.is_(None),
        )
        .order_by(VerificationCode.vence_en.desc())
    )
    vence_utc = (
        verif.vence_en.replace(tzinfo=timezone.utc)
        if verif and verif.vence_en.tzinfo is None
        else (verif.vence_en if verif else None)
    )
    if (
        verif is None
        or vence_utc is None
        or vence_utc < now
        or not secrets.compare_digest(verif.huella, hash_fingerprint(payload.codigo))
    ):
        if verif is not None:
            verif.intentos += 1
            db.commit()
        raise ProblemDetailError(
            status=400,
            title="Código inválido",
            detail="El código de recuperación es inválido o expiró.",
            problem_type="https://exponexo.co/problemas/codigo-invalido",
        )

    verif.usado_en = now
    user.hash_contrasena = hash_password(payload.nueva_contrasena)
    db.commit()
    return {"mensaje": "Contraseña actualizada correctamente."}
