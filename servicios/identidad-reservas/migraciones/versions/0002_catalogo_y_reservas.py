"""catalogo y reservas

Revision ID: 0002_catalogo_y_reservas
Revises: 0001_usuarios_y_mfa
Create Date: 2026-11-02 13:15:00
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002_catalogo_y_reservas"
down_revision: str | None = "0001_usuarios_y_mfa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TSQL_RESERVAR_STAND = """
CREATE OR ALTER PROCEDURE dbo.reservar_stand
    @reserva_id NVARCHAR(36),
    @evento_id NVARCHAR(36),
    @stand_id NVARCHAR(36),
    @empresa_id NVARCHAR(36) = NULL,
    @usuario_id NVARCHAR(36),
    @minutos_vencimiento INT,
    @clave_idempotencia NVARCHAR(64) = NULL,
    @correlacion_id NVARCHAR(64) = NULL,
    @evento_salida_id NVARCHAR(36),
    @monto_out DECIMAL(12,2) OUTPUT,
    @vence_en_out DATETIME2 OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @estado_evento NVARCHAR(20);
        SELECT @estado_evento = estado
        FROM dbo.eventos WITH (UPDLOCK, HOLDLOCK)
        WHERE id = @evento_id;

        IF @estado_evento IS NULL OR @estado_evento NOT IN ('publicado', 'en_curso')
        BEGIN
            THROW 50001, 'El evento no existe o no está disponible para reservas.', 1;
        END

        SELECT @monto_out = precio_base
        FROM dbo.stands WITH (UPDLOCK, HOLDLOCK)
        WHERE id = @stand_id;

        IF @monto_out IS NULL
        BEGIN
            THROW 50002, 'El stand indicado no existe.', 1;
        END

        IF EXISTS (
            SELECT 1
            FROM dbo.reservas_stand WITH (UPDLOCK, HOLDLOCK)
            WHERE evento_id = @evento_id
              AND stand_id = @stand_id
              AND estado IN ('pendiente_pago', 'pagada')
        )
        BEGIN
            THROW 50003, 'El stand ya se encuentra reservado o pagado en este evento.', 1;
        END

        DECLARE @ahora DATETIME2 = SYSUTCDATETIME();
        SET @vence_en_out = DATEADD(MINUTE, @minutos_vencimiento, @ahora);

        INSERT INTO dbo.reservas_stand (
            id, evento_id, stand_id, empresa_id, usuario_id,
            estado, monto, vence_en, orden_pago_id, clave_idempotencia,
            version, creado_en, actualizado_en
        )
        VALUES (
            @reserva_id, @evento_id, @stand_id, @empresa_id, @usuario_id,
            'pendiente_pago', @monto_out, @vence_en_out, NULL, @clave_idempotencia,
            1, @ahora, @ahora
        );

        DECLARE @carga NVARCHAR(MAX) = (
            SELECT
                @reserva_id AS reserva_id,
                @evento_id AS evento_id,
                @stand_id AS stand_id,
                @usuario_id AS usuario_id,
                @monto_out AS monto,
                CONVERT(NVARCHAR(33), @vence_en_out, 127) AS vence_en
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        );

        INSERT INTO dbo.bandeja_salida (
            id, tipo, carga, correlacion_id, creado_en, publicado_en, intentos
        )
        VALUES (
            @evento_salida_id, 'reserva.creada', @carga, @correlacion_id, @ahora, NULL, 0
        );

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
"""

TSQL_MARCAR_RESERVA_PAGADA = """
CREATE OR ALTER PROCEDURE dbo.marcar_reserva_pagada
    @reserva_id NVARCHAR(36),
    @orden_pago_id NVARCHAR(64),
    @evento_recibido_id NVARCHAR(36),
    @evento_salida_id NVARCHAR(36),
    @correlacion_id NVARCHAR(64) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (
            SELECT 1 FROM dbo.eventos_procesados WITH (UPDLOCK, HOLDLOCK)
            WHERE evento_id = @evento_recibido_id
        )
        BEGIN
            DECLARE @ahora DATETIME2 = SYSUTCDATETIME();

            UPDATE dbo.reservas_stand
            SET estado = 'pagada',
                orden_pago_id = @orden_pago_id,
                version = version + 1,
                actualizado_en = @ahora
            WHERE id = @reserva_id;

            INSERT INTO dbo.eventos_procesados (evento_id, procesado_en)
            VALUES (@evento_recibido_id, @ahora);

            DECLARE @carga NVARCHAR(MAX) = (
                SELECT @reserva_id AS reserva_id, @orden_pago_id AS orden_pago_id
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
            );

            INSERT INTO dbo.bandeja_salida (
                id, tipo, carga, correlacion_id, creado_en, publicado_en, intentos
            )
            VALUES (
                @evento_salida_id, 'reserva.pagada', @carga, @correlacion_id, @ahora, NULL, 0
            );
        END

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
"""

TSQL_VENCER_RESERVAS = """
CREATE OR ALTER PROCEDURE dbo.vencer_reservas
    @fecha_corte DATETIME2,
    @cantidad_vencida INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        UPDATE dbo.reservas_stand
        SET estado = 'vencida',
            version = version + 1,
            actualizado_en = @fecha_corte
        WHERE estado = 'pendiente_pago'
          AND vence_en <= @fecha_corte;

        SET @cantidad_vencida = @@ROWCOUNT;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
