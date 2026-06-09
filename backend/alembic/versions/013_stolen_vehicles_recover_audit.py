"""stolen vehicles recover audit fields and plate_group check

Revision ID: 013_stolen_recover
Revises: 012_stolen_vehicles
Create Date: 2026-06-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "013_stolen_recover"
down_revision: str | None = "012_stolen_vehicles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("stolen_vehicles", sa.Column("recovered_by_id", sa.Integer(), nullable=True))
    op.add_column("stolen_vehicles", sa.Column("recovered_notes", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_stolen_vehicles_recovered_by_id_users",
        "stolen_vehicles",
        "users",
        ["recovered_by_id"],
        ["id"],
    )
    op.create_index(
        "ix_stolen_vehicles_recovered_by_id",
        "stolen_vehicles",
        ["recovered_by_id"],
        unique=False,
    )
    op.create_check_constraint(
        "ck_stolen_vehicles_plate_group_range",
        "stolen_vehicles",
        "plate_group >= 0 AND plate_group <= 9",
    )


def downgrade() -> None:
    op.drop_constraint("ck_stolen_vehicles_plate_group_range", "stolen_vehicles", type_="check")
    op.drop_index("ix_stolen_vehicles_recovered_by_id", table_name="stolen_vehicles")
    op.drop_constraint("fk_stolen_vehicles_recovered_by_id_users", "stolen_vehicles", type_="foreignkey")
    op.drop_column("stolen_vehicles", "recovered_notes")
    op.drop_column("stolen_vehicles", "recovered_by_id")
