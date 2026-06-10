"""criminal watch vehicles C05 module

Revision ID: 014_criminal_watch
Revises: 013_stolen_recover
Create Date: 2026-06-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "014_criminal_watch"
down_revision: str | None = "013_stolen_recover"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vehicle_qru_codes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("description", sa.String(length=256), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_vehicle_qru_codes_code", "vehicle_qru_codes", ["code"], unique=True)
    op.create_index("ix_vehicle_qru_codes_is_active", "vehicle_qru_codes", ["is_active"], unique=False)
    op.create_index("ix_vehicle_qru_codes_created_by_id", "vehicle_qru_codes", ["created_by_id"], unique=False)

    op.create_table(
        "criminal_watch_vehicles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("plate", sa.String(length=16), nullable=False),
        sa.Column("vehicle_model", sa.String(length=128), nullable=False),
        sa.Column("color", sa.String(length=64), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("qru_code_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["qru_code_id"], ["vehicle_qru_codes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_criminal_watch_vehicles_plate", "criminal_watch_vehicles", ["plate"], unique=False)
    op.create_index(
        "ix_criminal_watch_vehicles_vehicle_model", "criminal_watch_vehicles", ["vehicle_model"], unique=False
    )
    op.create_index("ix_criminal_watch_vehicles_color", "criminal_watch_vehicles", ["color"], unique=False)
    op.create_index("ix_criminal_watch_vehicles_qru_code_id", "criminal_watch_vehicles", ["qru_code_id"], unique=False)
    op.create_index("ix_criminal_watch_vehicles_created_at", "criminal_watch_vehicles", ["created_at"], unique=False)
    op.create_index(
        "ix_criminal_watch_vehicles_created_by_id", "criminal_watch_vehicles", ["created_by_id"], unique=False
    )

    op.create_table(
        "criminal_watch_notes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["criminal_watch_vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_criminal_watch_notes_vehicle_id", "criminal_watch_notes", ["vehicle_id"], unique=False)
    op.create_index("ix_criminal_watch_notes_created_at", "criminal_watch_notes", ["created_at"], unique=False)
    op.create_index("ix_criminal_watch_notes_created_by_id", "criminal_watch_notes", ["created_by_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_criminal_watch_notes_created_by_id", table_name="criminal_watch_notes")
    op.drop_index("ix_criminal_watch_notes_created_at", table_name="criminal_watch_notes")
    op.drop_index("ix_criminal_watch_notes_vehicle_id", table_name="criminal_watch_notes")
    op.drop_table("criminal_watch_notes")

    op.drop_index("ix_criminal_watch_vehicles_created_by_id", table_name="criminal_watch_vehicles")
    op.drop_index("ix_criminal_watch_vehicles_created_at", table_name="criminal_watch_vehicles")
    op.drop_index("ix_criminal_watch_vehicles_qru_code_id", table_name="criminal_watch_vehicles")
    op.drop_index("ix_criminal_watch_vehicles_color", table_name="criminal_watch_vehicles")
    op.drop_index("ix_criminal_watch_vehicles_vehicle_model", table_name="criminal_watch_vehicles")
    op.drop_index("ix_criminal_watch_vehicles_plate", table_name="criminal_watch_vehicles")
    op.drop_table("criminal_watch_vehicles")

    op.drop_index("ix_vehicle_qru_codes_created_by_id", table_name="vehicle_qru_codes")
    op.drop_index("ix_vehicle_qru_codes_is_active", table_name="vehicle_qru_codes")
    op.drop_index("ix_vehicle_qru_codes_code", table_name="vehicle_qru_codes")
    op.drop_table("vehicle_qru_codes")
