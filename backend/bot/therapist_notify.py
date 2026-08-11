"""Telegram-уведомление терапевту о подтверждённой брони."""

from __future__ import annotations

import logging

from aiogram import Bot

from app.models import Booking, Client, Therapist

logger = logging.getLogger(__name__)

# Заглушки из seed/.env.example — на них нельзя слать сообщения
PLACEHOLDER_TELEGRAM_IDS = frozenset(
    {
        2000000001,  # SEED_IWONA_TELEGRAM_ID по умолчанию
        123456789,  # старый демо-id
    }
)


def is_notifiable_telegram_id(telegram_id: int | None) -> bool:
    """True только для похожего на реальный user id (не seed-заглушка)."""
    if telegram_id is None or telegram_id <= 0:
        return False
    return telegram_id not in PLACEHOLDER_TELEGRAM_IDS


def format_confirmed_booking_message(
    *,
    booking: Booking,
    client: Client,
    therapist: Therapist,
) -> str:
    """Текст «Ny bokning bekräftad» для терапевта."""
    time_label = booking.booking_time.strftime("%H:%M")
    return (
        "Ny bokning bekräftad ✅\n\n"
        f"Klient: {client.name}\n"
        f"Telefon: {client.phone}\n"
        f"E-post: {client.email}\n"
        f"Tjänst: {booking.service_name}\n"
        f"Datum: {booking.booking_date.isoformat()} kl. {time_label}\n"
        f"Behandlare: {therapist.name}"
    )


async def notify_therapist_confirmed_booking(
    bot: Bot,
    *,
    booking: Booking,
    client: Client,
    therapist: Therapist,
) -> None:
    """Отправить терапевту сообщение о подтверждённой брони."""
    therapist_tg = therapist.telegram_id
    if not is_notifiable_telegram_id(therapist_tg):
        return

    text = format_confirmed_booking_message(
        booking=booking,
        client=client,
        therapist=therapist,
    )
    try:
        await bot.send_message(chat_id=therapist_tg, text=text)
    except Exception:
        logger.exception(
            "Не удалось уведомить терапевта telegram_id=%s",
            therapist_tg,
        )
