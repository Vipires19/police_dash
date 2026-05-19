"""compensations operational types, statuses and audit logs

Revision ID: 009_comp_ops
Revises: 008_vehicle_obs
Create Date: 2026-05-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_comp_ops"
down_revision: str | None = "008_vehicle_obs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

compensationlogaction = postgresql.ENUM(
    "CREATED",
    "APPROVED",
    "REJECTED",
    "UPDATED",
    "CANCELLED",
    "REVERTED",
    name="compensationlogaction",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    compensationlogaction.create(bind, checkfirst=True)

    for value in ("FOLGA_MENSAL", "COMPENSACAO", "DS"):
        op.execute(sa.text(f"ALTER TYPE compensationtype ADD VALUE IF NOT EXISTS '{value}'"))

    for value in ("CANCELLED", "REVERTED"):
        op.execute(sa.text(f"ALTER TYPE compensationstatus ADD VALUE IF NOT EXISTS '{value}'"))

    op.execute(sa.text("ALTER TYPE usercompensationstatus ADD VALUE IF NOT EXISTS 'REVOKED'"))

    op.create_table(
        "compensation_event_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("compensation_event_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", compensationlogaction, nullable=False),
        sa.Column("from_status", postgresql.ENUM(name="compensationstatus", create_type=False), nullable=True),
        sa.Column("to_status", postgresql.ENUM(name="compensationstatus", create_type=False), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["compensation_event_id"],
            ["compensation_events.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_compensation_event_logs_event_id",
        "compensation_event_logs",
        ["compensation_event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_compensation_event_logs_event_id", table_name="compensation_event_logs")
    op.drop_table("compensation_event_logs")
    bind = op.get_bind()
    compensationlogaction.drop(bind, checkfirst=True)
