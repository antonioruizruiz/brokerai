"""amplía volumen de mercado a bigint

Revision ID: d7e3a9c5b1f2
Revises: c6d9e2f4a8b1
Create Date: 2026-11-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7e3a9c5b1f2"
down_revision: Union[str, Sequence[str], None] = "c6d9e2f4a8b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("price_bars", schema=None) as batch_op:
        batch_op.alter_column(
            "volume",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
    with op.batch_alter_table("index_bars", schema=None) as batch_op:
        batch_op.alter_column(
            "volume",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("index_bars", schema=None) as batch_op:
        batch_op.alter_column(
            "volume",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
    with op.batch_alter_table("price_bars", schema=None) as batch_op:
        batch_op.alter_column(
            "volume",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )