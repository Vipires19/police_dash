"""add DS leave type

Revision ID: 010_leave_ds
Revises: 009_comp_ops
Create Date: 2026-05-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010_leave_ds"
down_revision: str | None = "009_comp_ops"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TYPE leavetype ADD VALUE IF NOT EXISTS 'DS'"))


def downgrade() -> None:
    pass
