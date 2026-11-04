from datetime import datetime, timedelta, timezone
import json
import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import ProblemDetailError
from app.models.identity import (
    AuditLog,
    BackupCode,
    LoginAttempt,
    MfaFactor,
    OutboxEvent,
    User,
    UserSession,
    VerificationCode,
)
from app.schemas.identity import (
    AccountResponse,
    LoginStep1Response,
    MfaFactorInfo,
    PasskeyInfo,
    RegisterAccountRequest,
    SecurityProfileResponse,
    SessionInfo,
    TokenPairResponse,
    TotpSetupResponse,
)
from app.security.encryption import decrypt_secret, encrypt_secret
from app.security.mfa import (
    build_totp_provisioning_uri,
    generate_backup_codes,
    generate_email_otp_code,
    generate_qr_data_url,
    generate_totp_secret,
    verify_totp_code,
)
from app.security.passwords import (
    hash_fingerprint,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.security.tokens import (
    create_access_token,
    create_mfa_pass_token,
    create_refresh_token_raw,
)
from app.services.email_sender import send_verification_email


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _record_audit(
    db: Session,
    user_id: str | None,
    action: str,
    entity: str,
    entity_id: str,
    detail: str | None = None,
    correlation_id: str | None = None,
) -> None:
    db.add(
        AuditLog(
            usuario_id=user_id,
            accion=action,
            entidad=entity,
            entidad_id=entity_id,
            detalle=detail,
            correlacion_id=correlation_id,
        )
    )


def _record_outbox_event(
    db: Session,
    event_type: str,
    payload_data: dict,
    correlation_id: str | None = None,
) -> None:
    event = OutboxEvent(
        tipo=event_type,
        carga=json.dumps(payload_data, ensure_ascii=False),
        correlacion_id=correlation_id,
    )
    db.add(event)


def _check_account_lockout(db: Session, email: str, client_ip: str) -> None:
    settings = get_settings()
    window_start = datetime.now(timezone.utc) - timedelta(minutes=settings.mfa_lockout_minutes)
    email_fp = hash_fingerprint(email.lower())
    ip_fp = hash_fingerprint(client_ip)

    recent_failures = db.scalar(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.correo_huella == email_fp,
            LoginAttempt.exito == False,  # noqa: E712
            LoginAttempt.ocurrido_en >= window_start,
        )
    ) or 0

    ip_failures = db.scalar(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.ip_huella == ip_fp,
            LoginAttempt.exito == False,  # noqa: E712
            LoginAttempt.ocurrido_en >= window_start,
        )
    ) or 0

    if recent_failures >= settings.mfa_max_attempts or ip_failures >= settings.mfa_max_attempts * 2:
        raise ProblemDetailError(
            status=429,
            title="Cuenta bloqueada temporalmente",
            detail=(
                "Demasiados intentos fallidos. Espera unos minutos antes de volver a intentarlo."
            ),
            problem_type="https://exponexo.co/problemas/cuenta-bloqueada",
        )


def _record_login_attempt(db: Session, email: str, client_ip: str, success: bool) -> None:
    db.add(
        LoginAttempt(
            correo_huella=hash_fingerprint(email.lower()),
            ip_huella=hash_fingerprint(client_ip),
            exito=success,
        )
    )


