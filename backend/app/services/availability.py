"""Генерация слотов доступности."""

from __future__ import annotations

from datetime import date, datetime, timedelta, time

# Пн–чт: 11:00–18:00; пт: 11:00–17:00; сб–вс: закрыто
WEEKDAY_START = time(11, 0)
WEEKDAY_END = time(18, 0)
FRIDAY_END = time(17, 0)
SLOT_STEP = timedelta(minutes=30)


def generate_time_slots(on_date: date) -> list[str]:
    """
    Стартовые времена записи на выбранный день.
    Выходные — пустой список. Шаг 30 минут, последний слот = конец окна.
    """
    weekday = on_date.weekday()  # 0=пн … 6=вс
    if weekday >= 5:
        return []

    end = FRIDAY_END if weekday == 4 else WEEKDAY_END
    day = date(2000, 1, 1)  # только для арифметики времени
    current = datetime.combine(day, WEEKDAY_START)
    end_dt = datetime.combine(day, end)
    slots: list[str] = []
    while current <= end_dt:
        slots.append(current.strftime("%H:%M"))
        current += SLOT_STEP
    return slots
