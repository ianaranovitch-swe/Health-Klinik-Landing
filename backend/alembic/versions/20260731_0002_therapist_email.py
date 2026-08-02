"""add email to therapists (idempotent if already in 0001)

Revision ID: 20260731_0002
Revises: 20260731_0001
Create Date: 2026-07-31

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0002"
down_revision: Union[str, Sequence[str], None] = "20260731_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _therapist_columns() -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col["name"] for col in inspector.get_columns("therapists")}


def upgrade() -> None:
    cols = _therapist_columns()
    if "email" in cols:
        # Уже создано в 0001 на свежей установке
        return

    op.add_column("therapists", sa.Column("email", sa.String(length=255), nullable=True))
    op.execute(
        """
        UPDATE therapists
        SET email = 'therapist_' || id::text || '@example.com'
        WHERE email IS NULL
        """
    )
    op.alter_column("therapists", "email", nullable=False)

    # unique может уже существовать — создаём только если нет
    inspector = sa.inspect(op.get_bind())
    uniques = {u["name"] for u in inspector.get_unique_constraints("therapists")}
    if "uq_therapists_email" not in uniques:
        op.create_unique_constraint("uq_therapists_email", "therapists", ["email"])


def downgrade() -> None:
    cols = _therapist_columns()
    if "email" not in cols:
        return
    inspector = sa.inspect(op.get_bind())
    uniques = {u["name"] for u in inspector.get_unique_constraints("therapists")}
    if "uq_therapists_email" in uniques:
        op.drop_constraint("uq_therapists_email", "therapists", type_="unique")
    op.drop_column("therapists", "email")
