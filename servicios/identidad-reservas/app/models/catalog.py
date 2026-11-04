from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.identity import new_uuid, utc_now


class Event(Base):
    __tablename__ = "eventos"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('borrador', 'publicado', 'en_curso', 'finalizado', 'cancelado')",
            name="ck_eventos_estado",
        ),
        Index("ix_eventos_slug", "slug", unique=True),
        Index("ix_eventos_estado", "estado"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="borrador")
    precio_entrada: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    aforo: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    imagen_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
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


class Pavilion(Base):
    __tablename__ = "pabellones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    capacidad_stands: Mapped[int] = mapped_column(Integer, nullable=False)
    plano_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
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

    stands: Mapped[list["Stand"]] = relationship(
        back_populates="pavilion",
        cascade="all, delete-orphan",
    )


class Stand(Base):
    __tablename__ = "stands"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('basico', 'esquinero', 'isla')",
            name="ck_stands_tipo",
        ),
        UniqueConstraint("pabellon_id", "codigo", name="uq_stands_pabellon_codigo"),
        Index("ix_stands_pabellon_id", "pabellon_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pabellon_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pabellones.id", ondelete="CASCADE"),
        nullable=False,
    )
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    metros_cuadrados: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="basico")
    precio_base: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fila: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    columna: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
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

    pavilion: Mapped["Pavilion"] = relationship(back_populates="stands")


class StandReservation(Base):
    __tablename__ = "reservas_stand"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente_pago', 'pagada', 'cancelada', 'vencida')",
            name="ck_reservas_stand_estado",
        ),
        # Filtered unique index: a stand cannot have two active reservations in the same event
        Index(
            "uq_reservas_stand_activa",
            "evento_id",
            "stand_id",
            unique=True,
            sqlite_where=text("estado IN ('pendiente_pago', 'pagada')"),
            mssql_where=text("estado IN ('pendiente_pago', 'pagada')"),
        ),
        UniqueConstraint(
            "usuario_id",
            "clave_idempotencia",
            name="uq_reservas_usuario_idempotencia",
        ),
        Index("ix_reservas_stand_evento_id", "evento_id"),
        Index("ix_reservas_stand_stand_id", "stand_id"),
        Index("ix_reservas_stand_empresa_id", "empresa_id"),
        Index("ix_reservas_stand_usuario_id", "usuario_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    evento_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("eventos.id"),
        nullable=False,
    )
    stand_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("stands.id"),
        nullable=False,
    )
    empresa_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("empresas.id"),
        nullable=True,
    )
    usuario_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id"),
        nullable=False,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pendiente_pago",
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    vence_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    orden_pago_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    clave_idempotencia: Mapped[str | None] = mapped_column(String(64), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
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
