"""add DISTRIBUTED_PENDING to dejem month status

Revision ID: 017_dejem_interest
Revises: 016_dejem
Create Date: 2026-07-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "017_dejem_interest"
down_revision: str | None = "016_dejem"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TYPE dejemmonthstatus ADD VALUE IF NOT EXISTS 'DISTRIBUTED_PENDING'"))


def downgrade() -> None:
    # PostgreSQL não remove valores de ENUM com segurança.
    pass
