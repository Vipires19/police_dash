"""DEJEM credit lifecycle: audit reason + origin

Revision ID: 034_dejem_credit_lifecycle
Revises: 033_dejem_incremental_allocation
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "034_dejem_credit_lifecycle"
down_revision: str | None = "033_dejem_incremental_allocation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "dejem_credit_status_audits",
        sa.Column("reason", sa.String(length=512), nullable=True),
    )
    op.add_column(
        "dejem_credit_status_audits",
        sa.Column("origin", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_dejem_credit_status_audits_origin",
        "dejem_credit_status_audits",
        ["origin"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dejem_credit_status_audits_origin",
        table_name="dejem_credit_status_audits",
    )
    op.drop_column("dejem_credit_status_audits", "origin")
    op.drop_column("dejem_credit_status_audits", "reason")
