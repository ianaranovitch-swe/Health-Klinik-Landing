"""initial schema: therapists, clients, services, bookings

Revision ID: 20260731_0001
Revises:
Create Date: 2026-07-31

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

booking_status = postgresql.ENUM(
    "pending",
    "confirmed",
    "cancelled",
    "completed",
    name="booking_status",
    create_type=False,
)


def upgrade() -> None:
    booking_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "therapists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("specialization", sa.String(length=300), nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
        sa.UniqueConstraint("email", name="uq_therapists_email"),
    )
    op.create_index("ix_therapists_telegram_id", "therapists", ["telegram_id"])

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_clients_telegram_id", "clients", ["telegram_id"])

    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("therapist_id", sa.Integer(), nullable=False),
        sa.Column("service_name", sa.String(length=200), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column(
            "status",
            booking_status,
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "telegram_confirm_token",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["therapist_id"], ["therapists.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_confirm_token"),
    )
    op.create_index("ix_bookings_client_id", "bookings", ["client_id"])
    op.create_index("ix_bookings_therapist_id", "bookings", ["therapist_id"])
    op.create_index("ix_bookings_date", "bookings", ["date"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index(
        "ix_bookings_telegram_confirm_token",
        "bookings",
        ["telegram_confirm_token"],
    )


def downgrade() -> None:
    op.drop_index("ix_bookings_telegram_confirm_token", table_name="bookings")
    op.drop_index("ix_bookings_status", table_name="bookings")
    op.drop_index("ix_bookings_date", table_name="bookings")
    op.drop_index("ix_bookings_therapist_id", table_name="bookings")
    op.drop_index("ix_bookings_client_id", table_name="bookings")
    op.drop_table("bookings")

    op.drop_table("services")

    op.drop_index("ix_clients_telegram_id", table_name="clients")
    op.drop_table("clients")

    op.drop_index("ix_therapists_telegram_id", table_name="therapists")
    op.drop_table("therapists")

    booking_status.drop(op.get_bind(), checkfirst=True)
