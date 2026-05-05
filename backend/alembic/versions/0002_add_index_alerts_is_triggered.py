"""add_index_alerts_is_triggered

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-05 12:05:22.489341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_alerts_is_triggered", "alerts", ["is_triggered"])


def downgrade() -> None:
    op.drop_index("ix_alerts_is_triggered", table_name="alerts")