def register_account(
    db: Session,
    payload: RegisterAccountRequest,
    correlation_id: str | None = None,
) -> User:
    normalized_email = payload.correo.strip().lower()
    existing = db.scalar(select(User).where(User.correo == normalized_email))
    if existing is not None:
        raise ProblemDetailError(
            status=409,
            title="Correo ya registrado",
            detail="Ya existe una cuenta registrada con este correo electrónico.",
            problem_type="https://exponexo.co/problemas/correo-duplicado",
        )

    strength_error = validate_password_strength(payload.contrasena)
    if strength_error:
        raise ProblemDetailError(
            status=422,
            title="Contraseña débil",
            detail=strength_error,
            problem_type="https://exponexo.co/problemas/contrasena-debil",
        )

    user = User(
        correo=normalized_email,
        nombre=payload.nombre.strip(),
        hash_contrasena=hash_password(payload.contrasena),
        rol=payload.rol,
        activo=True,
        correo_verificado=False,
    )
    db.add(user)
    db.flush()

    # Enable email MFA factor by default so 2FA is mandatory from the very first sign-in
    email_factor = MfaFactor(
        usuario_id=user.id,
        tipo="correo",
        secreto_cifrado=None,
        activo=True,
        preferido=True,
    )
    db.add(email_factor)

    # Create email confirmation code
    settings = get_settings()
    raw_code = generate_email_otp_code()
    db.add(
        VerificationCode(
            usuario_id=user.id,
            proposito="confirmar_correo",
            huella=hash_fingerprint(raw_code),
            vence_en=datetime.now(timezone.utc) + timedelta(minutes=settings.mfa_email_code_minutes),
        )
    )

    _record_outbox_event(
        db=db,
        event_type="cuenta.creada",
        payload_data={
            "usuario_id": user.id,
            "correo": user.correo,
            "nombre": user.nombre,
            "rol": user.rol,
        },
        correlation_id=correlation_id,
    )
    _record_audit(
        db=db,
        user_id=user.id,
        action="cuenta.creada",
        entity="usuarios",
        entity_id=user.id,
        detail=f"Registro de cuenta con rol {user.rol}",
        correlation_id=correlation_id,
    )
    db.commit()
    db.refresh(user)

    send_verification_email(user.correo, user.nombre, raw_code, "confirmar_correo")
    return user


def confirm_email(db: Session, email: str, code: str) -> AccountResponse:
    normalized = email.strip().lower()
    user = db.scalar(select(User).where(User.correo == normalized))
    if user is None:
        raise ProblemDetailError(
            status=404,
            title="Cuenta no encontrada",
            detail="No se encontró una cuenta con el correo indicado.",
            problem_type="https://exponexo.co/problemas/cuenta-no-encontrada",
        )

    code_fp = hash_fingerprint(code)
    now = datetime.now(timezone.utc)
    verification = db.scalar(
        select(VerificationCode)
        .where(
            VerificationCode.usuario_id == user.id,
            VerificationCode.proposito == "confirmar_correo",
            VerificationCode.usado_en.is_(None),
        )
        .order_by(VerificationCode.vence_en.desc())
    )
    if (
        verification is None
        or _ensure_utc(verification.vence_en) < now
        or verification.huella != code_fp
    ):
        if verification is not None:
            verification.intentos += 1
            db.commit()
        raise ProblemDetailError(
            status=400,
            title="Código inválido o vencido",
            detail="El código de confirmación no es válido o ya expiró.",
            problem_type="https://exponexo.co/problemas/codigo-invalido",
        )

    verification.usado_en = now
    user.correo_verificado = True
    db.commit()
    db.refresh(user)
    return AccountResponse.model_validate(user)


def login_step_one(
    db: Session,
    email: str,
    password: str,
    client_ip: str,
    correlation_id: str | None = None,
) -> LoginStep1Response:
    normalized_email = email.strip().lower()
    _check_account_lockout(db, normalized_email, client_ip)

    user = db.scalar(select(User).where(User.correo == normalized_email))
    if user is None or not user.activo or not verify_password(user.hash_contrasena, password):
        _record_login_attempt(db, normalized_email, client_ip, success=False)
        _record_audit(
            db=db,
            user_id=user.id if user else None,
            action="ingreso.fallido",
            entity="usuarios",
            entity_id=user.id if user else normalized_email,
            detail="Credenciales inválidas en paso 1",
            correlation_id=correlation_id,
        )
        db.commit()
        raise ProblemDetailError(
            status=401,
            title="Credenciales inválidas",
            detail="El correo o la contraseña son incorrectos.",
            problem_type="https://exponexo.co/problemas/credenciales-invalidas",
        )

    active_factors = list(
        db.scalars(
            select(MfaFactor).where(
                MfaFactor.usuario_id == user.id,
                MfaFactor.activo == True,  # noqa: E712
            )
        )
    )
    methods = [f.tipo for f in active_factors]
    if not methods:
        methods = ["correo"]
    preferred = next((f.tipo for f in active_factors if f.preferido), methods[0])
    has_app = any(f.tipo == "app" for f in active_factors)

    pass_token, expires_in = create_mfa_pass_token(user.id, user.correo)
    return LoginStep1Response(
        pase_segundo_paso=pass_token,
        vence_en_segundos=expires_in,
        metodos_disponibles=methods,
        metodo_preferido=preferred,
        requiere_configurar_mfa=not has_app,
    )


