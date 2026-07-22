"""DEJEM interest: add updated_at for manifestation edits

Revision ID: 030_dejem_interest_updated_at
Revises: 029_dejem_campaign_lifecycle
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "030_dejem_interest_updated_at"
down_revision: str | None = "029_dejem_campaign_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "dejem_interests",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("dejem_interests", "updated_at")
