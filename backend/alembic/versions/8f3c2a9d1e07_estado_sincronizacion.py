"""estado de sincronizacion de precios

Revision ID: 8f3c2a9d1e07
Revises: 4ba29ba378f1
Create Date: 2026-11-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f3c2a9d1e07'
down_revision: Union[str, Sequence[str], None] = '4ba29ba378f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'sync_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('descarga_completa_en_progreso', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('ultima_descarga_completa', sa.DateTime(), nullable=True),
        sa.Column('ultima_actualizacion_horaria', sa.DateTime(), nullable=True),
        sa.Column('ultimo_error', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sync_status')
