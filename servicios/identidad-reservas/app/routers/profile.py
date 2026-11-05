from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ProblemDetailError
from app.models.identity import PasskeyCredential, User
from app.schemas.identity import (
    BackupCodesResponse,
    ChangePasswordRequest,
    TelegramLinkResponse,
    PasskeyInfo,
    PasskeyOptionsResponse,
    PasskeyRegisterRequest,
    SecurityProfileResponse,
    SetPreferredMfaRequest,
    TotpConfirmRequest,
    TotpSetupResponse,
)
from app.security.dependencies import get_current_user
from app.security.passkeys import (
    complete_passkey_registration,
    create_passkey_registration_options,
)
from app.services.identity_service import (
    change_password,
    confirm_totp_setup,
    start_telegram_link,
    unlink_telegram,
    enable_email_mfa,
    get_security_profile,
    regenerate_backup_codes,
    set_preferred_mfa,
    start_totp_setup,
)


router = APIRouter(prefix="/v1/perfil", tags=["Seguridad del perfil"])


@router.get("/seguridad", response_model=SecurityProfileResponse)
def read_security_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityProfileResponse:
    return get_security_profile(db=db, user=current_user)


@router.put("/contrasena")
def update_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    closed = change_password(
        db=db,
        user=current_user,
        current_password=payload.contrasena_actual,
        new_password=payload.nueva_contrasena,
        keep_refresh_token=payload.token_refresco,
    )
    return {"mensaje": "Contraseña actualizada.", "sesiones_cerradas": closed}


@router.post("/telegram", response_model=TelegramLinkResponse)
def create_telegram_link(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TelegramLinkResponse:
    return start_telegram_link(db=db, user=current_user)


@router.delete("/telegram", response_model=SecurityProfileResponse)
def remove_telegram_link(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityProfileResponse:
    return unlink_telegram(db=db, user=current_user)


@router.post("/mfa/app", response_model=TotpSetupResponse)
def initiate_totp_app(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TotpSetupResponse:
    return start_totp_setup(db=db, user=current_user)


@router.post("/mfa/app/confirmar", response_model=SecurityProfileResponse)
def confirm_totp_app(
    payload: TotpConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityProfileResponse:
    return confirm_totp_setup(db=db, user=current_user, code=payload.codigo)


@router.post("/mfa/correo", response_model=SecurityProfileResponse)
def activate_email_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityProfileResponse:
    return enable_email_mfa(db=db, user=current_user)


@router.put("/mfa/preferido", response_model=SecurityProfileResponse)
def update_preferred_mfa(
    payload: SetPreferredMfaRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SecurityProfileResponse:
    return set_preferred_mfa(db=db, user=current_user, factor_type=payload.tipo)


@router.post("/codigos-respaldo", response_model=BackupCodesResponse)
def create_backup_codes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BackupCodesResponse:
    codes = regenerate_backup_codes(db=db, user=current_user)
    return BackupCodesResponse(codigos=codes)


@router.post("/llaves/opciones", response_model=PasskeyOptionsResponse)
def register_passkey_options(
    current_user: User = Depends(get_current_user),
) -> PasskeyOptionsResponse:
    existing_ids = [p.credencial_id for p in current_user.passkeys]
    options, challenge_token = create_passkey_registration_options(
        user_id=current_user.id,
        email=current_user.correo,
        name=current_user.nombre,
        existing_credential_ids=existing_ids,
    )
    return PasskeyOptionsResponse(opciones=options, desafio_token=challenge_token)


@router.post("/llaves", response_model=PasskeyInfo, status_code=status.HTTP_201_CREATED)
def register_passkey(
    payload: PasskeyRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PasskeyInfo:
    try:
        cred_id, pub_key, sign_count = complete_passkey_registration(
            user_id=current_user.id,
            challenge_token=payload.desafio_token,
            credential_payload=payload.credencial,
        )
    except Exception as exc:
        raise ProblemDetailError(
            status=400,
            title="Error al registrar llave de acceso",
            detail="No se pudo verificar el registro de la llave WebAuthn.",
            problem_type="https://exponexo.co/problemas/llave-registro-invalido",
        ) from exc

    passkey = PasskeyCredential(
        usuario_id=current_user.id,
        credencial_id=cred_id,
        clave_publica=pub_key,
        contador=sign_count,
        nombre_dispositivo=payload.nombre_dispositivo.strip(),
    )
    db.add(passkey)
    db.commit()
    db.refresh(passkey)
    return PasskeyInfo(
        id=passkey.id,
        nombre_dispositivo=passkey.nombre_dispositivo,
        creada_en=passkey.creada_en,
        ultimo_uso_en=passkey.ultimo_uso_en,
    )
