"""dejem module foundation tables

Revision ID: 016_dejem
Revises: 015_org_structure
Create Date: 2026-07-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016_dejem"
down_revision: str | None = "015_org_structure"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

dejemmonthstatus = postgresql.ENUM(
    "OPEN_INTEREST",
    "DISTRIBUTED_PENDING",
    "DISTRIBUTED",
    "OPEN_SHIFTS",
    "FINISHED",
    name="dejemmonthstatus",
    create_type=False,
)
dejemshiftstatus = postgresql.ENUM(
    "OPEN",
    "CLOSED",
    "FINISHED",
    name="dejemshiftstatus",
    create_type=False,
)
participationtype = postgresql.ENUM(
    "NORMAL",
    "EXTRAORDINARY",
    "SUBSTITUTION",
    name="participationtype",
    create_type=False,
)
participantstatus = postgresql.ENUM(
    "REGISTERED",
    "CONFIRMED",
    "CANCELLED",
    name="participantstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    dejemmonthstatus.create(bind, checkfirst=True)
    dejemshiftstatus.create(bind, checkfirst=True)
    participationtype.create(bind, checkfirst=True)
    participantstatus.create(bind, checkfirst=True)

    op.create_table(
        "dejem_months",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("total_available_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monthly_limit_per_officer", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", dejemmonthstatus, nullable=False, server_default="OPEN_INTEREST"),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "month", name="uq_dejem_months_year_month"),
    )
    op.create_index("ix_dejem_months_year", "dejem_months", ["year"], unique=False)
    op.create_index("ix_dejem_months_month", "dejem_months", ["month"], unique=False)
    op.create_index("ix_dejem_months_status", "dejem_months", ["status"], unique=False)
    op.create_index("ix_dejem_months_created_by_id", "dejem_months", ["created_by_id"], unique=False)

    op.create_table(
        "dejem_interests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("month_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("interested", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("desired_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["month_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("month_id", "user_id", name="uq_dejem_interests_month_user"),
    )
    op.create_index("ix_dejem_interests_month_id", "dejem_interests", ["month_id"], unique=False)
    op.create_index("ix_dejem_interests_user_id", "dejem_interests", ["user_id"], unique=False)

    op.create_table(
        "dejem_allocations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("month_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("allocated_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remaining_slots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["month_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("month_id", "user_id", name="uq_dejem_allocations_month_user"),
    )
    op.create_index("ix_dejem_allocations_month_id", "dejem_allocations", ["month_id"], unique=False)
    op.create_index("ix_dejem_allocations_user_id", "dejem_allocations", ["user_id"], unique=False)

    op.create_table(
        "dejem_shifts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("month_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", dejemshiftstatus, nullable=False, server_default="OPEN"),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["month_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dejem_shifts_month_id", "dejem_shifts", ["month_id"], unique=False)
    op.create_index("ix_dejem_shifts_date", "dejem_shifts", ["date"], unique=False)
    op.create_index("ix_dejem_shifts_status", "dejem_shifts", ["status"], unique=False)
    op.create_index("ix_dejem_shifts_created_by_id", "dejem_shifts", ["created_by_id"], unique=False)

    op.create_table(
        "dejem_participants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("shift_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("participation_type", participationtype, nullable=False, server_default="NORMAL"),
        sa.Column("status", participantstatus, nullable=False, server_default="REGISTERED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shift_id"], ["dejem_shifts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shift_id", "user_id", name="uq_dejem_participants_shift_user"),
    )
    op.create_index("ix_dejem_participants_shift_id", "dejem_participants", ["shift_id"], unique=False)
    op.create_index("ix_dejem_participants_user_id", "dejem_participants", ["user_id"], unique=False)
    op.create_index("ix_dejem_participants_status", "dejem_participants", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_dejem_participants_status", table_name="dejem_participants")
    op.drop_index("ix_dejem_participants_user_id", table_name="dejem_participants")
    op.drop_index("ix_dejem_participants_shift_id", table_name="dejem_participants")
    op.drop_table("dejem_participants")

    op.drop_index("ix_dejem_shifts_created_by_id", table_name="dejem_shifts")
    op.drop_index("ix_dejem_shifts_status", table_name="dejem_shifts")
    op.drop_index("ix_dejem_shifts_date", table_name="dejem_shifts")
    op.drop_index("ix_dejem_shifts_month_id", table_name="dejem_shifts")
    op.drop_table("dejem_shifts")

    op.drop_index("ix_dejem_allocations_user_id", table_name="dejem_allocations")
    op.drop_index("ix_dejem_allocations_month_id", table_name="dejem_allocations")
    op.drop_table("dejem_allocations")

    op.drop_index("ix_dejem_interests_user_id", table_name="dejem_interests")
    op.drop_index("ix_dejem_interests_month_id", table_name="dejem_interests")
    op.drop_table("dejem_interests")

    op.drop_index("ix_dejem_months_created_by_id", table_name="dejem_months")
    op.drop_index("ix_dejem_months_status", table_name="dejem_months")
    op.drop_index("ix_dejem_months_month", table_name="dejem_months")
    op.drop_index("ix_dejem_months_year", table_name="dejem_months")
    op.drop_table("dejem_months")

    bind = op.get_bind()
    participantstatus.drop(bind, checkfirst=True)
    participationtype.drop(bind, checkfirst=True)
    dejemshiftstatus.drop(bind, checkfirst=True)
    dejemmonthstatus.drop(bind, checkfirst=True)
