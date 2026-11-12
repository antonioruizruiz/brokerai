"""vigila el avance de la descarga completa

Revision ID: c6d9e2f4a8b1
Revises: b3a7f1c9d2e4
Create Date: 2026-11-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6d9e2f4a8b1"
down_revision: Union[str, Sequence[str], None] = "b3a7f1c9d2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("sync_status", schema=None) as batch_op:
        batch_op.add_column(sa.Column("descarga_id", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("descarga_recuento_precios", sa.Integer(), nullable=False, server_default="0")
        )
        batch_op.add_column(sa.Column("descarga_ultimo_avance", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("sync_status", schema=None) as batch_op:
        batch_op.drop_column("descarga_ultimo_avance")
        batch_op.drop_column("descarga_recuento_precios")
        batch_op.drop_column("descarga_id")