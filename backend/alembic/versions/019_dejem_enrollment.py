"""dejem enrollment: audit fields and enrollment audits

Revision ID: 019_dejem_enrollment
Revises: 018_dejem_shifts
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "019_dejem_enrollment"
down_revision: str | None = "018_dejem_shifts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

dejemenrollmentaction = postgresql.ENUM(
    "ENROLLED",
    "CANCELLED",
    "ADMIN_ADDED",
    "ADMIN_REMOVED",
    "CLOSED",
    name="dejemenrollmentaction",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    dejemenrollmentaction.create(bind, checkfirst=True)

    op.add_column(
        "dejem_participants",
        sa.Column("enrolled_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.add_column(
        "dejem_participants",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "dejem_participants",
        sa.Column("cancelled_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.add_column(
        "dejem_participants",
        sa.Column(
            "consumes_balance",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "dejem_participants",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_dejem_participants_enrolled_by_id",
        "dejem_participants",
        ["enrolled_by_id"],
    )

    op.add_column(
        "dejem_shifts",
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "dejem_shifts",
        sa.Column("closed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )

    op.create_table(
        "dejem_enrollment_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action", dejemenrollmentaction, nullable=False),
        sa.Column(
            "shift_id",
            sa.Integer(),
            sa.ForeignKey("dejem_shifts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_id",
            sa.Integer(),
            sa.ForeignKey("dejem_participants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("subject_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("details", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dejem_enrollment_audits_shift_id",
        "dejem_enrollment_audits",
        ["shift_id"],
    )
    op.create_index(
        "ix_dejem_enrollment_audits_actor_id",
        "dejem_enrollment_audits",
        ["actor_id"],
    )
    op.create_index(
        "ix_dejem_enrollment_audits_created_at",
        "dejem_enrollment_audits",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_dejem_enrollment_audits_created_at", table_name="dejem_enrollment_audits")
    op.drop_index("ix_dejem_enrollment_audits_actor_id", table_name="dejem_enrollment_audits")
    op.drop_index("ix_dejem_enrollment_audits_shift_id", table_name="dejem_enrollment_audits")
    op.drop_table("dejem_enrollment_audits")

    op.drop_column("dejem_shifts", "closed_by_id")
    op.drop_column("dejem_shifts", "closed_at")

    op.drop_index("ix_dejem_participants_enrolled_by_id", table_name="dejem_participants")
    op.drop_column("dejem_participants", "updated_at")
    op.drop_column("dejem_participants", "consumes_balance")
    op.drop_column("dejem_participants", "cancelled_by_id")
    op.drop_column("dejem_participants", "cancelled_at")
    op.drop_column("dejem_participants", "enrolled_by_id")

    bind = op.get_bind()
    dejemenrollmentaction.drop(bind, checkfirst=True)
