"""Напоминания о бронях: 24 ч и 2 ч до слота (Europe/Stockholm)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from html import escape
from typing import assert_never
from zoneinfo import ZoneInfo

from sqlalchemy import case, select
from sqlalchemy.orm import Session, joinedload

from app.models import Booking, BookingStatus
from app.services.staff_access import list_active_staff_telegram_ids
from app.services.staff_bookings import status_label_sv

_CLINIC_TZ = ZoneInfo("Europe/Stockholm")


class ReminderKind(str, Enum):
    h24 = "24h"
    h2 = "2h"


@dataclass(frozen=True)
class ReminderJob:
    """Одна бронь + тип напоминания, готовая к отправке."""

    booking: Booking
    kind: ReminderKind


def booking_slot_datetime(booking: Booking) -> datetime:
    """Дата+время слота в часовом поясе клиники."""
    return datetime.combine(
        booking.booking_date,
        booking.booking_time,
        tzinfo=_CLINIC_TZ,
    )


def should_send_reminder(
    *,
    kind: ReminderKind,
    delta: timedelta,
    already_sent: bool,
) -> bool:
    """
    Окна с «догоном», если бот был выключен:
    - 24h: осталось ≤ 24 ч и > 2 ч, ещё не слали
    - 2h: осталось ≤ 2 ч и > 0, ещё не слали
    """
    if already_sent or delta.total_seconds() <= 0:
        return False
    if kind is ReminderKind.h24:
        return delta <= timedelta(hours=24) and delta > timedelta(hours=2)
    if kind is ReminderKind.h2:
        return delta <= timedelta(hours=2)
    assert_never(kind)


def collect_due_reminders(
    db: Session,
    *,
    now: datetime | None = None,
) -> list[ReminderJob]:
    """Брони pending/confirmed, которым пора слать 24h и/или 2h."""
    clock = now or datetime.now(_CLINIC_TZ)
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=_CLINIC_TZ)
    clock = clock.astimezone(_CLINIC_TZ)

    today = clock.date()
    stmt = (
        select(Booking)
        .options(
            joinedload(Booking.client),
            joinedload(Booking.therapist),
        )
        .where(
            Booking.status.in_(
                (BookingStatus.pending, BookingStatus.confirmed)
            ),
            Booking.booking_date >= today,
        )
        .order_by(
            case(
                (Booking.status == BookingStatus.confirmed, 0),
                else_=1,
            ),
            Booking.booking_date.asc(),
            Booking.booking_time.asc(),
        )
    )
    rows = list(db.scalars(stmt).unique().all())

    jobs: list[ReminderJob] = []
    for booking in rows:
        slot = booking_slot_datetime(booking)
        delta = slot - clock
        if should_send_reminder(
            kind=ReminderKind.h24,
            delta=delta,
            already_sent=booking.reminder_24h_sent_at is not None,
        ):
            jobs.append(ReminderJob(booking=booking, kind=ReminderKind.h24))
        if should_send_reminder(
            kind=ReminderKind.h2,
            delta=delta,
            already_sent=booking.reminder_2h_sent_at is not None,
        ):
            jobs.append(ReminderJob(booking=booking, kind=ReminderKind.h2))
    return jobs


def _when_label(kind: ReminderKind) -> str:
    if kind is ReminderKind.h24:
        return "om cirka 24 timmar"
    if kind is ReminderKind.h2:
        return "om cirka 2 timmar"
    assert_never(kind)


def format_staff_reminder(booking: Booking, kind: ReminderKind) -> str:
    """Текст напоминания для Viktoria / Iwona / Boris / Jan."""
    client = booking.client
    therapist = booking.therapist
    time_label = booking.booking_time.strftime("%H:%M")
    client_name = escape(client.name) if client is not None else "Okänd"
    client_phone = escape(client.phone) if client is not None else "—"
    client_email = escape(client.email) if client is not None else "—"
    therapist_name = (
        escape(therapist.name) if therapist is not None else "Okänd"
    )
    return (
        f"🔔 <b>Påminnelse — bokning {_when_label(kind)}</b>\n"
        f"──────────────\n"
        f"<b>Status:</b> {escape(status_label_sv(booking.status))}\n"
        f"<b>Datum:</b> {booking.booking_date.isoformat()} kl. {time_label}\n\n"
        f"<b>Klient:</b> {client_name}\n"
        f"<b>Telefon:</b> {client_phone}\n"
        f"<b>E-post:</b> {client_email}\n\n"
        f"<b>Tjänst:</b> {escape(booking.service_name)}\n"
        f"<b>Behandlare:</b> {therapist_name}"
    )


def format_client_reminder(booking: Booking, kind: ReminderKind) -> str | None:
    """
    Текст напоминания клиенту.
    None — нет клиента (нельзя слать / нечего форматировать).
    """
    client = booking.client
    if client is None:
        return None
    therapist = booking.therapist
    time_label = booking.booking_time.strftime("%H:%M")
    therapist_name = (
        escape(therapist.name) if therapist is not None else "Okänd"
    )
    return (
        f"🔔 <b>Påminnelse om din bokning</b>\n\n"
        f"Hej {escape(client.name)}!\n"
        f"Din tid hos Människans Resurser är {_when_label(kind)}.\n\n"
        f"<b>Status:</b> {escape(status_label_sv(booking.status))}\n"
        f"<b>Datum:</b> {booking.booking_date.isoformat()} kl. {time_label}\n"
        f"<b>Tjänst:</b> {escape(booking.service_name)}\n"
        f"<b>Behandlare:</b> {therapist_name}\n\n"
        f"Vi ses på kliniken!"
    )


def mark_reminder_sent(
    db: Session,
    booking: Booking,
    kind: ReminderKind,
    *,
    when: datetime | None = None,
) -> None:
    stamp = when or datetime.now(_CLINIC_TZ)
    if kind is ReminderKind.h24:
        booking.reminder_24h_sent_at = stamp
    elif kind is ReminderKind.h2:
        booking.reminder_2h_sent_at = stamp
    else:
        assert_never(kind)
    db.commit()


def staff_recipient_ids(db: Session) -> list[int]:
    return list_active_staff_telegram_ids(db)
