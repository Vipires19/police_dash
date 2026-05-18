"""vacation and LP operational module

Revision ID: 006_vacations
Revises: 005_uc_label
Create Date: 2026-05-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_vacations"
down_revision: str | None = "005_uc_label"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

vacationtype = postgresql.ENUM("FERIAS", "LP", name="vacationtype", create_type=False)
vacationstatus = postgresql.ENUM(
    "PENDING",
    "REVIEW",
    "APPROVED",
    "REJECTED",
    "CANCELLED",
    name="vacationstatus",
    create_type=False,
)
vacationlogaction = postgresql.ENUM(
    "CREATED",
    "APPROVED",
    "REJECTED",
    "CANCELLED",
    "UPDATED",
    name="vacationlogaction",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    vacationtype.create(bind, checkfirst=True)
    vacationstatus.create(bind, checkfirst=True)
    vacationlogaction.create(bind, checkfirst=True)

    op.create_table(
        "vacation_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("vacation_type", vacationtype, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("total_days", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            vacationstatus,
            nullable=False,
            server_default=sa.text("'PENDING'::vacationstatus"),
        ),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vacation_requests_user_id", "vacation_requests", ["user_id"])
    op.create_index("ix_vacation_requests_start_date", "vacation_requests", ["start_date"])
    op.create_index("ix_vacation_requests_end_date", "vacation_requests", ["end_date"])

    op.create_table(
        "vacation_approval_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vacation_request_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", vacationlogaction, nullable=False),
        sa.Column("from_status", vacationstatus, nullable=True),
        sa.Column("to_status", vacationstatus, nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vacation_request_id"], ["vacation_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vacation_approval_logs_vacation_request_id",
        "vacation_approval_logs",
        ["vacation_request_id"],
    )
    op.create_index("ix_vacation_approval_logs_actor_id", "vacation_approval_logs", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_vacation_approval_logs_actor_id", table_name="vacation_approval_logs")
    op.drop_index("ix_vacation_approval_logs_vacation_request_id", table_name="vacation_approval_logs")
    op.drop_table("vacation_approval_logs")
    op.drop_index("ix_vacation_requests_end_date", table_name="vacation_requests")
    op.drop_index("ix_vacation_requests_start_date", table_name="vacation_requests")
    op.drop_index("ix_vacation_requests_user_id", table_name="vacation_requests")
    op.drop_table("vacation_requests")
    vacationlogaction.drop(op.get_bind(), checkfirst=True)
    vacationstatus.drop(op.get_bind(), checkfirst=True)
    vacationtype.drop(op.get_bind(), checkfirst=True)
