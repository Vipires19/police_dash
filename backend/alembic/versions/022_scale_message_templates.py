"""scale message templates for operational WhatsApp message

Revision ID: 022_scale_message_templates
Revises: 021_scale_publish_versions
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "022_scale_message_templates"
down_revision: str | None = "021_scale_publish_versions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DEFAULT_BODY = """💀 ESCALA DE SERVIÇO

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
    op.create_table(
        "scale_message_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_scale_message_templates_slug"),
    )
    op.create_index(
        "ix_scale_message_templates_is_default",
        "scale_message_templates",
        ["is_default"],
    )
    op.create_index(
        "ix_scale_message_templates_is_active",
        "scale_message_templates",
        ["is_active"],
    )

    op.add_column(
        "service_scales",
        sa.Column("fardamento", sa.String(length=256), nullable=True),
    )

    op.get_bind().execute(
        sa.text(
            """
            INSERT INTO scale_message_templates
                (slug, name, body_text, is_default, is_active)
            VALUES
                (
                    'operational_whatsapp',
                    'Mensagem operacional (WhatsApp)',
                    :body,
                    true,
                    true
                )
            """
        ),
        {"body": _DEFAULT_BODY},
    )


def downgrade() -> None:
    op.drop_column("service_scales", "fardamento")
    op.drop_index("ix_scale_message_templates_is_active", table_name="scale_message_templates")
    op.drop_index("ix_scale_message_templates_is_default", table_name="scale_message_templates")
    op.drop_table("scale_message_templates")
