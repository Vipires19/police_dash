"""DEJEM incremental engine: offer_excess_slots

Revision ID: 033_dejem_incremental_allocation
Revises: 032_dejem_allocation_engine
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "033_dejem_incremental_allocation"
down_revision: str | None = "032_dejem_allocation_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "dejem_months",
        sa.Column(
            "offer_excess_slots",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("dejem_months", "offer_excess_slots")
