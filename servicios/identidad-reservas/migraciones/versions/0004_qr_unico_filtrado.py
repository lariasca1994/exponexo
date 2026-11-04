"""El código QR de las entradas es único solo cuando existe

En SQL Server una restricción UNIQUE sobre una columna que admite nulos permite un único NULL: la
segunda entrada pendiente de pago (aún sin QR) fallaba. Se reemplaza por un índice único filtrado.

Revision ID: 0004_qr_unico_filtrado
Revises: 0003_entradas_y_agenda
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_qr_unico_filtrado"
down_revision: Union[str, None] = "0003_entradas_y_agenda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mssql":
        # La restricción la nombró SQL Server al crear la tabla: se busca su nombre real
        op.execute(
            """
            DECLARE @nombre sysname = (
                SELECT kc.name FROM sys.key_constraints kc
                JOIN sys.index_columns ic ON ic.object_id = kc.parent_object_id AND ic.index_id = kc.unique_index_id
                JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
                WHERE kc.parent_object_id = OBJECT_ID('dbo.entradas') AND kc.type = 'UQ' AND c.name = 'codigo_qr');
            IF @nombre IS NOT NULL EXEC('ALTER TABLE dbo.entradas DROP CONSTRAINT ' + QUOTENAME(@nombre));
            """
        )
        op.create_index("uq_entradas_codigo_qr", "entradas", ["codigo_qr"], unique=True,
                        mssql_where=sa.text("codigo_qr IS NOT NULL"))
    else:
        with op.batch_alter_table("entradas") as batch:
            batch.create_index("uq_entradas_codigo_qr", ["codigo_qr"], unique=True,
                               sqlite_where=sa.text("codigo_qr IS NOT NULL"))


def downgrade() -> None:
    op.drop_index("uq_entradas_codigo_qr", table_name="entradas")
