"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-05-13

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

userrole = postgresql.ENUM(
    "ADMIN",
    "N90",
    "TAT_CMD",
    "BRACAL",
    "ESTAGIO",
    name="userrole",
    create_type=False,
)

userstatus = postgresql.ENUM(
    "PENDING",
    "APPROVED",
    "REJECTED",
    name="userstatus",
    create_type=False,
)


def upgrade() -> None:
    userrole.create(op.get_bind(), checkfirst=True)
    userstatus.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("patente", sa.String(length=64), nullable=False),
        sa.Column("nome_guerra", sa.String(length=128), nullable=False),
        sa.Column("role", userrole, nullable=False),
        sa.Column("status", userstatus, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    userstatus.drop(op.get_bind(), checkfirst=True)
    userrole.drop(op.get_bind(), checkfirst=True)
