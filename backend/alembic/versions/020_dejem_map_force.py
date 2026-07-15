"""dejem map force integration statuses and link

Revision ID: 020_dejem_map_force
Revises: 019_dejem_enrollment
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "020_dejem_map_force"
down_revision: str | None = "019_dejem_enrollment"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TYPE dejemshiftstatus ADD VALUE IF NOT EXISTS 'INTEGRATED'"))
    op.execute(sa.text("ALTER TYPE dejemshiftstatus ADD VALUE IF NOT EXISTS 'READY_FOR_MAP'"))
    op.execute(sa.text("ALTER TYPE scalelogaction ADD VALUE IF NOT EXISTS 'UNPUBLISHED'"))
    op.execute(sa.text("ALTER TYPE scalelogaction ADD VALUE IF NOT EXISTS 'DEJEM_INTEGRATED'"))
    op.execute(sa.text("ALTER TYPE dejemenrollmentaction ADD VALUE IF NOT EXISTS 'INTEGRATED'"))
    op.execute(sa.text("ALTER TYPE dejemenrollmentaction ADD VALUE IF NOT EXISTS 'MAP_REOPENED'"))

    op.add_column(
        "dejem_shifts",
        sa.Column(
            "service_scale_id",
            sa.Integer(),
            sa.ForeignKey("service_scales.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "dejem_shifts",
        sa.Column("integrated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "dejem_shifts",
        sa.Column("integrated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_dejem_shifts_service_scale_id", "dejem_shifts", ["service_scale_id"])
    op.create_index("ix_dejem_shifts_integrated_by_id", "dejem_shifts", ["integrated_by_id"])


def downgrade() -> None:
    op.drop_index("ix_dejem_shifts_integrated_by_id", table_name="dejem_shifts")
    op.drop_index("ix_dejem_shifts_service_scale_id", table_name="dejem_shifts")
    op.drop_column("dejem_shifts", "integrated_by_id")
    op.drop_column("dejem_shifts", "integrated_at")
    op.drop_column("dejem_shifts", "service_scale_id")
