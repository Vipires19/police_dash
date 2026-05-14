"""display_label em user_compensations

Revision ID: 005_uc_label
Revises: 004_leaves
Create Date: 2026-05-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_uc_label"
down_revision: str | None = "004_leaves"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_compensations",
        sa.Column("display_label", sa.String(length=128), nullable=False, server_default=""),
    )
    op.execute(
        sa.text(
            """
            UPDATE user_compensations AS uc
            SET display_label = CASE ce.event_type::text
                WHEN 'CPJ_SUPPORT' THEN 'Horas CPJ'
                WHEN 'WEAPON_OCCURRENCE' THEN 'Ocorrência com arma'
                WHEN 'RELEVANT_OCCURRENCE' THEN 'Ocorrência de relevância'
                WHEN 'TWO_WANTED' THEN '02 Procurados'
                WHEN 'FIVE_FLAGRANTS' THEN '05 Flagrantes'
                ELSE ce.event_type::text
            END
            FROM compensation_events AS ce
            WHERE uc.compensation_event_id = ce.id
            """
        )
    )
    op.alter_column("user_compensations", "display_label", server_default=None)


def downgrade() -> None:
    op.drop_column("user_compensations", "display_label")