def send_login_email_code(db: Session, user: User) -> None:
    settings = get_settings()
    raw_code = generate_email_otp_code()
    db.add(
        VerificationCode(
            usuario_id=user.id,
            proposito="ingreso",
            huella=hash_fingerprint(raw_code),
            vence_en=datetime.now(timezone.utc) + timedelta(minutes=settings.mfa_email_code_minutes),
        )
    )
    db.commit()
    send_verification_email(user.correo, user.nombre, raw_code, "ingreso")


def issue_session_tokens(
    db: Session,
    user: User,
    user_agent: str | None = None,
) -> TokenPairResponse:
    settings = get_settings()
    access_token, expires_in = create_access_token(
        user_id=user.id,
        email=user.correo,
        name=user.nombre,
        role=user.rol,
    )
    refresh_raw = create_refresh_token_raw()
    now = datetime.now(timezone.utc)
    session_row = UserSession(
        usuario_id=user.id,
        huella_token=hash_fingerprint(refresh_raw),
        creada_en=now,
        vence_en=now + timedelta(days=settings.jwt_refresh_days),
        agente=(user_agent or "Portal Web")[:200],
    )
    db.add(session_row)
    db.commit()

    return TokenPairResponse(
        token_acceso=access_token,
        token_refresco=refresh_raw,
        vence_en_segundos=expires_in,
        usuario=AccountResponse.model_validate(user),
    )


def login_step_two(
    db: Session,
    user: User,
    method: str,
    code: str,
    client_ip: str,
    user_agent: str | None = None,
    correlation_id: str | None = None,
) -> TokenPairResponse:
    _check_account_lockout(db, user.correo, client_ip)
    now = datetime.now(timezone.utc)
    verified = False

    if method == "app":
        factor = db.scalar(
            select(MfaFactor).where(
                MfaFactor.usuario_id == user.id,
                MfaFactor.tipo == "app",
                MfaFactor.activo == True,  # noqa: E712
            )
        )
        if factor and factor.secreto_cifrado:
            secret = decrypt_secret(factor.secreto_cifrado)
            ok, accepted_step = verify_totp_code(secret, code, factor.ultimo_paso)
            if ok and accepted_step is not None:
                factor.ultimo_paso = accepted_step
                verified = True

    elif method == "correo":
        code_fp = hash_fingerprint(code)
        verif = db.scalar(
            select(VerificationCode)
            .where(
                VerificationCode.usuario_id == user.id,
                VerificationCode.proposito == "ingreso",
                VerificationCode.usado_en.is_(None),
            )
            .order_by(VerificationCode.vence_en.desc())
        )
        if verif is not None and _ensure_utc(verif.vence_en) >= now:
            if secrets.compare_digest(verif.huella, code_fp):
                verif.usado_en = now
                verified = True
            else:
                verif.intentos += 1

    elif method == "respaldo":
        code_fp = hash_fingerprint(code.upper())
        backup = db.scalar(
            select(BackupCode).where(
                BackupCode.usuario_id == user.id,
                BackupCode.huella == code_fp,
                BackupCode.usado_en.is_(None),
            )
        )
        if backup is not None:
            backup.usado_en = now
            verified = True

    if not verified:
        _record_login_attempt(db, user.correo, client_ip, success=False)
        _record_audit(
            db=db,
            user_id=user.id,
            action="mfa.fallido",
            entity="usuarios",
            entity_id=user.id,
            detail=f"Código de segundo paso inválido ({method})",
            correlation_id=correlation_id,
        )
        db.commit()
        raise ProblemDetailError(
            status=401,
            title="Código de verificación inválido",
            detail="El código ingresado es incorrecto, ya fue utilizado o ha expirado.",
            problem_type="https://exponexo.co/problemas/codigo-mfa-invalido",
        )

    _record_login_attempt(db, user.correo, client_ip, success=True)
    _record_audit(
        db=db,
        user_id=user.id,
        action="ingreso.exitoso",
        entity="usuarios",
        entity_id=user.id,
        detail=f"Ingreso verificado con {method}",
        correlation_id=correlation_id,
    )
    return issue_session_tokens(db, user, user_agent=user_agent)


