"""DEJEM date selection: ShiftSlot + credit reservation

Revision ID: 035_dejem_date_selection
Revises: 034_dejem_credit_lifecycle
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "035_dejem_date_selection"
down_revision: str | None = "034_dejem_credit_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

dejemshiftslotstatus = postgresql.ENUM(
    "OPEN",
    "FULL",
    "CLOSED",
    name="dejemshiftslotstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    dejemshiftslotstatus.create(bind, checkfirst=True)

    op.create_table(
        "dejem_shift_slots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("total_slots", sa.Integer(), nullable=False),
        sa.Column("reserved_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remaining_slots", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            dejemshiftslotstatus,
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dejem_shift_slots_campaign_id", "dejem_shift_slots", ["campaign_id"])
    op.create_index("ix_dejem_shift_slots_date", "dejem_shift_slots", ["date"])
    op.create_index("ix_dejem_shift_slots_status", "dejem_shift_slots", ["status"])

    op.add_column(
        "dejem_credits",
        sa.Column("shift_slot_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_dejem_credits_shift_slot_id",
        "dejem_credits",
        "dejem_shift_slots",
        ["shift_slot_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_dejem_credits_shift_slot_id",
        "dejem_credits",
        ["shift_slot_id"],
    )

    op.create_table(
        "dejem_credit_reservation_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("credit_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("from_shift_slot_id", sa.Integer(), nullable=True),
        sa.Column("to_shift_slot_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=512), nullable=True),
        sa.Column("origin", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["credit_id"], ["dejem_credits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["from_shift_slot_id"],
            ["dejem_shift_slots.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["to_shift_slot_id"],
            ["dejem_shift_slots.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dejem_credit_reservation_audits_credit_id",
        "dejem_credit_reservation_audits",
        ["credit_id"],
    )
    op.create_index(
        "ix_dejem_credit_reservation_audits_campaign_id",
        "dejem_credit_reservation_audits",
        ["campaign_id"],
    )
    op.create_index(
        "ix_dejem_credit_reservation_audits_actor_id",
        "dejem_credit_reservation_audits",
        ["actor_id"],
    )
    op.create_index(
        "ix_dejem_credit_reservation_audits_from_shift_slot_id",
        "dejem_credit_reservation_audits",
        ["from_shift_slot_id"],
    )
    op.create_index(
        "ix_dejem_credit_reservation_audits_to_shift_slot_id",
        "dejem_credit_reservation_audits",
        ["to_shift_slot_id"],
    )
    op.create_index(
        "ix_dejem_credit_reservation_audits_action",
        "dejem_credit_reservation_audits",
        ["action"],
    )
    op.create_index(
        "ix_dejem_credit_reservation_audits_origin",
        "dejem_credit_reservation_audits",
        ["origin"],
    )
    op.create_index(
        "ix_dejem_credit_reservation_audits_created_at",
        "dejem_credit_reservation_audits",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dejem_credit_reservation_audits_created_at",
        table_name="dejem_credit_reservation_audits",
    )
    op.drop_index(
        "ix_dejem_credit_reservation_audits_origin",
        table_name="dejem_credit_reservation_audits",
    )
    op.drop_index(
        "ix_dejem_credit_reservation_audits_action",
        table_name="dejem_credit_reservation_audits",
    )
    op.drop_index(
        "ix_dejem_credit_reservation_audits_to_shift_slot_id",
        table_name="dejem_credit_reservation_audits",
    )
    op.drop_index(
        "ix_dejem_credit_reservation_audits_from_shift_slot_id",
        table_name="dejem_credit_reservation_audits",
    )
    op.drop_index(
        "ix_dejem_credit_reservation_audits_actor_id",
        table_name="dejem_credit_reservation_audits",
    )
    op.drop_index(
        "ix_dejem_credit_reservation_audits_campaign_id",
        table_name="dejem_credit_reservation_audits",
    )
    op.drop_index(
        "ix_dejem_credit_reservation_audits_credit_id",
        table_name="dejem_credit_reservation_audits",
    )
    op.drop_table("dejem_credit_reservation_audits")

    op.drop_index("ix_dejem_credits_shift_slot_id", table_name="dejem_credits")
    op.drop_constraint("fk_dejem_credits_shift_slot_id", "dejem_credits", type_="foreignkey")
    op.drop_column("dejem_credits", "shift_slot_id")

    op.drop_index("ix_dejem_shift_slots_status", table_name="dejem_shift_slots")
    op.drop_index("ix_dejem_shift_slots_date", table_name="dejem_shift_slots")
    op.drop_index("ix_dejem_shift_slots_campaign_id", table_name="dejem_shift_slots")
    op.drop_table("dejem_shift_slots")

    dejemshiftslotstatus.drop(op.get_bind(), checkfirst=True)
