"""organizational structure: units and new roles

Revision ID: 015_org_structure
Revises: 014_criminal_watch
Create Date: 2026-07-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015_org_structure"
down_revision: str | None = "014_criminal_watch"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

organizationalunit = postgresql.ENUM(
    "FIRST_PLATOON",
    "SECOND_PLATOON",
    "COMPANY_ADMIN",
    name="organizationalunit",
    create_type=False,
)


def upgrade() -> None:
    op.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'CMD_TATICO'"))
    op.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'ADM'"))

    organizationalunit.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column(
            "organizational_unit",
            organizationalunit,
            nullable=False,
            server_default="FIRST_PLATOON",
        ),
    )
    op.execute(
        sa.text(
            "UPDATE users SET organizational_unit = 'COMPANY_ADMIN' "
            "WHERE role = 'ADMIN'"
        )
    )


def downgrade() -> None:
    op.drop_column("users", "organizational_unit")
    organizationalunit.drop(op.get_bind(), checkfirst=True)
    # PostgreSQL não remove valores de ENUM com segurança; roles CMD_TATICO/ADM permanecem.
