"""stolen vehicles operational module

Revision ID: 012_stolen_vehicles
Revises: 011_absences
Create Date: 2026-06-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_stolen_vehicles"
down_revision: str | None = "011_absences"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

stolenvehicletype = postgresql.ENUM("CARRO", "MOTO", name="stolenvehicletype", create_type=False)
stolenoccurrencetype = postgresql.ENUM("FURTO", "ROUBO", name="stolenoccurrencetype", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    stolenvehicletype.create(bind, checkfirst=True)
    stolenoccurrencetype.create(bind, checkfirst=True)

    op.create_table(
        "stolen_vehicles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vehicle_type", stolenvehicletype, nullable=False),
        sa.Column("plate", sa.String(length=16), nullable=False),
        sa.Column("vehicle_model", sa.String(length=128), nullable=False),
        sa.Column("color", sa.String(length=64), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("occurrence_type", stolenoccurrencetype, nullable=False),
        sa.Column("plate_group", sa.Integer(), nullable=False),
        sa.Column("observation", sa.Text(), nullable=True),
        sa.Column("is_recovered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("recovered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stolen_vehicles_vehicle_type", "stolen_vehicles", ["vehicle_type"], unique=False)
    op.create_index("ix_stolen_vehicles_plate", "stolen_vehicles", ["plate"], unique=False)
    op.create_index("ix_stolen_vehicles_plate_group", "stolen_vehicles", ["plate_group"], unique=False)
    op.create_index("ix_stolen_vehicles_is_recovered", "stolen_vehicles", ["is_recovered"], unique=False)
    op.create_index("ix_stolen_vehicles_created_at", "stolen_vehicles", ["created_at"], unique=False)
    op.create_index("ix_stolen_vehicles_created_by_id", "stolen_vehicles", ["created_by_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_stolen_vehicles_created_by_id", table_name="stolen_vehicles")
    op.drop_index("ix_stolen_vehicles_created_at", table_name="stolen_vehicles")
    op.drop_index("ix_stolen_vehicles_is_recovered", table_name="stolen_vehicles")
    op.drop_index("ix_stolen_vehicles_plate_group", table_name="stolen_vehicles")
    op.drop_index("ix_stolen_vehicles_plate", table_name="stolen_vehicles")
    op.drop_index("ix_stolen_vehicles_vehicle_type", table_name="stolen_vehicles")
    op.drop_table("stolen_vehicles")
    bind = op.get_bind()
    stolenoccurrencetype.drop(bind, checkfirst=True)
    stolenvehicletype.drop(bind, checkfirst=True)
