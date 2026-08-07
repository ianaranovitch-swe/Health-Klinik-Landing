"""Подтверждение брони по telegram_confirm_token."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Booking, BookingStatus, Client, Therapist


@dataclass(frozen=True)
class ConfirmResult:
    """Результат подтверждения для ответа бота."""

    ok: bool
    message_sv: str
    booking: Booking | None = None
    therapist: Therapist | None = None
    client: Client | None = None


def _parse_confirm_token(payload: str) -> uuid.UUID | None:
    raw = (payload or "").strip()
    if raw.startswith("confirm_"):
        raw = raw[len("confirm_") :]
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


def confirm_booking_by_payload(
    db: Session,
    payload: str,
    *,
    client_telegram_id: int | None = None,
) -> ConfirmResult:
    """
    Подтверждает бронь по deep-link payload (confirm_<uuid>).
    Сохраняет telegram_id клиента, если передан.
    """
    token = _parse_confirm_token(payload)
    if token is None:
        return ConfirmResult(
            ok=False,
            message_sv=(
                "Länken är ogiltig. Öppna knappen «Bekräfta i Telegram» "
                "från bokningsbekräftelsen på webbplatsen."
            ),
        )

    booking = db.scalar(
        select(Booking)
        .options(
            joinedload(Booking.client),
            joinedload(Booking.therapist),
        )
        .where(Booking.telegram_confirm_token == token)
    )
    if booking is None:
        return ConfirmResult(
            ok=False,
            message_sv="Bokningen hittades inte. Kontakta kliniken om problemet kvarstår.",
        )

    if booking.status == BookingStatus.cancelled:
        return ConfirmResult(
            ok=False,
            message_sv="Den här bokningen är avbokad och kan inte bekräftas.",
            booking=booking,
            therapist=booking.therapist,
            client=booking.client,
        )

    if booking.status == BookingStatus.completed:
        return ConfirmResult(
            ok=False,
            message_sv="Besöket är redan markerat som genomfört.",
            booking=booking,
            therapist=booking.therapist,
            client=booking.client,
        )

    if client_telegram_id is not None and booking.client is not None:
        # Привязываем Telegram-аккаунт клиента (если слот свободен)
        other = db.scalar(
            select(Client).where(
                Client.telegram_id == client_telegram_id,
                Client.id != booking.client_id,
            )
        )
        if other is None:
            booking.client.telegram_id = client_telegram_id

    if booking.status == BookingStatus.confirmed:
        db.commit()
        time_label = booking.booking_time.strftime("%H:%M")
        return ConfirmResult(
            ok=True,
            message_sv=(
                f"Bokningen är redan bekräftad ✅\n\n"
                f"{booking.service_name}\n"
                f"{booking.booking_date.isoformat()} kl. {time_label}\n"
                f"Behandlare: {booking.therapist.name}"
            ),
            booking=booking,
            therapist=booking.therapist,
            client=booking.client,
        )

    booking.status = BookingStatus.confirmed
    db.commit()
    db.refresh(booking)

    time_label = booking.booking_time.strftime("%H:%M")
    return ConfirmResult(
        ok=True,
        message_sv=(
            f"Tack! Din bokning är bekräftad ✅\n\n"
            f"{booking.service_name}\n"
            f"{booking.booking_date.isoformat()} kl. {time_label}\n"
            f"Behandlare: {booking.therapist.name}\n\n"
            f"Vi ses på kliniken!"
        ),
        booking=booking,
        therapist=booking.therapist,
        client=booking.client,
    )
