"""Expand AssignmentRole + role on DejemParticipant; God Mode credit nullable

Revision ID: 039_dejem_assignment_roles
Revises: 038_dejem_hardening_indexes
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "039_dejem_assignment_roles"
down_revision: str | None = "038_dejem_hardening_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_ROLES = ("DRIVER", "THIRD_MAN", "FOURTH_MAN", "MOTO_2", "MOTO_3")


def upgrade() -> None:
    # PostgreSQL: ADD VALUE não pode rodar em transação em versões antigas;
    # com SQLAlchemy/Alembic moderno costuma funcionar com commit autônomo.
    for value in _NEW_ROLES:
        op.execute(
            sa.text(
                f"ALTER TYPE dejemassignmentrole ADD VALUE IF NOT EXISTS '{value}'"
            )
        )

    op.alter_column(
        "dejem_operational_assignments",
        "credit_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.add_column(
        "dejem_participants",
        sa.Column(
            "role",
            sa.Enum(
                "MEMBER",
                "COMMANDER",
                "DRIVER",
                "THIRD_MAN",
                "FOURTH_MAN",
                "MOTO_2",
                "MOTO_3",
                name="dejemassignmentrole",
                create_type=False,
            ),
            nullable=False,
            server_default="MEMBER",
        ),
    )


def downgrade() -> None:
    op.drop_column("dejem_participants", "role")
    op.alter_column(
        "dejem_operational_assignments",
        "credit_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    # Valores de ENUM PostgreSQL não são removidos com segurança no downgrade.
