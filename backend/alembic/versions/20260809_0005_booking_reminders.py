"""booking reminders: флаги отправленных напоминаний 24h / 2h

Revision ID: 20260809_0005
Revises: 20260808_0004
Create Date: 2026-08-09

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260809_0005"
down_revision: Union[str, Sequence[str], None] = "20260808_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column(
            "reminder_24h_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "bookings",
        sa.Column(
            "reminder_2h_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("bookings", "reminder_2h_sent_at")
    op.drop_column("bookings", "reminder_24h_sent_at")
