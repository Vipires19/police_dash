"""leaves and compensation operational module

Revision ID: 004_leaves
Revises: 003_vehicles
Create Date: 2026-05-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_leaves"
down_revision: str | None = "003_vehicles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

leavetype = postgresql.ENUM("MONTHLY", "COMPENSATION", name="leavetype", create_type=False)
leavestatus = postgresql.ENUM(
    "PENDING",
    "REVIEW",
    "APPROVED",
    "REJECTED",
    "CANCELLED",
    name="leavestatus",
    create_type=False,
)
leavelogaction = postgresql.ENUM(
    "CREATED",
    "APPROVED",
    "REJECTED",
    "CANCELLED",
    "UPDATED",
    name="leavelogaction",
    create_type=False,
)
compensationtype = postgresql.ENUM(
    "CPJ_SUPPORT",
    "WEAPON_OCCURRENCE",
    "RELEVANT_OCCURRENCE",
    "TWO_WANTED",
    "FIVE_FLAGRANTS",
    name="compensationtype",
    create_type=False,
)
compensationstatus = postgresql.ENUM(
    "PENDING",
    "APPROVED",
    "REJECTED",
    name="compensationstatus",
    create_type=False,
)
usercompensationstatus = postgresql.ENUM(
    "AVAILABLE",
    "USED",
    name="usercompensationstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    leavetype.create(bind, checkfirst=True)
    leavestatus.create(bind, checkfirst=True)
    leavelogaction.create(bind, checkfirst=True)
    compensationtype.create(bind, checkfirst=True)
    compensationstatus.create(bind, checkfirst=True)
    usercompensationstatus.create(bind, checkfirst=True)

    op.create_table(
        "compensation_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_type", compensationtype, nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("status", compensationstatus, nullable=False, server_default=sa.text("'PENDING'::compensationstatus")),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("decided_by_id", sa.Integer(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_motivo", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_compensation_events_created_by_id", "compensation_events", ["created_by_id"], unique=False)
    op.create_index("ix_compensation_events_status", "compensation_events", ["status"], unique=False)

    op.create_table(
        "compensation_event_participants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("compensation_event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["compensation_event_id"], ["compensation_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("compensation_event_id", "user_id", name="uq_comp_event_user"),
    )
    op.create_index(
        "ix_compensation_event_participants_event_id",
        "compensation_event_participants",
        ["compensation_event_id"],
        unique=False,
    )
    op.create_index(
        "ix_compensation_event_participants_user_id",
        "compensation_event_participants",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "user_compensations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("compensation_event_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            usercompensationstatus,
            nullable=False,
            server_default=sa.text("'AVAILABLE'::usercompensationstatus"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["compensation_event_id"], ["compensation_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_compensations_user_id", "user_compensations", ["user_id"], unique=False)
    op.create_index("ix_user_compensations_event_id", "user_compensations", ["compensation_event_id"], unique=False)

    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("leave_on", sa.Date(), nullable=False),
        sa.Column("leave_type", leavetype, nullable=False),
        sa.Column("user_compensation_id", sa.Integer(), nullable=True),
        sa.Column("status", leavestatus, nullable=False, server_default=sa.text("'PENDING'::leavestatus")),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("decision_motivo", sa.Text(), nullable=True),
        sa.Column("decided_by_id", sa.Integer(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_compensation_id"], ["user_compensations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leave_requests_user_id", "leave_requests", ["user_id"], unique=False)
    op.create_index("ix_leave_requests_leave_on", "leave_requests", ["leave_on"], unique=False)
    op.create_index("ix_leave_requests_user_compensation_id", "leave_requests", ["user_compensation_id"], unique=False)

    op.create_table(
        "leave_approval_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("leave_request_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", leavelogaction, nullable=False),
        sa.Column("from_status", leavestatus, nullable=True),
        sa.Column("to_status", leavestatus, nullable=True),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["leave_request_id"], ["leave_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leave_approval_logs_leave_request_id", "leave_approval_logs", ["leave_request_id"], unique=False)
    op.create_index("ix_leave_approval_logs_actor_id", "leave_approval_logs", ["actor_id"], unique=False)

    op.add_column("user_compensations", sa.Column("used_leave_request_id", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_user_compensations_used_leave", "user_compensations", ["used_leave_request_id"])
    op.create_foreign_key(
        "fk_user_compensations_used_leave_request",
        "user_compensations",
        "leave_requests",
        ["used_leave_request_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_user_compensations_used_leave_request", "user_compensations", type_="foreignkey")
    op.drop_constraint("uq_user_compensations_used_leave", "user_compensations", type_="unique")
    op.drop_column("user_compensations", "used_leave_request_id")

    op.drop_index("ix_leave_approval_logs_actor_id", table_name="leave_approval_logs")
    op.drop_index("ix_leave_approval_logs_leave_request_id", table_name="leave_approval_logs")
    op.drop_table("leave_approval_logs")

    op.drop_index("ix_leave_requests_user_compensation_id", table_name="leave_requests")
    op.drop_index("ix_leave_requests_leave_on", table_name="leave_requests")
    op.drop_index("ix_leave_requests_user_id", table_name="leave_requests")
    op.drop_table("leave_requests")

    op.drop_index("ix_user_compensations_event_id", table_name="user_compensations")
    op.drop_index("ix_user_compensations_user_id", table_name="user_compensations")
    op.drop_table("user_compensations")

    op.drop_index("ix_compensation_event_participants_user_id", table_name="compensation_event_participants")
    op.drop_index("ix_compensation_event_participants_event_id", table_name="compensation_event_participants")
    op.drop_table("compensation_event_participants")

    op.drop_index("ix_compensation_events_status", table_name="compensation_events")
    op.drop_index("ix_compensation_events_created_by_id", table_name="compensation_events")
    op.drop_table("compensation_events")

    bind = op.get_bind()
    usercompensationstatus.drop(bind, checkfirst=True)
    compensationstatus.drop(bind, checkfirst=True)
    compensationtype.drop(bind, checkfirst=True)
    leavelogaction.drop(bind, checkfirst=True)
    leavestatus.drop(bind, checkfirst=True)
    leavetype.drop(bind, checkfirst=True)
