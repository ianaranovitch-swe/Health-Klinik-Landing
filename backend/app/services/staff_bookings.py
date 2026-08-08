"""Актуальные брони для staff-бота: список и красивый текст."""

from __future__ import annotations

from datetime import date, datetime, time
from html import escape
from urllib.parse import quote
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Booking, BookingStatus

# Клиника в Швеции — «сегодня» и «сейчас» по Стокгольму
_CLINIC_TZ = ZoneInfo("Europe/Stockholm")

_STATUS_SV: dict[BookingStatus, str] = {
    BookingStatus.pending: "Väntar på bekräftelse",
    BookingStatus.confirmed: "Bekräftad",
    BookingStatus.cancelled: "Avbokad",
    BookingStatus.completed: "Genomförd",
}


def _now_clinic() -> datetime:
    return datetime.now(_CLINIC_TZ)


def is_current_or_future_slot(
    booking_date: date,
    booking_time: time,
    *,
    now: datetime | None = None,
) -> bool:
    """True, если слот ещё не прошёл (сегодняшнее прошедшее время — нет)."""
    clock = now or _now_clinic()
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=_CLINIC_TZ)
    local = clock.astimezone(_CLINIC_TZ)
    if booking_date > local.date():
        return True
    if booking_date < local.date():
        return False
    return booking_time >= local.time().replace(second=0, microsecond=0)


def list_active_bookings(db: Session) -> list[Booking]:
    """
    Все актуальные брони клиники (pending + confirmed, ещё не прошедшие).
    Все 4 staff видят один и тот же список.
    """
    today = _now_clinic().date()
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
        .order_by(Booking.booking_date.asc(), Booking.booking_time.asc())
    )
    rows = list(db.scalars(stmt).unique().all())
    now = _now_clinic()
    return [
        b
        for b in rows
        if is_current_or_future_slot(b.booking_date, b.booking_time, now=now)
    ]


def status_label_sv(status: BookingStatus) -> str:
    return _STATUS_SV.get(status, status.value)


def format_booking_card(booking: Booking, *, index: int, total: int) -> str:
    """Карточка одной брони — сразу видно кто, когда и к кому."""
    client = booking.client
    therapist = booking.therapist
    time_label = booking.booking_time.strftime("%H:%M")
    header = f"Bokning {index}/{total}" if total > 1 else "Bokning"
    lines = [
        f"📅 <b>{escape(header)}</b>",
        "──────────────",
        f"<b>Datum:</b> {booking.booking_date.isoformat()} kl. {time_label}",
        f"<b>Status:</b> {escape(status_label_sv(booking.status))}",
        "",
        f"<b>Klient:</b> {escape(client.name)}",
        f"<b>Telefon:</b> {escape(client.phone)}",
        f"<b>E-post:</b> {escape(client.email)}",
        "",
        f"<b>Tjänst:</b> {escape(booking.service_name)}",
        f"<b>Behandlare:</b> {escape(therapist.name)}",
    ]
    return "\n".join(lines)


def mailto_url(*, to_email: str, client_name: str, booking: Booking) -> str:
    """Ссылка mailto: — откроет стандартный почтовый клиент."""
    time_label = booking.booking_time.strftime("%H:%M")
    subject = (
        f"Angående din bokning {booking.booking_date.isoformat()} kl. {time_label}"
    )
    body = (
        f"Hej {client_name},\n\n"
        f"Vi hör av oss angående din bokning "
        f"({booking.service_name}) "
        f"{booking.booking_date.isoformat()} kl. {time_label}.\n\n"
        f"Vänliga hälsningar\nMänniskans Resurser"
    )
    return (
        f"mailto:{to_email}"
        f"?subject={quote(subject)}"
        f"&body={quote(body)}"
    )


def telegram_user_url(telegram_id: int) -> str:
    """Открыть чат с пользователем по Telegram ID (мобильные клиенты)."""
    return f"tg://user?id={telegram_id}"
