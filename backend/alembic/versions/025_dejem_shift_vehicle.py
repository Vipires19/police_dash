"""dejem shifts vehicle link

Revision ID: 025_dejem_shift_vehicle
Revises: 024_operational_publications
Create Date: 2026-07-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "025_dejem_shift_vehicle"
down_revision: str | None = "024_operational_publications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "dejem_shifts",
        sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id"), nullable=True),
    )
    op.create_index("ix_dejem_shifts_vehicle_id", "dejem_shifts", ["vehicle_id"])


def downgrade() -> None:
    op.drop_index("ix_dejem_shifts_vehicle_id", table_name="dejem_shifts")
    op.drop_column("dejem_shifts", "vehicle_id")
