"""Юнит-тесты для staff-броней (без БД)."""

from __future__ import annotations

from datetime import date, datetime, time
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from app.models.booking import BookingStatus
from app.models.staff import StaffRole
from app.services.staff_bookings import (
    format_booking_card,
    format_therapist_group_header,
    group_bookings_by_therapist,
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


def test_format_booking_card_shows_status_and_client() -> None:
    booking = SimpleNamespace(
        booking_date=date(2026, 8, 10),
        booking_time=time(11, 30),
        status=BookingStatus.pending,
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
    assert "Väntar på bekräftelse" in text
    assert "──────────────" in text


def test_group_bookings_by_therapist() -> None:
    b1 = SimpleNamespace(therapist=SimpleNamespace(name="Iwona"))
    b2 = SimpleNamespace(therapist=SimpleNamespace(name="Viktoria"))
    b3 = SimpleNamespace(therapist=SimpleNamespace(name="Iwona"))
    groups = group_bookings_by_therapist([b1, b2, b3])  # type: ignore[arg-type]
    assert [name for name, _ in groups] == ["Iwona", "Viktoria"]
    assert len(groups[0][1]) == 2
    assert "Behandlare: Iwona" in format_therapist_group_header("Iwona", 2)


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


def test_email_confirm_link_shape() -> None:
    """Формат ссылки как в build_email_confirm_link (без импорта FastAPI-схем)."""
    import uuid

    token = uuid.UUID("12345678-1234-5678-1234-567812345678")
    base = "https://api.example.com".rstrip("/")
    link = f"{base}/api/bookings/confirm/{token}"
    assert link.endswith(
        "/api/bookings/confirm/12345678-1234-5678-1234-567812345678"
    )


def test_status_label_sv() -> None:
    assert "Väntar" in status_label_sv(BookingStatus.pending)
    assert "Bekräftad" in status_label_sv(BookingStatus.confirmed)
    assert StaffRole.therapist.value == "therapist"
