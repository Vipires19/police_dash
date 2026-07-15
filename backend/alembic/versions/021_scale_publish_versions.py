"""service scale publication versions (intelligent publish pipeline)

Revision ID: 021_scale_publish_versions
Revises: 020_dejem_map_force
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "021_scale_publish_versions"
down_revision: str | None = "020_dejem_map_force"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TYPE scalelogaction ADD VALUE IF NOT EXISTS 'VERSION_CREATED'"))

    op.create_table(
        "service_scale_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "service_scale_id",
            sa.Integer(),
            sa.ForeignKey("service_scales.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("export_text", sa.Text(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("dejem_integrated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "service_scale_id",
            "version_number",
            name="uq_service_scale_versions_scale_version",
        ),
    )
    op.create_index(
        "ix_service_scale_versions_service_scale_id",
        "service_scale_versions",
        ["service_scale_id"],
    )
    op.create_index(
        "ix_service_scale_versions_published_by_id",
        "service_scale_versions",
        ["published_by_id"],
    )

    op.add_column(
        "service_scales",
        sa.Column(
            "current_version_id",
            sa.Integer(),
            sa.ForeignKey("service_scale_versions.id", ondelete="SET NULL", use_alter=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_service_scales_current_version_id",
        "service_scales",
        ["current_version_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_service_scales_current_version_id", table_name="service_scales")
    op.drop_column("service_scales", "current_version_id")
    op.drop_index("ix_service_scale_versions_published_by_id", table_name="service_scale_versions")
    op.drop_index("ix_service_scale_versions_service_scale_id", table_name="service_scale_versions")
    op.drop_table("service_scale_versions")
