"""Доступ staff к боту: поиск по telegram_id."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.staff import StaffMember


def get_active_staff_by_telegram_id(
    db: Session,
    telegram_id: int,
) -> StaffMember | None:
    """Вернуть активного сотрудника или None (гость / клиент)."""
    return db.scalar(
        select(StaffMember).where(
            StaffMember.telegram_id == telegram_id,
            StaffMember.active.is_(True),
        )
    )
