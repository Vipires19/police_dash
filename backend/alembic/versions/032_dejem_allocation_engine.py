"""DEJEM allocation engine: undistributed_slots on campaign

Revision ID: 032_dejem_allocation_engine
Revises: 031_dejem_allocation_domain
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "032_dejem_allocation_engine"
down_revision: str | None = "031_dejem_allocation_domain"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "dejem_months",
        sa.Column(
            "undistributed_slots",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("dejem_months", "undistributed_slots")
