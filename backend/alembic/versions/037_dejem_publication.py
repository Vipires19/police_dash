"""DEJEM publication: PublishedSchedule + audits

Revision ID: 037_dejem_publication
Revises: 036_dejem_operational_planning
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "037_dejem_publication"
down_revision: str | None = "036_dejem_operational_planning"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

dejempublishedschedulestatus = postgresql.ENUM(
    "ACTIVE",
    "SUPERSEDED",
    name="dejempublishedschedulestatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    dejempublishedschedulestatus.create(bind, checkfirst=True)

    op.create_table(
        "dejem_published_schedules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("published_by", sa.Integer(), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            dejempublishedschedulestatus,
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("notes", sa.String(length=512), nullable=True),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("mapa_payload_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("previous_publication_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["campaign_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["previous_publication_id"],
            ["dejem_published_schedules.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "campaign_id",
            "version",
            name="uq_dejem_published_campaign_version",
        ),
    )
    op.create_index(
        "ix_dejem_published_schedules_campaign_id",
        "dejem_published_schedules",
        ["campaign_id"],
    )
    op.create_index(
        "ix_dejem_published_schedules_published_by",
        "dejem_published_schedules",
        ["published_by"],
    )
    op.create_index(
        "ix_dejem_published_schedules_published_at",
        "dejem_published_schedules",
        ["published_at"],
    )
    op.create_index(
        "ix_dejem_published_schedules_status",
        "dejem_published_schedules",
        ["status"],
    )
    op.create_index(
        "ix_dejem_published_schedules_previous_publication_id",
        "dejem_published_schedules",
        ["previous_publication_id"],
    )

    op.create_table(
        "dejem_published_schedule_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("publication_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=512), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["publication_id"],
            ["dejem_published_schedules.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dejem_published_schedule_audits_publication_id",
        "dejem_published_schedule_audits",
        ["publication_id"],
    )
    op.create_index(
        "ix_dejem_published_schedule_audits_campaign_id",
        "dejem_published_schedule_audits",
        ["campaign_id"],
    )
    op.create_index(
        "ix_dejem_published_schedule_audits_actor_id",
        "dejem_published_schedule_audits",
        ["actor_id"],
    )
    op.create_index(
        "ix_dejem_published_schedule_audits_action",
        "dejem_published_schedule_audits",
        ["action"],
    )
    op.create_index(
        "ix_dejem_published_schedule_audits_created_at",
        "dejem_published_schedule_audits",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dejem_published_schedule_audits_created_at",
        table_name="dejem_published_schedule_audits",
    )
    op.drop_index(
        "ix_dejem_published_schedule_audits_action",
        table_name="dejem_published_schedule_audits",
    )
    op.drop_index(
        "ix_dejem_published_schedule_audits_actor_id",
        table_name="dejem_published_schedule_audits",
    )
    op.drop_index(
        "ix_dejem_published_schedule_audits_campaign_id",
        table_name="dejem_published_schedule_audits",
    )
    op.drop_index(
        "ix_dejem_published_schedule_audits_publication_id",
        table_name="dejem_published_schedule_audits",
    )
    op.drop_table("dejem_published_schedule_audits")

    op.drop_index(
        "ix_dejem_published_schedules_previous_publication_id",
        table_name="dejem_published_schedules",
    )
    op.drop_index(
        "ix_dejem_published_schedules_status",
        table_name="dejem_published_schedules",
    )
    op.drop_index(
        "ix_dejem_published_schedules_published_at",
        table_name="dejem_published_schedules",
    )
    op.drop_index(
        "ix_dejem_published_schedules_published_by",
        table_name="dejem_published_schedules",
    )
    op.drop_index(
        "ix_dejem_published_schedules_campaign_id",
        table_name="dejem_published_schedules",
    )
    op.drop_table("dejem_published_schedules")

    dejempublishedschedulestatus.drop(op.get_bind(), checkfirst=True)
