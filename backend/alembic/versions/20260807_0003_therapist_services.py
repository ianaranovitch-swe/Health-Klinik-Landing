"""therapist_services: кто какую услугу оказывает

Revision ID: 20260807_0003
Revises: 20260731_0002
Create Date: 2026-08-07

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260807_0003"
down_revision: Union[str, Sequence[str], None] = "20260731_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "therapist_services" in inspector.get_table_names():
        return

    op.create_table(
        "therapist_services",
        sa.Column("therapist_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["therapist_id"],
            ["therapists.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("therapist_id", "service_id"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "therapist_services" not in inspector.get_table_names():
        return
    op.drop_table("therapist_services")
