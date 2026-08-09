"""Тесты окон напоминаний (без БД / Telegram)."""

from __future__ import annotations

from datetime import date, time, timedelta
from types import SimpleNamespace

from app.models.booking import BookingStatus
from app.services.reminders import (
    ReminderKind,
    format_client_reminder,
    format_staff_reminder,
    should_send_reminder,
)


def test_24h_window_inside() -> None:
    assert should_send_reminder(
        kind=ReminderKind.h24,
        delta=timedelta(hours=20),
        already_sent=False,
    )


def test_24h_window_too_soon_for_2h_only() -> None:
    # Уже в окне 2h — 24h не шлём (догон 24h только пока > 2h)
    assert not should_send_reminder(
        kind=ReminderKind.h24,
        delta=timedelta(hours=1, minutes=30),
        already_sent=False,
    )


def test_24h_already_sent() -> None:
    assert not should_send_reminder(
        kind=ReminderKind.h24,
        delta=timedelta(hours=20),
        already_sent=True,
    )


def test_2h_window() -> None:
    assert should_send_reminder(
        kind=ReminderKind.h2,
        delta=timedelta(hours=1, minutes=30),
        already_sent=False,
    )


def test_2h_past_slot() -> None:
    assert not should_send_reminder(
        kind=ReminderKind.h2,
        delta=timedelta(minutes=-5),
        already_sent=False,
    )


def test_2h_still_far() -> None:
    assert not should_send_reminder(
        kind=ReminderKind.h2,
        delta=timedelta(hours=5),
        already_sent=False,
    )


def test_format_staff_reminder_without_client() -> None:
    booking = SimpleNamespace(
        booking_date=date(2026, 8, 10),
        booking_time=time(11, 0),
        status=BookingStatus.confirmed,
        service_name="Alfa",
        client=None,
        therapist=SimpleNamespace(name="Viktoria"),
    )
    text = format_staff_reminder(booking, ReminderKind.h24)  # type: ignore[arg-type]
    assert "Okänd" in text
    assert "Alfa" in text


def test_format_client_reminder_without_client_returns_none() -> None:
    booking = SimpleNamespace(
        booking_date=date(2026, 8, 10),
        booking_time=time(11, 0),
        status=BookingStatus.pending,
        service_name="Alfa",
        client=None,
        therapist=SimpleNamespace(name="Iwona"),
    )
    assert format_client_reminder(booking, ReminderKind.h2) is None  # type: ignore[arg-type]
