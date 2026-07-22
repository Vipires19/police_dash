"""DEJEM operational planning: teams + assignments

Revision ID: 036_dejem_operational_planning
Revises: 035_dejem_date_selection
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "036_dejem_operational_planning"
down_revision: str | None = "035_dejem_date_selection"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

dejemteamtype = postgresql.ENUM(
    "FT",
    "ROCAM",
    "APOIO",
    "ADMINISTRATIVO",
    name="dejemteamtype",
    create_type=False,
)
dejemteamstatus = postgresql.ENUM(
    "DRAFT",
    "READY",
    name="dejemteamstatus",
    create_type=False,
)
dejemassignmentrole = postgresql.ENUM(
    "MEMBER",
    "COMMANDER",
    name="dejemassignmentrole",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    dejemteamtype.create(bind, checkfirst=True)
    dejemteamstatus.create(bind, checkfirst=True)
    dejemassignmentrole.create(bind, checkfirst=True)

    op.create_table(
        "dejem_operational_teams",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("shift_slot_id", sa.Integer(), nullable=False),
        sa.Column("team_type", dejemteamtype, nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=True),
        sa.Column("commander_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            dejemteamstatus,
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("max_members", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["shift_slot_id"],
            ["dejem_shift_slots.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["commander_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "shift_slot_id",
            "vehicle_id",
            name="uq_dejem_op_team_slot_vehicle",
        ),
    )
    op.create_index(
        "ix_dejem_operational_teams_campaign_id",
        "dejem_operational_teams",
        ["campaign_id"],
    )
    op.create_index(
        "ix_dejem_operational_teams_shift_slot_id",
        "dejem_operational_teams",
        ["shift_slot_id"],
    )
    op.create_index(
        "ix_dejem_operational_teams_team_type",
        "dejem_operational_teams",
        ["team_type"],
    )
    op.create_index(
        "ix_dejem_operational_teams_vehicle_id",
        "dejem_operational_teams",
        ["vehicle_id"],
    )
    op.create_index(
        "ix_dejem_operational_teams_commander_id",
        "dejem_operational_teams",
        ["commander_id"],
    )
    op.create_index(
        "ix_dejem_operational_teams_status",
        "dejem_operational_teams",
        ["status"],
    )

    op.create_table(
        "dejem_operational_assignments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("operational_team_id", sa.Integer(), nullable=False),
        sa.Column("credit_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            dejemassignmentrole,
            nullable=False,
            server_default="MEMBER",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["operational_team_id"],
            ["dejem_operational_teams.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["credit_id"], ["dejem_credits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("credit_id", name="uq_dejem_op_assignment_credit"),
        sa.UniqueConstraint(
            "operational_team_id",
            "user_id",
            name="uq_dejem_op_assignment_team_user",
        ),
    )
    op.create_index(
        "ix_dejem_operational_assignments_operational_team_id",
        "dejem_operational_assignments",
        ["operational_team_id"],
    )
    op.create_index(
        "ix_dejem_operational_assignments_credit_id",
        "dejem_operational_assignments",
        ["credit_id"],
    )
    op.create_index(
        "ix_dejem_operational_assignments_user_id",
        "dejem_operational_assignments",
        ["user_id"],
    )

    op.create_table(
        "dejem_operational_team_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("credit_id", sa.Integer(), nullable=True),
        sa.Column("vehicle_id", sa.Integer(), nullable=True),
        sa.Column("commander_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["dejem_operational_teams.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["credit_id"], ["dejem_credits.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["commander_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dejem_operational_team_audits_team_id",
        "dejem_operational_team_audits",
        ["team_id"],
    )
    op.create_index(
        "ix_dejem_operational_team_audits_campaign_id",
        "dejem_operational_team_audits",
        ["campaign_id"],
    )
    op.create_index(
        "ix_dejem_operational_team_audits_actor_id",
        "dejem_operational_team_audits",
        ["actor_id"],
    )
    op.create_index(
        "ix_dejem_operational_team_audits_action",
        "dejem_operational_team_audits",
        ["action"],
    )
    op.create_index(
        "ix_dejem_operational_team_audits_created_at",
        "dejem_operational_team_audits",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dejem_operational_team_audits_created_at",
        table_name="dejem_operational_team_audits",
    )
    op.drop_index(
        "ix_dejem_operational_team_audits_action",
        table_name="dejem_operational_team_audits",
    )
    op.drop_index(
        "ix_dejem_operational_team_audits_actor_id",
        table_name="dejem_operational_team_audits",
    )
    op.drop_index(
        "ix_dejem_operational_team_audits_campaign_id",
        table_name="dejem_operational_team_audits",
    )
    op.drop_index(
        "ix_dejem_operational_team_audits_team_id",
        table_name="dejem_operational_team_audits",
    )
    op.drop_table("dejem_operational_team_audits")

    op.drop_index(
        "ix_dejem_operational_assignments_user_id",
        table_name="dejem_operational_assignments",
    )
    op.drop_index(
        "ix_dejem_operational_assignments_credit_id",
        table_name="dejem_operational_assignments",
    )
    op.drop_index(
        "ix_dejem_operational_assignments_operational_team_id",
        table_name="dejem_operational_assignments",
    )
    op.drop_table("dejem_operational_assignments")

    op.drop_index(
        "ix_dejem_operational_teams_status",
        table_name="dejem_operational_teams",
    )
    op.drop_index(
        "ix_dejem_operational_teams_commander_id",
        table_name="dejem_operational_teams",
    )
    op.drop_index(
        "ix_dejem_operational_teams_vehicle_id",
        table_name="dejem_operational_teams",
    )
    op.drop_index(
        "ix_dejem_operational_teams_team_type",
        table_name="dejem_operational_teams",
    )
    op.drop_index(
        "ix_dejem_operational_teams_shift_slot_id",
        table_name="dejem_operational_teams",
    )
    op.drop_index(
        "ix_dejem_operational_teams_campaign_id",
        table_name="dejem_operational_teams",
    )
    op.drop_table("dejem_operational_teams")

    dejemassignmentrole.drop(op.get_bind(), checkfirst=True)
    dejemteamstatus.drop(op.get_bind(), checkfirst=True)
    dejemteamtype.drop(op.get_bind(), checkfirst=True)
