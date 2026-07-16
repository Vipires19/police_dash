"""God Mode audit fields: actor/target/origin + created_by/updated_by

Revision ID: 027_god_mode_audit
Revises: 026_dejem_multi_shift
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "027_god_mode_audit"
down_revision: str | None = "026_dejem_multi_shift"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

auditorigin = sa.Enum("SELF", "ADMIN", "SYSTEM", name="auditorigin")


def upgrade() -> None:
    auditorigin.create(op.get_bind(), checkfirst=True)

    op.add_column("leave_requests", sa.Column("created_by_id", sa.Integer(), nullable=True))
    op.add_column("leave_requests", sa.Column("updated_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_leave_requests_created_by_id_users",
        "leave_requests",
        "users",
        ["created_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_leave_requests_updated_by_id_users",
        "leave_requests",
        "users",
        ["updated_by_id"],
        ["id"],
    )
    op.create_index("ix_leave_requests_created_by_id", "leave_requests", ["created_by_id"])
    op.create_index("ix_leave_requests_updated_by_id", "leave_requests", ["updated_by_id"])
    op.execute(sa.text("UPDATE leave_requests SET created_by_id = user_id WHERE created_by_id IS NULL"))

    op.add_column("leave_approval_logs", sa.Column("subject_user_id", sa.Integer(), nullable=True))
    op.add_column(
        "leave_approval_logs",
        sa.Column("origin", auditorigin, nullable=False, server_default="SELF"),
    )
    op.create_foreign_key(
        "fk_leave_approval_logs_subject_user_id_users",
        "leave_approval_logs",
        "users",
        ["subject_user_id"],
        ["id"],
    )
    op.create_index("ix_leave_approval_logs_subject_user_id", "leave_approval_logs", ["subject_user_id"])
    op.execute(
        sa.text(
            """
            UPDATE leave_approval_logs AS l
            SET subject_user_id = r.user_id
            FROM leave_requests AS r
            WHERE l.leave_request_id = r.id AND l.subject_user_id IS NULL
            """
        )
    )

    op.add_column("vacation_requests", sa.Column("created_by_id", sa.Integer(), nullable=True))
    op.add_column("vacation_requests", sa.Column("updated_by_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_vacation_requests_created_by_id_users",
        "vacation_requests",
        "users",
        ["created_by_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_vacation_requests_updated_by_id_users",
        "vacation_requests",
        "users",
        ["updated_by_id"],
        ["id"],
    )
    op.create_index("ix_vacation_requests_created_by_id", "vacation_requests", ["created_by_id"])
    op.create_index("ix_vacation_requests_updated_by_id", "vacation_requests", ["updated_by_id"])
    op.execute(sa.text("UPDATE vacation_requests SET created_by_id = user_id WHERE created_by_id IS NULL"))

    op.add_column("vacation_approval_logs", sa.Column("subject_user_id", sa.Integer(), nullable=True))
    op.add_column(
        "vacation_approval_logs",
        sa.Column("origin", auditorigin, nullable=False, server_default="SELF"),
    )
    op.create_foreign_key(
        "fk_vacation_approval_logs_subject_user_id_users",
        "vacation_approval_logs",
        "users",
        ["subject_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_vacation_approval_logs_subject_user_id",
        "vacation_approval_logs",
        ["subject_user_id"],
    )
    op.execute(
        sa.text(
            """
            UPDATE vacation_approval_logs AS l
            SET subject_user_id = r.user_id
            FROM vacation_requests AS r
            WHERE l.vacation_request_id = r.id AND l.subject_user_id IS NULL
            """
        )
    )

    op.add_column("compensation_event_logs", sa.Column("subject_user_id", sa.Integer(), nullable=True))
    op.add_column(
        "compensation_event_logs",
        sa.Column("origin", auditorigin, nullable=False, server_default="SELF"),
    )
    op.create_foreign_key(
        "fk_compensation_event_logs_subject_user_id_users",
        "compensation_event_logs",
        "users",
        ["subject_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_compensation_event_logs_subject_user_id",
        "compensation_event_logs",
        ["subject_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_compensation_event_logs_subject_user_id", table_name="compensation_event_logs")
    op.drop_constraint(
        "fk_compensation_event_logs_subject_user_id_users",
        "compensation_event_logs",
        type_="foreignkey",
    )
    op.drop_column("compensation_event_logs", "origin")
    op.drop_column("compensation_event_logs", "subject_user_id")

    op.drop_index("ix_vacation_approval_logs_subject_user_id", table_name="vacation_approval_logs")
    op.drop_constraint(
        "fk_vacation_approval_logs_subject_user_id_users",
        "vacation_approval_logs",
        type_="foreignkey",
    )
    op.drop_column("vacation_approval_logs", "origin")
    op.drop_column("vacation_approval_logs", "subject_user_id")

    op.drop_index("ix_vacation_requests_updated_by_id", table_name="vacation_requests")
    op.drop_index("ix_vacation_requests_created_by_id", table_name="vacation_requests")
    op.drop_constraint("fk_vacation_requests_updated_by_id_users", "vacation_requests", type_="foreignkey")
    op.drop_constraint("fk_vacation_requests_created_by_id_users", "vacation_requests", type_="foreignkey")
    op.drop_column("vacation_requests", "updated_by_id")
    op.drop_column("vacation_requests", "created_by_id")

    op.drop_index("ix_leave_approval_logs_subject_user_id", table_name="leave_approval_logs")
    op.drop_constraint(
        "fk_leave_approval_logs_subject_user_id_users",
        "leave_approval_logs",
        type_="foreignkey",
    )
    op.drop_column("leave_approval_logs", "origin")
    op.drop_column("leave_approval_logs", "subject_user_id")

    op.drop_index("ix_leave_requests_updated_by_id", table_name="leave_requests")
    op.drop_index("ix_leave_requests_created_by_id", table_name="leave_requests")
    op.drop_constraint("fk_leave_requests_updated_by_id_users", "leave_requests", type_="foreignkey")
    op.drop_constraint("fk_leave_requests_created_by_id_users", "leave_requests", type_="foreignkey")
    op.drop_column("leave_requests", "updated_by_id")
    op.drop_column("leave_requests", "created_by_id")

    auditorigin.drop(op.get_bind(), checkfirst=True)
