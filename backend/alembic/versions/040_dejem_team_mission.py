"""Mission name on OperationalTeam + DejemShift (parity with Escala Operacional)

Revision ID: 040_dejem_team_mission
Revises: 039_dejem_assignment_roles
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "040_dejem_team_mission"
down_revision: str | None = "039_dejem_assignment_roles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "dejem_operational_teams",
        sa.Column("mission_name", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "dejem_shifts",
        sa.Column("mission_name", sa.String(length=256), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("dejem_shifts", "mission_name")
    op.drop_column("dejem_operational_teams", "mission_name")
