"""dejem multi-shift uniqueness + remove global QTR from template

Revision ID: 026_dejem_multi_shift
Revises: 025_dejem_shift_vehicle
Create Date: 2026-07-16

- Unicidade DEJEM: (month_id, date, start_time, end_time)
- Template operacional sem bloco QTR global pós-fardamento
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "026_dejem_multi_shift"
down_revision: str | None = "025_dejem_shift_vehicle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_BODY = """*💀 ESCALA DE SERVIÇO 💀*

*{{titulo}}*

*📅 {{data}}*

*👕 Fardamento*

{{fardamento}}

━━━━━━━━━━━━━━━━━━━━━━
{{equipes}}
━━━━━━━━━━━━━━━━━━━━━━
*📢 OBSERVAÇÕES*
*{{observacoes}}*
"""

_OLD_BODY = """💀 ESCALA DE SERVIÇO 💀

{{titulo}}

📅 {{data}}

👕 Fardamento

{{fardamento}}

🕘 QTR

{{qtr}}

━━━━━━━━━━━━━━━━━━━━━━
{{equipes}}
━━━━━━━━━━━━━━━━━━━━━━
{{observacoes}}
"""


def upgrade() -> None:
    # Remove duplicatas exatas (mesmo horário), preservando a escala com mais
    # participantes ativos; em empate, mantém o menor id.
    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY month_id, date, start_time, end_time
                        ORDER BY
                            (
                                SELECT COUNT(*)
                                FROM dejem_participants p
                                WHERE p.shift_id = dejem_shifts.id
                                  AND p.status <> 'CANCELLED'
                            ) DESC,
                            id ASC
                    ) AS rn
                FROM dejem_shifts
            )
            DELETE FROM dejem_shifts
            WHERE id IN (SELECT id FROM ranked WHERE rn > 1)
            """
        )
    )
    op.create_unique_constraint(
        "uq_dejem_shifts_month_date_start_end",
        "dejem_shifts",
        ["month_id", "date", "start_time", "end_time"],
    )

    op.get_bind().execute(
        sa.text(
            """
            UPDATE scale_message_templates
            SET body_text = :body, updated_at = now()
            WHERE slug = 'operational_whatsapp'
            """
        ),
        {"body": _NEW_BODY},
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_dejem_shifts_month_date_start_end",
        "dejem_shifts",
        type_="unique",
    )
    op.get_bind().execute(
        sa.text(
            """
            UPDATE scale_message_templates
            SET body_text = :body, updated_at = now()
            WHERE slug = 'operational_whatsapp'
            """
        ),
        {"body": _OLD_BODY},
    )
