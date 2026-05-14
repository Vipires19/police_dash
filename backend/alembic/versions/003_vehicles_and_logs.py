"""vehicles and operational logs

Revision ID: 003_vehicles
Revises: 002_profile
Create Date: 2026-05-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_vehicles"
down_revision: str | None = "002_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

vehiclemodalidade = postgresql.ENUM("FT", "ROCAM", name="vehiclemodalidade", create_type=False)

vehiclestatus = postgresql.ENUM(
    "OPERANDO",
    "BAIXADA",
    "MANUTENCAO",
    "RESERVA",
    name="vehiclestatus",
    create_type=False,
)

vehicleactiontype = postgresql.ENUM(
    "CREATED",
    "STATUS_CHANGED",
    "RETURNED",
    "UPDATED",
    name="vehicleactiontype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    vehiclemodalidade.create(bind, checkfirst=True)
    vehiclestatus.create(bind, checkfirst=True)
    vehicleactiontype.create(bind, checkfirst=True)

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("placa", sa.String(length=16), nullable=False),
        sa.Column("prefixo", sa.String(length=32), nullable=False),
        sa.Column("modelo", sa.String(length=128), nullable=False),
        sa.Column("modalidade", vehiclemodalidade, nullable=False),
        sa.Column("status", vehiclestatus, nullable=False, server_default=sa.text("'OPERANDO'::vehiclestatus")),
        sa.Column("baixada_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retorno_operacao_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("placa"),
        sa.UniqueConstraint("prefixo"),
    )

    op.create_table(
        "vehicle_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action_type", vehicleactiontype, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("old_status", vehiclestatus, nullable=True),
        sa.Column("new_status", vehiclestatus, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicle_logs_vehicle_id", "vehicle_logs", ["vehicle_id"], unique=False)
    op.create_index("ix_vehicle_logs_created_at", "vehicle_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_vehicle_logs_created_at", table_name="vehicle_logs")
    op.drop_index("ix_vehicle_logs_vehicle_id", table_name="vehicle_logs")
    op.drop_table("vehicle_logs")
    op.drop_table("vehicles")
    bind = op.get_bind()
    vehicleactiontype.drop(bind, checkfirst=True)
    vehiclestatus.drop(bind, checkfirst=True)
    vehiclemodalidade.drop(bind, checkfirst=True)
