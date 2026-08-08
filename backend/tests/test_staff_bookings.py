"""Юнит-тесты для staff-броней (без БД)."""

from __future__ import annotations

from datetime import date, datetime, time
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.models.booking import BookingStatus
from app.services.staff_bookings import (
    format_booking_card,
    is_current_or_future_slot,
    mailto_url,
    status_label_sv,
    telegram_user_url,
)

_TZ = ZoneInfo("Europe/Stockholm")


def test_is_current_or_future_slot_today_future() -> None:
    now = datetime(2026, 8, 8, 10, 0, tzinfo=_TZ)
    assert is_current_or_future_slot(date(2026, 8, 8), time(11, 0), now=now)


def test_is_current_or_future_slot_today_past() -> None:
    now = datetime(2026, 8, 8, 12, 0, tzinfo=_TZ)
    assert not is_current_or_future_slot(date(2026, 8, 8), time(11, 0), now=now)


def test_is_current_or_future_slot_tomorrow() -> None:
    now = datetime(2026, 8, 8, 23, 0, tzinfo=_TZ)
    assert is_current_or_future_slot(date(2026, 8, 9), time(9, 0), now=now)


def test_format_booking_card_shows_therapist_and_client() -> None:
    booking = SimpleNamespace(
        booking_date=date(2026, 8, 10),
        booking_time=time(11, 30),
        status=BookingStatus.confirmed,
        service_name="Alfa skanning",
        client=SimpleNamespace(
            name="Anna Test",
            phone="+46700000000",
            email="anna@example.com",
        ),
        therapist=SimpleNamespace(name="Viktoria Antropova"),
    )
    text = format_booking_card(booking, index=1, total=2)  # type: ignore[arg-type]
    assert "Anna Test" in text
    assert "Viktoria Antropova" in text
    assert "Alfa skanning" in text
    assert "11:30" in text
    assert "Bokning 1/2" in text
    assert "──────────────" in text


def test_mailto_and_telegram_urls() -> None:
    booking = SimpleNamespace(
        booking_date=date(2026, 8, 10),
        booking_time=time(11, 30),
        service_name="Alfa skanning",
    )
    mail = mailto_url(
        to_email="anna@example.com",
        client_name="Anna",
        booking=booking,  # type: ignore[arg-type]
    )
    assert mail.startswith("mailto:anna@example.com?")
    assert "subject=" in mail
    assert telegram_user_url(12345) == "tg://user?id=12345"


def test_status_label_sv() -> None:
    assert status_label_sv(BookingStatus.pending) == "Väntar på bekräftelse"
    assert status_label_sv(BookingStatus.confirmed) == "Bekräftad"
