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


def list_active_staff_telegram_ids(db: Session) -> list[int]:
    """Все активные staff (Viktoria, Iwona, Boris, Jan) — получатели напоминаний."""
    rows = db.scalars(
        select(StaffMember.telegram_id).where(StaffMember.active.is_(True))
    ).all()
    return [int(tg) for tg in rows if tg and int(tg) > 0]
