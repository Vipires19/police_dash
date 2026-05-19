"""expand vacation module to operational absences

Revision ID: 011_absences
Revises: 010_leave_ds
Create Date: 2026-05-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "011_absences"
down_revision: str | None = "010_leave_ds"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TYPE vacationtype ADD VALUE IF NOT EXISTS 'LTS'"))
    op.execute(sa.text("ALTER TYPE vacationtype ADD VALUE IF NOT EXISTS 'CURSO'"))
    op.execute(sa.text("ALTER TYPE vacationtype ADD VALUE IF NOT EXISTS 'ESTAGIO_OPERACIONAL'"))
    op.execute(sa.text("ALTER TYPE vacationtype ADD VALUE IF NOT EXISTS 'OUTROS'"))
    op.execute(sa.text("ALTER TYPE vacationstatus ADD VALUE IF NOT EXISTS 'REVERTED'"))
    op.execute(sa.text("ALTER TYPE vacationlogaction ADD VALUE IF NOT EXISTS 'REVERTED'"))
    op.add_column("vacation_requests", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("vacation_requests", "notes")
