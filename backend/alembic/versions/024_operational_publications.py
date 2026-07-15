"""operational publications domain (fase 4.10)

Revision ID: 024_operational_publications
Revises: 023_message_gen_template
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "024_operational_publications"
down_revision: str | None = "023_message_gen_template"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_status = postgresql.ENUM(
    "DRAFT",
    "READY",
    "PUBLISHED",
    "ARCHIVED",
    name="operationalpublicationstatus",
    create_type=False,
)
_audit_action = postgresql.ENUM(
    "CREATED",
    "REFRESHED",
    "VALIDATED",
    "PUBLISHED",
    "REPUBLISHED",
    "ARCHIVED",
    "RISK_ACK",
    name="operationalpublicationauditaction",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        "CREATE TYPE operationalpublicationstatus AS ENUM "
        "('DRAFT', 'READY', 'PUBLISHED', 'ARCHIVED')"
    )
    op.execute(
        "CREATE TYPE operationalpublicationauditaction AS ENUM "
        "('CREATED', 'REFRESHED', 'VALIDATED', 'PUBLISHED', 'REPUBLISHED', 'ARCHIVED', 'RISK_ACK')"
    )

    op.create_table(
        "operational_publications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_scale_id", sa.Integer(), sa.ForeignKey("service_scales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scale_date", sa.Date(), nullable=False),
        sa.Column("publication_number", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", _status, nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("published_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generated_message", sa.Text(), nullable=True),
        sa.Column("generated_pdf", sa.Text(), nullable=True),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("checklist_json", sa.Text(), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("publish_reason", sa.String(length=512), nullable=True),
        sa.Column("risk_acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("previous_publication_id", sa.Integer(), sa.ForeignKey("operational_publications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_scale_id", "version", name="uq_operational_publications_scale_version"),
    )
    op.create_index("ix_operational_publications_service_scale_id", "operational_publications", ["service_scale_id"])
    op.create_index("ix_operational_publications_scale_date", "operational_publications", ["scale_date"])
    op.create_index("ix_operational_publications_publication_number", "operational_publications", ["publication_number"])
    op.create_index("ix_operational_publications_status", "operational_publications", ["status"])
    op.create_index("ix_operational_publications_created_by_id", "operational_publications", ["created_by_id"])
    op.create_index("ix_operational_publications_published_by_id", "operational_publications", ["published_by_id"])
    op.create_index("ix_operational_publications_previous_publication_id", "operational_publications", ["previous_publication_id"])

    op.create_table(
        "operational_publication_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("publication_id", sa.Integer(), sa.ForeignKey("operational_publications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", _audit_action, nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operational_publication_audits_publication_id", "operational_publication_audits", ["publication_id"])
    op.create_index("ix_operational_publication_audits_action", "operational_publication_audits", ["action"])
    op.create_index("ix_operational_publication_audits_actor_id", "operational_publication_audits", ["actor_id"])


def downgrade() -> None:
    op.drop_table("operational_publication_audits")
    op.drop_table("operational_publications")
    op.execute("DROP TYPE IF EXISTS operationalpublicationauditaction")
    op.execute("DROP TYPE IF EXISTS operationalpublicationstatus")