"""


def upgrade() -> None:
    op.create_table(
        "eventos",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("precio_entrada", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("aforo", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "estado IN ('borrador', 'publicado', 'en_curso', 'finalizado', 'cancelado')",
            name="ck_eventos_estado",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_eventos_slug", "eventos", ["slug"], unique=True)
    op.create_index("ix_eventos_estado", "eventos", ["estado"], unique=False)

    op.create_table(
        "pabellones",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("nombre", sa.String(length=60), nullable=False),
        sa.Column("capacidad_stands", sa.Integer(), nullable=False),
        sa.Column("plano_url", sa.String(length=300), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "stands",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("pabellon_id", sa.String(length=36), nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("metros_cuadrados", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("precio_base", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("fila", sa.Integer(), nullable=False),
        sa.Column("columna", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "tipo IN ('basico', 'esquinero', 'isla')",
            name="ck_stands_tipo",
        ),
        sa.ForeignKeyConstraint(["pabellon_id"], ["pabellones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pabellon_id", "codigo", name="uq_stands_pabellon_codigo"),
    )
    op.create_index("ix_stands_pabellon_id", "stands", ["pabellon_id"], unique=False)

    op.create_table(
        "reservas_stand",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("evento_id", sa.String(length=36), nullable=False),
        sa.Column("stand_id", sa.String(length=36), nullable=False),
        sa.Column("empresa_id", sa.String(length=36), nullable=True),
        sa.Column("usuario_id", sa.String(length=36), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("monto", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("vence_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("orden_pago_id", sa.String(length=64), nullable=True),
        sa.Column("clave_idempotencia", sa.String(length=64), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "estado IN ('pendiente_pago', 'pagada', 'cancelada', 'vencida')",
            name="ck_reservas_stand_estado",
        ),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["evento_id"], ["eventos.id"]),
        sa.ForeignKeyConstraint(["stand_id"], ["stands.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "usuario_id",
            "clave_idempotencia",
            name="uq_reservas_usuario_idempotencia",
        ),
    )
    op.create_index(
        "uq_reservas_stand_activa",
        "reservas_stand",
        ["evento_id", "stand_id"],
        unique=True,
        sqlite_where=sa.text("estado IN ('pendiente_pago', 'pagada')"),
        mssql_where=sa.text("estado IN ('pendiente_pago', 'pagada')"),
    )
    op.create_index("ix_reservas_stand_evento_id", "reservas_stand", ["evento_id"], unique=False)
    op.create_index("ix_reservas_stand_stand_id", "reservas_stand", ["stand_id"], unique=False)
    op.create_index("ix_reservas_stand_empresa_id", "reservas_stand", ["empresa_id"], unique=False)
    op.create_index("ix_reservas_stand_usuario_id", "reservas_stand", ["usuario_id"], unique=False)

    if op.get_bind().dialect.name == "mssql":
        op.execute(TSQL_RESERVAR_STAND)
        op.execute(TSQL_MARCAR_RESERVA_PAGADA)
        op.execute(TSQL_VENCER_RESERVAS)


def downgrade() -> None:
    if op.get_bind().dialect.name == "mssql":
        op.execute("DROP PROCEDURE IF EXISTS dbo.vencer_reservas;")
        op.execute("DROP PROCEDURE IF EXISTS dbo.marcar_reserva_pagada;")
        op.execute("DROP PROCEDURE IF EXISTS dbo.reservar_stand;")

    op.drop_table("reservas_stand")
    op.drop_table("stands")
    op.drop_table("pabellones")
    op.drop_table("eventos")
