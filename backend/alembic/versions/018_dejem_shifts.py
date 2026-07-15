"""dejem shifts: type column, templates, updated_at

Revision ID: 018_dejem_shifts
Revises: 017_dejem_interest
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "018_dejem_shifts"
down_revision: str | None = "017_dejem_interest"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

dejemshifttype = postgresql.ENUM(
    "FT",
    "ROCAM",
    "OUTROS",
    name="dejemshifttype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    dejemshifttype.create(bind, checkfirst=True)

    op.add_column(
        "dejem_shifts",
        sa.Column("shift_type", dejemshifttype, nullable=False, server_default="FT"),
    )
    op.add_column(
        "dejem_shifts",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_dejem_shifts_shift_type", "dejem_shifts", ["shift_type"], unique=False)

    op.create_table(
        "dejem_shift_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("shift_type", dejemshifttype, nullable=False, server_default="FT"),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("default_capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dejem_shift_templates_shift_type", "dejem_shift_templates", ["shift_type"], unique=False)
    op.create_index("ix_dejem_shift_templates_is_active", "dejem_shift_templates", ["is_active"], unique=False)
    op.create_index("ix_dejem_shift_templates_created_by_id", "dejem_shift_templates", ["created_by_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_dejem_shift_templates_created_by_id", table_name="dejem_shift_templates")
    op.drop_index("ix_dejem_shift_templates_is_active", table_name="dejem_shift_templates")
    op.drop_index("ix_dejem_shift_templates_shift_type", table_name="dejem_shift_templates")
    op.drop_table("dejem_shift_templates")

    op.drop_index("ix_dejem_shifts_shift_type", table_name="dejem_shifts")
    op.drop_column("dejem_shifts", "updated_at")
    op.drop_column("dejem_shifts", "shift_type")

    bind = op.get_bind()
    dejemshifttype.drop(bind, checkfirst=True)