def refresh_session(
    db: Session,
    refresh_token: str,
    user_agent: str | None = None,
) -> TokenPairResponse:
    token_fp = hash_fingerprint(refresh_token)
    now = datetime.now(timezone.utc)
    session_row = db.scalar(
        select(UserSession).where(UserSession.huella_token == token_fp)
    )
    if (
        session_row is None
        or session_row.revocada_en is not None
        or _ensure_utc(session_row.vence_en) < now
    ):
        raise ProblemDetailError(
            status=401,
            title="Sesión inválida o revocada",
            detail="El token de refresco no es válido o la sesión ya fue cerrada.",
            problem_type="https://exponexo.co/problemas/sesion-invalida",
        )

    user = db.scalar(select(User).where(User.id == session_row.usuario_id))
    if user is None or not user.activo:
        raise ProblemDetailError(
            status=401,
            title="Cuenta inactiva",
            detail="El usuario asociado a la sesión no está activo.",
            problem_type="https://exponexo.co/problemas/cuenta-inactiva",
        )

    # Rotate refresh token
    session_row.revocada_en = now
    return issue_session_tokens(db, user, user_agent=user_agent)


def revoke_session(db: Session, user: User, refresh_token: str) -> None:
    token_fp = hash_fingerprint(refresh_token)
    session_row = db.scalar(
        select(UserSession).where(
            UserSession.usuario_id == user.id,
            UserSession.huella_token == token_fp,
        )
    )
    if session_row and session_row.revocada_en is None:
        session_row.revocada_en = datetime.now(timezone.utc)
        db.commit()


def start_totp_setup(db: Session, user: User) -> TotpSetupResponse:
    secret = generate_totp_secret()
    encrypted = encrypt_secret(secret)

    factor = db.scalar(
        select(MfaFactor).where(
            MfaFactor.usuario_id == user.id,
            MfaFactor.tipo == "app",
        )
    )
    if factor is None:
        factor = MfaFactor(
            usuario_id=user.id,
            tipo="app",
            secreto_cifrado=encrypted,
            activo=False,
            preferido=False,
            ultimo_paso=None,
        )
        db.add(factor)
    else:
        factor.secreto_cifrado = encrypted
        factor.activo = False
        factor.ultimo_paso = None

    db.commit()
    otpauth_url = build_totp_provisioning_uri(secret, user.correo)
    qr_data_url = generate_qr_data_url(otpauth_url)
    return TotpSetupResponse(
        secreto=secret,
        otpauth_url=otpauth_url,
        qr_datos_url=qr_data_url,
    )


