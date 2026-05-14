"""user profile and efetivo ordering

Revision ID: 002_profile
Revises: 001_initial
Create Date: 2026-05-13

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_profile"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("re", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("address", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("blood_type", sa.String(length=8), nullable=True))
    op.add_column(
        "users",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_users_re", "users", ["re"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_re", table_name="users")
    op.drop_column("users", "is_active")
    op.drop_column("users", "display_order")
    op.drop_column("users", "blood_type")
    op.drop_column("users", "birth_date")
    op.drop_column("users", "phone")
    op.drop_column("users", "address")
    op.drop_column("users", "re")
    op.drop_column("users", "full_name")
