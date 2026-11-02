"""usuarios y mfa

Revision ID: 0001_usuarios_y_mfa
Revises: None
Create Date: 2026-11-02 12:40:00
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_usuarios_y_mfa"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "empresas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("nit", sa.String(length=20), nullable=False),
        sa.Column("razon_social", sa.String(length=150), nullable=False),
        sa.Column("sector", sa.String(length=60), nullable=False),
        sa.Column("sitio_web", sa.String(length=200), nullable=True),
        sa.Column("logo_url", sa.String(length=300), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nit"),
    )
    op.create_table(
        "usuarios",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("correo", sa.String(length=320), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("hash_contrasena", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("empresa_id", sa.String(length=36), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("correo_verificado", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "rol IN ('visitante', 'expositor', 'personal', 'administrador')",
            name="ck_usuarios_rol",
        ),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("correo"),
    )
    op.create_index("ix_usuarios_correo", "usuarios", ["correo"], unique=True)
    op.create_index("ix_usuarios_empresa_id", "usuarios", ["empresa_id"], unique=False)

    op.create_table(
        "factores_mfa",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("secreto_cifrado", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("preferido", sa.Boolean(), nullable=False),
        sa.Column("ultimo_paso", sa.BigInteger(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("tipo IN ('app', 'correo')", name="ck_factores_mfa_tipo"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id", "tipo", name="uq_factores_mfa_usuario_tipo"),
    )
    op.create_index("ix_factores_mfa_usuario_id", "factores_mfa", ["usuario_id"], unique=False)

    op.create_table(
        "codigos_verificacion",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), nullable=False),
        sa.Column("proposito", sa.String(length=30), nullable=False),
        sa.Column("huella", sa.String(length=128), nullable=False),
        sa.Column("intentos", sa.Integer(), nullable=False),
        sa.Column("vence_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usado_en", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "proposito IN ('ingreso', 'confirmar_correo', 'recuperar', 'activar_correo')",
            name="ck_codigos_verificacion_proposito",
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_codigos_verificacion_usuario_id",
        "codigos_verificacion",
        ["usuario_id"],
        unique=False,
    )

    op.create_table(
        "codigos_respaldo",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), nullable=False),
        sa.Column("huella", sa.String(length=128), nullable=False),
        sa.Column("usado_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_codigos_respaldo_usuario_id",
        "codigos_respaldo",
        ["usuario_id"],
        unique=False,
    )

    op.create_table(
        "llaves_acceso",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), nullable=False),
        sa.Column("credencial_id", sa.String(length=512), nullable=False),
        sa.Column("clave_publica", sa.Text(), nullable=False),
        sa.Column("contador", sa.BigInteger(), nullable=False),
        sa.Column("nombre_dispositivo", sa.String(length=60), nullable=False),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultimo_uso_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("credencial_id"),
    )
    op.create_index("ix_llaves_acceso_usuario_id", "llaves_acceso", ["usuario_id"], unique=False)
    op.create_index(
        "ix_llaves_acceso_credencial_id",
        "llaves_acceso",
        ["credencial_id"],
        unique=True,
    )

    op.create_table(
        "sesiones",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), nullable=False),
        sa.Column("huella_token", sa.String(length=128), nullable=False),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vence_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("agente", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("huella_token"),
    )
    op.create_index("ix_sesiones_usuario_id", "sesiones", ["usuario_id"], unique=False)
    op.create_index("ix_sesiones_huella_token", "sesiones", ["huella_token"], unique=True)

    op.create_table(
        "intentos_ingreso",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("correo_huella", sa.String(length=128), nullable=False),
        sa.Column("ip_huella", sa.String(length=128), nullable=False),
        sa.Column("exito", sa.Boolean(), nullable=False),
        sa.Column("ocurrido_en", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_intentos_correo_ocurrido",
        "intentos_ingreso",
        ["correo_huella", "ocurrido_en"],
        unique=False,
    )
    op.create_index(
        "ix_intentos_ip_ocurrido",
        "intentos_ingreso",
        ["ip_huella", "ocurrido_en"],
        unique=False,
    )

    op.create_table(
        "auditoria",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), nullable=True),
        sa.Column("accion", sa.String(length=40), nullable=False),
        sa.Column("entidad", sa.String(length=60), nullable=False),
        sa.Column("entidad_id", sa.String(length=64), nullable=False),
        sa.Column("detalle", sa.String(length=400), nullable=True),
        sa.Column("correlacion_id", sa.String(length=64), nullable=True),
        sa.Column("ocurrido_en", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auditoria_usuario_id", "auditoria", ["usuario_id"], unique=False)

    op.create_table(
        "bandeja_salida",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tipo", sa.String(length=60), nullable=False),
        sa.Column("carga", sa.Text(), nullable=False),
        sa.Column("correlacion_id", sa.String(length=64), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("publicado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("intentos", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eventos_procesados",
        sa.Column("evento_id", sa.String(length=36), nullable=False),
        sa.Column("procesado_en", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("evento_id"),
    )


def downgrade() -> None:
    op.drop_table("eventos_procesados")
    op.drop_table("bandeja_salida")
    op.drop_table("auditoria")
    op.drop_table("intentos_ingreso")
    op.drop_table("sesiones")
    op.drop_table("llaves_acceso")
    op.drop_table("codigos_respaldo")
    op.drop_table("codigos_verificacion")
    op.drop_table("factores_mfa")
    op.drop_table("usuarios")
    op.drop_table("empresas")
