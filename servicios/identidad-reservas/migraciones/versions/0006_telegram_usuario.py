"""Telegram de cada usuario para sus avisos

Revision ID: 0006_telegram_usuario
Revises: 0005_imagen_evento
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_telegram_usuario"
down_revision: Union[str, None] = "0005_imagen_evento"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PROPOSITOS_ANTES = "proposito IN ('ingreso', 'confirmar_correo', 'recuperar', 'activar_correo')"
PROPOSITOS = "proposito IN ('ingreso', 'confirmar_correo', 'recuperar', 'activar_correo', 'telegram')"


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("telegram_chat_id", sa.String(length=32), nullable=True))
    with op.batch_alter_table("codigos_verificacion") as tabla:
        tabla.drop_constraint("ck_codigos_verificacion_proposito", type_="check")
        tabla.create_check_constraint("ck_codigos_verificacion_proposito", PROPOSITOS)


def downgrade() -> None:
    op.execute("DELETE FROM codigos_verificacion WHERE proposito = 'telegram'")
    with op.batch_alter_table("codigos_verificacion") as tabla:
        tabla.drop_constraint("ck_codigos_verificacion_proposito", type_="check")
        tabla.create_check_constraint("ck_codigos_verificacion_proposito", PROPOSITOS_ANTES)
    op.drop_column("usuarios", "telegram_chat_id")
