"""Тесты guidad Telegram-bokning (без БД / Telegram)."""

from __future__ import annotations

from datetime import date

from app.services.availability import (
    DEFAULT_BOOKING_DAYS_AHEAD,
    generate_time_slots,
    list_open_booking_dates,
)
from app.services.client_email import is_synthetic_client_email
from bot.client_booking.flow import format_summary, is_valid_email, is_valid_name, normalize_phone
from bot.client_booking.keyboards import BookingCb, times_keyboard


def test_synthetic_email_hidden_from_summary() -> None:
    data = {
        "name": "Anna",
        "service_name": "EIS",
        "therapist_name": "Viktoria",
        "date": "2026-08-15",
        "time": "14:00",
        "phone": "+46701234567",
        "email": "tg_42@noemail.mrboka.local",
    }
    summary = format_summary(data)
    assert "E-post:" not in summary
    assert is_synthetic_client_email(data["email"])


def test_real_email_shown_in_summary() -> None:
    data = {
        "name": "Anna",
        "service_name": "EIS",
        "therapist_name": "Viktoria",
        "date": "2026-08-15",
        "time": "14:00",
        "phone": "+46701234567",
        "email": "anna@example.com",
    }
    summary = format_summary(data)
    assert "E-post: anna@example.com" in summary


def test_list_open_booking_dates_skips_weekends() -> None:
    # Понедельник 2026-08-10
    start = date(2026, 8, 10)
    days = list_open_booking_dates(from_date=start, days_ahead=7)
    assert len(days) == 5  # пн–пт
    assert all(generate_time_slots(d) for d in days)
    assert all(d.weekday() < 5 for d in days)


def test_list_open_booking_days_ahead_default() -> None:
    days = list_open_booking_dates(from_date=date(2026, 8, 10))
    # 28 календарных дней → 20 рабочих (4 полные недели)
    assert len(days) == 20
    assert len(days) <= DEFAULT_BOOKING_DAYS_AHEAD


def test_phone_validation() -> None:
    assert normalize_phone("0701234567") == "+46701234567"
    assert normalize_phone("+46 70 123 45 67") == "+46701234567"
    assert normalize_phone("08123456") is None


def test_name_and_email_validation() -> None:
    assert is_valid_name("Anna")
    assert not is_valid_name("A")
    assert is_valid_email("anna@test.se")
    assert not is_valid_email("not-an-email")


def test_times_keyboard_packs_without_colon() -> None:
    """aiogram CallbackData запрещает «:» в value — слоты кодируем как 11-00."""
    slots = generate_time_slots(date(2026, 8, 14))  # пятница
    assert slots
    kb = times_keyboard(slots)
    flat = [btn for row in kb.inline_keyboard for btn in row]
    assert len(flat) == len(slots)
    for btn, slot in zip(flat, slots, strict=True):
        assert btn.text == slot
        unpacked = BookingCb.unpack(btn.callback_data)
        assert unpacked.step == "time"
        assert ":" not in unpacked.value
        assert unpacked.value.replace("-", ":") == slot
