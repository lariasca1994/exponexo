from datetime import datetime, timezone
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


class Ticket(Base):
    __tablename__ = "entradas"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('general', 'negocios', 'prensa')",
            name="ck_entradas_tipo",
        ),
        CheckConstraint(
            "estado IN ('pendiente_pago', 'activa', 'usada', 'cancelada')",
            name="ck_entradas_estado",
        ),
        # Único solo cuando existe: las entradas pendientes de pago aún no tienen QR
        Index(
            "uq_entradas_codigo_qr",
            "codigo_qr",
            unique=True,
            mssql_where=text("codigo_qr IS NOT NULL"),
            sqlite_where=text("codigo_qr IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    evento_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("eventos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="general")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente_pago")
    orden_pago_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    codigo_qr: Mapped[str | None] = mapped_column(String(512), nullable=True)
    usada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usada_en_dispositivo: Mapped[str | None] = mapped_column(String(64), nullable=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class MeetingRoom(Base):
    __tablename__ = "salas"
    __table_args__ = (
        UniqueConstraint("pabellon_id", "codigo", name="uq_salas_pabellon_codigo"),
        CheckConstraint("capacidad > 0", name="ck_salas_capacidad_positiva"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pabellon_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pabellones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo: Mapped[str] = mapped_column(String(32), nullable=False)
    capacidad: Mapped[int] = mapped_column(Integer, nullable=False, default=4)


class AvailabilitySlot(Base):
    __tablename__ = "disponibilidad"
    __table_args__ = (
        CheckConstraint("hasta > desde", name="ck_disponibilidad_rango"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evento_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("eventos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    desde: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hasta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BusinessAppointment(Base):
    __tablename__ = "citas"
    __table_args__ = (
        CheckConstraint("solicitante_id <> anfitrion_id", name="ck_citas_participantes_distintos"),
        CheckConstraint("fin > inicio", name="ck_citas_rango_valido"),
        CheckConstraint(
            "estado IN ('propuesta', 'aceptada', 'rechazada', 'cancelada')",
            name="ck_citas_estado",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    evento_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("eventos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    solicitante_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    anfitrion_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    sala_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("salas.id"),
        nullable=True,
        index=True,
    )
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="propuesta")
    mensaje: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
