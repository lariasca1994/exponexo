from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


class Company(Base):
    __tablename__ = "empresas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    nit: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    razon_social: Mapped[str] = mapped_column(String(150), nullable=False)
    sector: Mapped[str] = mapped_column(String(60), nullable=False)
    sitio_web: Mapped[str | None] = mapped_column(String(200), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(300), nullable=True)


class User(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('visitante', 'expositor', 'personal', 'administrador')",
            name="ck_usuarios_rol",
        ),
        Index("ix_usuarios_correo", "correo", unique=True),
        Index("ix_usuarios_empresa_id", "empresa_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    correo: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    hash_contrasena: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False, default="visitante")
    empresa_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("empresas.id"),
        nullable=True,
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    correo_verificado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Chat de Telegram vinculado por la propia persona desde su perfil (avisos personales)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    mfa_factors: Mapped[list["MfaFactor"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    verification_codes: Mapped[list["VerificationCode"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    backup_codes: Mapped[list["BackupCode"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    passkeys: Mapped[list["PasskeyCredential"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class MfaFactor(Base):
    __tablename__ = "factores_mfa"
    __table_args__ = (
        CheckConstraint("tipo IN ('app', 'correo')", name="ck_factores_mfa_tipo"),
        UniqueConstraint("usuario_id", "tipo", name="uq_factores_mfa_usuario_tipo"),
        Index("ix_factores_mfa_usuario_id", "usuario_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    secreto_cifrado: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    preferido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ultimo_paso: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    user: Mapped["User"] = relationship(back_populates="mfa_factors")


class VerificationCode(Base):
    __tablename__ = "codigos_verificacion"
    __table_args__ = (
        CheckConstraint(
            "proposito IN ('ingreso', 'confirmar_correo', 'recuperar', 'activar_correo', 'telegram')",
            name="ck_codigos_verificacion_proposito",
        ),
        Index("ix_codigos_verificacion_usuario_id", "usuario_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    proposito: Mapped[str] = mapped_column(String(30), nullable=False)
    huella: Mapped[str] = mapped_column(String(128), nullable=False)
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vence_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="verification_codes")


class BackupCode(Base):
    __tablename__ = "codigos_respaldo"
    __table_args__ = (Index("ix_codigos_respaldo_usuario_id", "usuario_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    huella: Mapped[str] = mapped_column(String(128), nullable=False)
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="backup_codes")


class PasskeyCredential(Base):
    __tablename__ = "llaves_acceso"
    __table_args__ = (
        Index("ix_llaves_acceso_usuario_id", "usuario_id"),
        Index("ix_llaves_acceso_credencial_id", "credencial_id", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    credencial_id: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    clave_publica: Mapped[str] = mapped_column(Text, nullable=False)
    contador: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    nombre_dispositivo: Mapped[str] = mapped_column(String(60), nullable=False)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    ultimo_uso_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="passkeys")


class UserSession(Base):
    __tablename__ = "sesiones"
    __table_args__ = (
        Index("ix_sesiones_usuario_id", "usuario_id"),
        Index("ix_sesiones_huella_token", "huella_token", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
    )
    huella_token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    vence_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revocada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    agente: Mapped[str | None] = mapped_column(String(200), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")


class LoginAttempt(Base):
    __tablename__ = "intentos_ingreso"
    __table_args__ = (
        Index("ix_intentos_correo_ocurrido", "correo_huella", "ocurrido_en"),
        Index("ix_intentos_ip_ocurrido", "ip_huella", "ocurrido_en"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    correo_huella: Mapped[str] = mapped_column(String(128), nullable=False)
    ip_huella: Mapped[str] = mapped_column(String(128), nullable=False)
    exito: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ocurrido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


class AuditLog(Base):
    __tablename__ = "auditoria"
    __table_args__ = (Index("ix_auditoria_usuario_id", "usuario_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    usuario_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    accion: Mapped[str] = mapped_column(String(40), nullable=False)
    entidad: Mapped[str] = mapped_column(String(60), nullable=False)
    entidad_id: Mapped[str] = mapped_column(String(64), nullable=False)
    detalle: Mapped[str | None] = mapped_column(String(400), nullable=True)
    correlacion_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ocurrido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


class OutboxEvent(Base):
    __tablename__ = "bandeja_salida"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tipo: Mapped[str] = mapped_column(String(60), nullable=False)
    carga: Mapped[str] = mapped_column(Text, nullable=False)
    correlacion_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    publicado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ProcessedEvent(Base):
    __tablename__ = "eventos_procesados"

    evento_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    procesado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
