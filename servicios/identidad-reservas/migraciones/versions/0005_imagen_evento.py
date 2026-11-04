"""Imagen de portada de los eventos

Revision ID: 0005_imagen_evento
Revises: 0004_qr_unico_filtrado
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_imagen_evento"
down_revision: Union[str, None] = "0004_qr_unico_filtrado"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("eventos", sa.Column("imagen_url", sa.String(length=300), nullable=True))


def downgrade() -> None:
    op.drop_column("eventos", "imagen_url")
