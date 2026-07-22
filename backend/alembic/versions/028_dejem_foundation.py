"""DEJEM foundation: offer events + credits tables

Revision ID: 028_dejem_foundation
Revises: 027_god_mode_audit
Create Date: 2026-07-21

Adiciona entidades do modelo-alvo (OfferEvent, Credit) sem alterar
tabelas de produção existentes (dejem_months, dejem_interests, dejem_allocations).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "028_dejem_foundation"
down_revision: str | None = "027_god_mode_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

dejemcreditstatus = postgresql.ENUM(
    "AVAILABLE",
    "DATE_SELECTED",
    "PENDING_APPROVAL",
    "APPROVED",
    "EXECUTED",
    "CANCELLED",
    name="dejemcreditstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    dejemcreditstatus.create(bind, checkfirst=True)

    op.create_table(
        "dejem_offer_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=512), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dejem_offer_events_campaign_id", "dejem_offer_events", ["campaign_id"])
    op.create_index("ix_dejem_offer_events_created_by", "dejem_offer_events", ["created_by"])

    op.create_table(
        "dejem_credits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("allocation_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("police_officer_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            dejemcreditstatus,
            nullable=False,
            server_default="AVAILABLE",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["allocation_id"], ["dejem_allocations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["police_officer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dejem_credits_allocation_id", "dejem_credits", ["allocation_id"])
    op.create_index("ix_dejem_credits_campaign_id", "dejem_credits", ["campaign_id"])
    op.create_index("ix_dejem_credits_police_officer_id", "dejem_credits", ["police_officer_id"])
    op.create_index("ix_dejem_credits_status", "dejem_credits", ["status"])


def downgrade() -> None:
    op.drop_index("ix_dejem_credits_status", table_name="dejem_credits")
    op.drop_index("ix_dejem_credits_police_officer_id", table_name="dejem_credits")
    op.drop_index("ix_dejem_credits_campaign_id", table_name="dejem_credits")
    op.drop_index("ix_dejem_credits_allocation_id", table_name="dejem_credits")
    op.drop_table("dejem_credits")

    op.drop_index("ix_dejem_offer_events_created_by", table_name="dejem_offer_events")
    op.drop_index("ix_dejem_offer_events_campaign_id", table_name="dejem_offer_events")
    op.drop_table("dejem_offer_events")

    dejemcreditstatus.drop(op.get_bind(), checkfirst=True)
