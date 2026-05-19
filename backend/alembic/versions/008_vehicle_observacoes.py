"""vehicle observacoes operacionais

Revision ID: 008_vehicle_obs
Revises: 007_service_scales
Create Date: 2026-05-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_vehicle_obs"
down_revision: str | None = "007_service_scales"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("vehicles", sa.Column("observacoes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("vehicles", "observacoes")
