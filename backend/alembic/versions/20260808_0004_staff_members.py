"""staff_members: доступ к просмотру броней в боте

Revision ID: 20260808_0004
Revises: 20260807_0003
Create Date: 2026-08-08

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260808_0004"
down_revision: Union[str, Sequence[str], None] = "20260807_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

staff_role = postgresql.ENUM(
    "therapist",
    "superuser",
    name="staff_role",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "staff_members" in inspector.get_table_names():
        return

    staff_role.create(bind, checkfirst=True)

    op.create_table(
        "staff_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("role", staff_role, nullable=False),
        sa.Column(
            "active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_staff_members_telegram_id"),
        "staff_members",
        ["telegram_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_staff_members_role"),
        "staff_members",
        ["role"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_staff_members_role"), table_name="staff_members")
    op.drop_index(op.f("ix_staff_members_telegram_id"), table_name="staff_members")
    op.drop_table("staff_members")
    staff_role.drop(op.get_bind(), checkfirst=True)
