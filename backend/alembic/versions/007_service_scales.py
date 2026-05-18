"""service scales operational module

Revision ID: 007_service_scales
Revises: 006_vacations
Create Date: 2026-05-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_service_scales"
down_revision: str | None = "006_vacations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

scalestatus = postgresql.ENUM("DRAFT", "PUBLISHED", name="scalestatus", create_type=False)
scalemodality = postgresql.ENUM("FT", "ROCAM", name="scalemodality", create_type=False)
scalelogaction = postgresql.ENUM(
    "CREATED",
    "UPDATED",
    "PUBLISHED",
    "TEAM_ADDED",
    "TEAM_UPDATED",
    "TEAM_REMOVED",
    "MEMBERS_CHANGED",
    "DELETED",
    name="scalelogaction",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    scalestatus.create(bind, checkfirst=True)
    scalemodality.create(bind, checkfirst=True)
    scalelogaction.create(bind, checkfirst=True)

    op.create_table(
        "service_scales",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scale_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            scalestatus,
            nullable=False,
            server_default=sa.text("'DRAFT'::scalestatus"),
        ),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scale_date"),
    )
    op.create_index("ix_service_scales_scale_date", "service_scales", ["scale_date"])
    op.create_index("ix_service_scales_created_by_id", "service_scales", ["created_by_id"])

    op.create_table(
        "scale_teams",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_scale_id", sa.Integer(), nullable=False),
        sa.Column("modality", scalemodality, nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=True),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mission_name", sa.String(length=256), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["service_scale_id"], ["service_scales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scale_teams_service_scale_id", "scale_teams", ["service_scale_id"])
    op.create_index("ix_scale_teams_vehicle_id", "scale_teams", ["vehicle_id"])

    op.create_table(
        "scale_team_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scale_team_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("assigned_vehicle_id", sa.Integer(), nullable=True),
        sa.Column("role_label", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assigned_vehicle_id"], ["vehicles.id"]),
        sa.ForeignKeyConstraint(["scale_team_id"], ["scale_teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scale_team_members_scale_team_id", "scale_team_members", ["scale_team_id"])
    op.create_index("ix_scale_team_members_user_id", "scale_team_members", ["user_id"])

    op.create_table(
        "scale_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_scale_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action_type", scalelogaction, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["service_scale_id"], ["service_scales.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scale_logs_service_scale_id", "scale_logs", ["service_scale_id"])
    op.create_index("ix_scale_logs_actor_id", "scale_logs", ["actor_id"])


def downgrade() -> None:
    op.drop_table("scale_logs")
    op.drop_table("scale_team_members")
    op.drop_table("scale_teams")
    op.drop_table("service_scales")
    bind = op.get_bind()
    scalelogaction.drop(bind, checkfirst=True)
    scalemodality.drop(bind, checkfirst=True)
    scalestatus.drop(bind, checkfirst=True)
