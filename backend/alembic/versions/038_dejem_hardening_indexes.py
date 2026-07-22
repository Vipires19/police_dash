"""DEJEM hardening: one ACTIVE publication per campaign

Revision ID: 038_dejem_hardening_indexes
Revises: 037_dejem_publication
Create Date: 2026-07-22
"""

from collections.abc import Sequence

from alembic import op

revision: str = "038_dejem_hardening_indexes"
down_revision: str | None = "037_dejem_publication"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Garante no máximo uma publicação ACTIVE por campanha (corrida de publish).
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_dejem_published_one_active_per_campaign
        ON dejem_published_schedules (campaign_id)
        WHERE status = 'ACTIVE'
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS uq_dejem_published_one_active_per_campaign"
    )
