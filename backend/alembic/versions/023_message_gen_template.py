"""Update default operational message template (fase 4.9)

Revision ID: 023_message_gen_template
Revises: 022_scale_message_templates
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "023_message_gen_template"
down_revision: str | None = "022_scale_message_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_BODY = """💀 ESCALA DE SERVIÇO 💀

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

_OLD_BODY = """💀 ESCALA DE SERVIÇO

{{titulo}}

📅 {{data}}
📆 {{dia_semana}}

👕 {{fardamento}}

🕘 QTR {{qtr}}

━━━━━━━━━━━━━━━━━━
{{equipes}}
━━━━━━━━━━━━━━━━━━
{{observacoes}}
"""


def upgrade() -> None:
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
