"""DEJEM campaign lifecycle: CREATED status + status audits

Revision ID: 029_dejem_campaign_lifecycle
Revises: 028_dejem_foundation
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "029_dejem_campaign_lifecycle"
down_revision: str | None = "028_dejem_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TYPE dejemmonthstatus ADD VALUE IF NOT EXISTS 'CREATED'"))

    op.create_table(
        "dejem_campaign_status_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=64), nullable=True),
        sa.Column("to_status", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["dejem_months.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dejem_campaign_status_audits_campaign_id",
        "dejem_campaign_status_audits",
        ["campaign_id"],
    )
    op.create_index(
        "ix_dejem_campaign_status_audits_actor_id",
        "dejem_campaign_status_audits",
        ["actor_id"],
    )
    op.create_index(
        "ix_dejem_campaign_status_audits_to_status",
        "dejem_campaign_status_audits",
        ["to_status"],
    )
    op.create_index(
        "ix_dejem_campaign_status_audits_created_at",
        "dejem_campaign_status_audits",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dejem_campaign_status_audits_created_at",
        table_name="dejem_campaign_status_audits",
    )
    op.drop_index(
        "ix_dejem_campaign_status_audits_to_status",
        table_name="dejem_campaign_status_audits",
    )
    op.drop_index(
        "ix_dejem_campaign_status_audits_actor_id",
        table_name="dejem_campaign_status_audits",
    )
    op.drop_index(
        "ix_dejem_campaign_status_audits_campaign_id",
        table_name="dejem_campaign_status_audits",
    )
    op.drop_table("dejem_campaign_status_audits")
    # PostgreSQL não remove valores de ENUM com segurança.
