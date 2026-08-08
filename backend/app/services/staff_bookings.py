"""Актуальные брони для staff-бота: список и красивый текст."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time
from html import escape
from typing import assert_never
from urllib.parse import quote
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Booking, BookingStatus, Therapist
from app.models.staff import StaffMember, StaffRole

# Клиника в Швеции — «сегодня» и «сейчас» по Стокгольму
_CLINIC_TZ = ZoneInfo("Europe/Stockholm")

_STATUS_SV: dict[BookingStatus, str] = {
    BookingStatus.pending: "⏳ Väntar på bekräftelse",
    BookingStatus.confirmed: "✅ Bekräftad",
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


def find_therapist_for_staff(db: Session, staff: StaffMember) -> Therapist | None:
    """Связь staff → Therapist по одинаковому telegram_id."""
    return db.scalar(
        select(Therapist).where(Therapist.telegram_id == staff.telegram_id)
    )


def list_active_bookings_for_staff(
    db: Session,
    staff: StaffMember,
) -> list[Booking]:
    """
    Актуальные брони (pending + confirmed, ещё не прошедшие).
    therapist — только свои; superuser — все.
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
        .order_by(
            Booking.booking_date.asc(),
            Booking.booking_time.asc(),
        )
    )

    if staff.role is StaffRole.therapist:
        therapist = find_therapist_for_staff(db, staff)
        if therapist is None:
            return []
        stmt = stmt.where(Booking.therapist_id == therapist.id)
    elif staff.role is StaffRole.superuser:
        pass
    else:
        assert_never(staff.role)

    rows = list(db.scalars(stmt).unique().all())
    now = _now_clinic()
    return [
        b
        for b in rows
        if is_current_or_future_slot(b.booking_date, b.booking_time, now=now)
    ]


def group_bookings_by_therapist(
    bookings: list[Booking],
) -> list[tuple[str, list[Booking]]]:
    """
    Группы для суперпользователя: [(имя терапевта, брони…), …]
    Порядок групп — по имени; внутри уже отсортировано по дате/времени.
    """
    buckets: dict[str, list[Booking]] = defaultdict(list)
    for booking in bookings:
        name = booking.therapist.name if booking.therapist else "Okänd"
        buckets[name].append(booking)
    return sorted(buckets.items(), key=lambda item: item[0].lower())


def status_label_sv(status: BookingStatus) -> str:
    return _STATUS_SV.get(status, status.value)


def format_booking_card(
    booking: Booking,
    *,
    index: int,
    total: int,
    show_therapist: bool = True,
) -> str:
    """Карточка одной брони — статус pending/confirmed сразу заметен."""
    client = booking.client
    therapist = booking.therapist
    time_label = booking.booking_time.strftime("%H:%M")
    header = f"Bokning {index}/{total}" if total > 1 else "Bokning"
    lines = [
        f"📅 <b>{escape(header)}</b>",
        "──────────────",
        f"<b>Status:</b> {escape(status_label_sv(booking.status))}",
        f"<b>Datum:</b> {booking.booking_date.isoformat()} kl. {time_label}",
        "",
        f"<b>Klient:</b> {escape(client.name)}",
        f"<b>Telefon:</b> {escape(client.phone)}",
        f"<b>E-post:</b> {escape(client.email)}",
        "",
        f"<b>Tjänst:</b> {escape(booking.service_name)}",
    ]
    if show_therapist:
        lines.append(f"<b>Behandlare:</b> {escape(therapist.name)}")
    return "\n".join(lines)


def format_therapist_group_header(therapist_name: str, count: int) -> str:
    """Разделитель групп для Boris/Jan."""
    return (
        f"══════════════\n"
        f"<b>Behandlare: {escape(therapist_name)}</b>\n"
        f"Bokningar: {count}\n"
        f"══════════════"
    )


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
