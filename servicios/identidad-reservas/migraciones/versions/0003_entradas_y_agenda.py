"""Tablas de entradas, salas, disponibilidad, citas y procedimiento aceptar_cita

Revision ID: 0003_entradas_y_agenda
Revises: 0002_catalogo_y_reservas
Create Date: 2026-11-02 13:55:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_entradas_y_agenda"
down_revision: Union[str, None] = "0002_catalogo_y_reservas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entradas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("evento_id", sa.String(length=36), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("orden_pago_id", sa.String(length=36), nullable=True),
        sa.Column("codigo_qr", sa.String(length=512), nullable=True),
        sa.Column("usada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usada_en_dispositivo", sa.String(length=64), nullable=True),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evento_id"], ["eventos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo_qr"),
        sa.CheckConstraint("tipo IN ('general', 'negocios', 'prensa')", name="ck_entradas_tipo"),
        sa.CheckConstraint(
            "estado IN ('pendiente_pago', 'activa', 'usada', 'cancelada')",
            name="ck_entradas_estado",
        ),
    )
    op.create_index("ix_entradas_evento_id", "entradas", ["evento_id"])
    op.create_index("ix_entradas_usuario_id", "entradas", ["usuario_id"])

    op.create_table(
        "salas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pabellon_id", sa.String(length=36), nullable=False),
        sa.Column("codigo", sa.String(length=32), nullable=False),
        sa.Column("capacidad", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["pabellon_id"], ["pabellones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pabellon_id", "codigo", name="uq_salas_pabellon_codigo"),
        sa.CheckConstraint("capacidad > 0", name="ck_salas_capacidad_positiva"),
    )
    op.create_index("ix_salas_pabellon_id", "salas", ["pabellon_id"])

    op.create_table(
        "disponibilidad",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("usuario_id", sa.String(length=36), nullable=False),
        sa.Column("evento_id", sa.String(length=36), nullable=False),
        sa.Column("desde", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hasta", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evento_id"], ["eventos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("hasta > desde", name="ck_disponibilidad_rango"),
    )
    op.create_index("ix_disponibilidad_usuario_id", "disponibilidad", ["usuario_id"])
    op.create_index("ix_disponibilidad_evento_id", "disponibilidad", ["evento_id"])

    op.create_table(
        "citas",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("evento_id", sa.String(length=36), nullable=False),
        sa.Column("solicitante_id", sa.String(length=36), nullable=False),
        sa.Column("anfitrion_id", sa.String(length=36), nullable=False),
        sa.Column("sala_id", sa.String(length=36), nullable=True),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("mensaje", sa.String(length=500), nullable=True),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evento_id"], ["eventos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["solicitante_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["anfitrion_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["sala_id"], ["salas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "solicitante_id <> anfitrion_id",
            name="ck_citas_participantes_distintos",
        ),
        sa.CheckConstraint("fin > inicio", name="ck_citas_rango_valido"),
        sa.CheckConstraint(
            "estado IN ('propuesta', 'aceptada', 'rechazada', 'cancelada')",
            name="ck_citas_estado",
        ),
    )
    op.create_index("ix_citas_evento_id", "citas", ["evento_id"])
    op.create_index("ix_citas_solicitante_id", "citas", ["solicitante_id"])
    op.create_index("ix_citas_anfitrion_id", "citas", ["anfitrion_id"])
    op.create_index("ix_citas_sala_id", "citas", ["sala_id"])

    bind = op.get_bind()
    if bind.dialect.name == "mssql":
        op.execute(
            """
            CREATE OR ALTER PROCEDURE dbo.aceptar_cita
                @cita_id VARCHAR(36),
                @anfitrion_id VARCHAR(36),
                @evento_outbox_id VARCHAR(36),
                @correlacion_id VARCHAR(64)
            AS
            BEGIN
                SET NOCOUNT ON;
                SET XACT_ABORT ON;

                BEGIN TRANSACTION;

                DECLARE @evento_id VARCHAR(36);
                DECLARE @solicitante_id VARCHAR(36);
                DECLARE @anfitrion_actual VARCHAR(36);
                DECLARE @inicio DATETIME2;
                DECLARE @fin DATETIME2;
                DECLARE @estado_actual VARCHAR(20);
                DECLARE @sala_id VARCHAR(36);

                SELECT
                    @evento_id = evento_id,
                    @solicitante_id = solicitante_id,
                    @anfitrion_actual = anfitrion_id,
                    @inicio = inicio,
                    @fin = fin,
                    @estado_actual = estado
                FROM dbo.citas WITH (UPDLOCK, HOLDLOCK)
                WHERE id = @cita_id;

                IF @evento_id IS NULL
                BEGIN
                    ROLLBACK TRANSACTION;
                    THROW 50010, 'Cita no encontrada.', 1;
                END

                IF @anfitrion_actual <> @anfitrion_id
                BEGIN
                    ROLLBACK TRANSACTION;
                    THROW 50011, 'Solo el anfitrion puede aceptar la cita.', 1;
                END

                IF @estado_actual <> 'propuesta'
                BEGIN
                    ROLLBACK TRANSACTION;
                    THROW 50012, 'La cita no esta en estado propuesta.', 1;
                END

                IF EXISTS (
                    SELECT 1
                    FROM dbo.citas WITH (UPDLOCK, HOLDLOCK)
                    WHERE evento_id = @evento_id
                      AND estado = 'aceptada'
                      AND inicio < @fin
                      AND fin > @inicio
                      AND (
                          solicitante_id IN (@solicitante_id, @anfitrion_id)
                          OR anfitrion_id IN (@solicitante_id, @anfitrion_id)
                      )
                )
                BEGIN
                    ROLLBACK TRANSACTION;
                    THROW 50013, 'Uno de los participantes ya tiene una cita aceptada en ese horario.', 1;
                END

                SELECT TOP 1 @sala_id = s.id
                FROM dbo.salas s WITH (UPDLOCK, HOLDLOCK)
                -- Las salas son del recinto (no de un evento): sirve cualquiera libre en ese horario
                WHERE NOT EXISTS (
                      SELECT 1
                      FROM dbo.citas c
                      WHERE c.sala_id = s.id
                        AND c.estado = 'aceptada'
                        AND c.inicio < @fin
                        AND c.fin > @inicio
                  )
                ORDER BY s.codigo ASC;

                IF @sala_id IS NULL
                BEGIN
                    ROLLBACK TRANSACTION;
                    THROW 50014, 'No hay salas libres en ese horario para el evento.', 1;
                END

                UPDATE dbo.citas
                SET estado = 'aceptada',
                    sala_id = @sala_id
                WHERE id = @cita_id;

                INSERT INTO dbo.bandeja_salida (id, tipo, carga, correlacion_id, creado_en, intentos)
                VALUES (
                    @evento_outbox_id,
                    'cita.aceptada',
                    CONCAT(
                        '{"cita":"', @cita_id,
                        '","evento":"', @evento_id,
                        '","sala":"', @sala_id,
                        '","solicitante":"', @solicitante_id,
                        '","anfitrion":"', @anfitrion_id, '"}'
                    ),
                    @correlacion_id,
                    SYSUTCDATETIME(),
                    0
                );

                COMMIT TRANSACTION;
            END
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mssql":
        op.execute("DROP PROCEDURE IF EXISTS dbo.aceptar_cita;")

    op.drop_index("ix_citas_sala_id", table_name="citas")
    op.drop_index("ix_citas_anfitrion_id", table_name="citas")
    op.drop_index("ix_citas_solicitante_id", table_name="citas")
    op.drop_index("ix_citas_evento_id", table_name="citas")
    op.drop_table("citas")

    op.drop_index("ix_disponibilidad_evento_id", table_name="disponibilidad")
    op.drop_index("ix_disponibilidad_usuario_id", table_name="disponibilidad")
    op.drop_table("disponibilidad")

    op.drop_index("ix_salas_pabellon_id", table_name="salas")
    op.drop_table("salas")

    op.drop_index("ix_entradas_usuario_id", table_name="entradas")
    op.drop_index("ix_entradas_evento_id", table_name="entradas")
    op.drop_table("entradas")
