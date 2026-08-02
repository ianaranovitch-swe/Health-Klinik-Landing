"""Генерация слотов доступности."""

from __future__ import annotations

from datetime import date, datetime, timedelta, time


WORKDAY_START = time(9, 0)
WORKDAY_END = time(17, 0)
SLOT_STEP = timedelta(minutes=90)


def generate_time_slots() -> list[str]:
    """Рабочие часы 09:00–17:00, шаг 1.5 часа (пока без проверки занятых)."""
    day = date(2000, 1, 1)  # только для арифметики времени
    current = datetime.combine(day, WORKDAY_START)
    end = datetime.combine(day, WORKDAY_END)
    slots: list[str] = []
    while current <= end:
        slots.append(current.strftime("%H:%M"))
        current += SLOT_STEP
    return slots
