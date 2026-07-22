"""DEJEM allocation domain infra: offer type + audits

Revision ID: 031_dejem_allocation_domain
Revises: 030_dejem_interest_updated_at
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "031_dejem_allocation_domain"
down_revision: str | None = "030_dejem_interest_updated_at"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

dejemoffereventtype = postgresql.ENUM(
    "INCREASE",
    "DECREASE",
    "ADJUSTMENT",
    name="dejemoffereventtype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    dejemoffereventtype.create(bind, checkfirst=True)

    op.add_column(
        "dejem_offer_events",
        sa.Column(
            "event_type",
            dejemoffereventtype,
            nullable=False,
            server_default="ADJUSTMENT",
        ),
    )
    op.create_index(
        "ix_dejem_offer_events_event_type",
        "dejem_offer_events",
        ["event_type"],
    )

    op.create_table(
        "dejem_credit_status_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("credit_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=64), nullable=True),
        sa.Column("to_status", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["credit_id"], ["dejem_credits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dejem_credit_status_audits_credit_id",
        "dejem_credit_status_audits",
        ["credit_id"],
    )
    op.create_index(
        "ix_dejem_credit_status_audits_campaign_id",
        "dejem_credit_status_audits",
        ["campaign_id"],
    )
    op.create_index(
        "ix_dejem_credit_status_audits_actor_id",
        "dejem_credit_status_audits",
        ["actor_id"],
    )
    op.create_index(
        "ix_dejem_credit_status_audits_to_status",
        "dejem_credit_status_audits",
        ["to_status"],
    )
    op.create_index(
        "ix_dejem_credit_status_audits_created_at",
        "dejem_credit_status_audits",
        ["created_at"],
    )

    op.create_table(
        "dejem_allocation_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("allocation_id", sa.Integer(), nullable=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["allocation_id"],
            ["dejem_allocations.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dejem_allocation_audits_allocation_id",
        "dejem_allocation_audits",
        ["allocation_id"],
    )
    op.create_index(
        "ix_dejem_allocation_audits_campaign_id",
        "dejem_allocation_audits",
        ["campaign_id"],
    )
    op.create_index(
        "ix_dejem_allocation_audits_actor_id",
        "dejem_allocation_audits",
        ["actor_id"],
    )
    op.create_index(
        "ix_dejem_allocation_audits_action",
        "dejem_allocation_audits",
        ["action"],
    )
    op.create_index(
        "ix_dejem_allocation_audits_created_at",
        "dejem_allocation_audits",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_dejem_allocation_audits_created_at", table_name="dejem_allocation_audits")
    op.drop_index("ix_dejem_allocation_audits_action", table_name="dejem_allocation_audits")
    op.drop_index("ix_dejem_allocation_audits_actor_id", table_name="dejem_allocation_audits")
    op.drop_index("ix_dejem_allocation_audits_campaign_id", table_name="dejem_allocation_audits")
    op.drop_index("ix_dejem_allocation_audits_allocation_id", table_name="dejem_allocation_audits")
    op.drop_table("dejem_allocation_audits")

    op.drop_index(
        "ix_dejem_credit_status_audits_created_at",
        table_name="dejem_credit_status_audits",
    )
    op.drop_index(
        "ix_dejem_credit_status_audits_to_status",
        table_name="dejem_credit_status_audits",
    )
    op.drop_index(
        "ix_dejem_credit_status_audits_actor_id",
        table_name="dejem_credit_status_audits",
    )
    op.drop_index(
        "ix_dejem_credit_status_audits_campaign_id",
        table_name="dejem_credit_status_audits",
    )
    op.drop_index(
        "ix_dejem_credit_status_audits_credit_id",
        table_name="dejem_credit_status_audits",
    )
    op.drop_table("dejem_credit_status_audits")

    op.drop_index("ix_dejem_offer_events_event_type", table_name="dejem_offer_events")
    op.drop_column("dejem_offer_events", "event_type")
    dejemoffereventtype.drop(op.get_bind(), checkfirst=True)