def confirm_totp_setup(db: Session, user: User, code: str) -> SecurityProfileResponse:
    factor = db.scalar(
        select(MfaFactor).where(
            MfaFactor.usuario_id == user.id,
            MfaFactor.tipo == "app",
        )
    )
    if factor is None or not factor.secreto_cifrado:
        raise ProblemDetailError(
            status=400,
            title="Configuración no iniciada",
            detail="Primero debes iniciar la configuración de la app autenticadora.",
            problem_type="https://exponexo.co/problemas/mfa-no-iniciado",
        )

    secret = decrypt_secret(factor.secreto_cifrado)
    ok, accepted_step = verify_totp_code(secret, code, factor.ultimo_paso)
    if not ok or accepted_step is None:
        raise ProblemDetailError(
            status=400,
            title="Código TOTP inválido",
            detail="El código de la app autenticadora es incorrecto o ya fue utilizado.",
            problem_type="https://exponexo.co/problemas/codigo-totp-invalido",
        )

    # Set only this factor as preferred
    for other in db.scalars(select(MfaFactor).where(MfaFactor.usuario_id == user.id)):
        other.preferido = False

    factor.activo = True
    factor.preferido = True
    factor.ultimo_paso = accepted_step
    db.commit()
    return get_security_profile(db, user)


def enable_email_mfa(db: Session, user: User) -> SecurityProfileResponse:
    factor = db.scalar(
        select(MfaFactor).where(
            MfaFactor.usuario_id == user.id,
            MfaFactor.tipo == "correo",
        )
    )
    if factor is None:
        factor = MfaFactor(
            usuario_id=user.id,
            tipo="correo",
            activo=True,
            preferido=False,
        )
        db.add(factor)
    else:
        factor.activo = True
    db.commit()
    return get_security_profile(db, user)


def set_preferred_mfa(db: Session, user: User, factor_type: str) -> SecurityProfileResponse:
    factors = list(db.scalars(select(MfaFactor).where(MfaFactor.usuario_id == user.id)))
    target = next((f for f in factors if f.tipo == factor_type and f.activo), None)
    if target is None:
        raise ProblemDetailError(
            status=400,
            title="Método MFA no activo",
            detail=f"El método '{factor_type}' no está activo en tu cuenta.",
            problem_type="https://exponexo.co/problemas/mfa-no-activo",
        )
    for f in factors:
        f.preferido = f.id == target.id
    db.commit()
    return get_security_profile(db, user)


def regenerate_backup_codes(db: Session, user: User) -> list[str]:
    existing = list(db.scalars(select(BackupCode).where(BackupCode.usuario_id == user.id)))
    for row in existing:
        db.delete(row)

    plain_codes = generate_backup_codes(count=8)
    for code in plain_codes:
        db.add(
            BackupCode(
                usuario_id=user.id,
                huella=hash_fingerprint(code.upper()),
            )
        )
    db.commit()
    return plain_codes


def get_security_profile(db: Session, user: User) -> SecurityProfileResponse:
    factors = list(db.scalars(select(MfaFactor).where(MfaFactor.usuario_id == user.id)))
    preferred = next((f.tipo for f in factors if f.preferido and f.activo), None)
    unused_backups = db.scalar(
        select(func.count(BackupCode.id)).where(
            BackupCode.usuario_id == user.id,
            BackupCode.usado_en.is_(None),
        )
    ) or 0
    now = datetime.now(timezone.utc)
    active_sessions = [
        s
        for s in user.sessions
        if s.revocada_en is None and _ensure_utc(s.vence_en) > now
    ]
    return SecurityProfileResponse(
        usuario=AccountResponse.model_validate(user),
        metodos_mfa=[
            MfaFactorInfo(
                tipo=f.tipo,
                activo=f.activo,
                preferido=f.preferido,
                creado_en=f.creado_en,
            )
            for f in factors
        ],
        metodo_preferido=preferred,
        codigos_respaldo_disponibles=unused_backups,
        llaves_acceso=[
            PasskeyInfo(
                id=p.id,
                nombre_dispositivo=p.nombre_dispositivo,
                creada_en=p.creada_en,
                ultimo_uso_en=p.ultimo_uso_en,
            )
            for p in user.passkeys
        ],
        sesiones_activas=[
            SessionInfo(
                id=s.id,
                creada_en=s.creada_en,
                vence_en=s.vence_en,
                agente=s.agente,
            )
            for s in active_sessions
        ],
    )
