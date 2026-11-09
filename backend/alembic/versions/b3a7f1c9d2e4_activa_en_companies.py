"""activa en companies

Revision ID: b3a7f1c9d2e4
Revises: 8f3c2a9d1e07
Create Date: 2026-11-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3a7f1c9d2e4'
down_revision: Union[str, Sequence[str], None] = '8f3c2a9d1e07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('activa', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.drop_column('activa')
