"""Обработчики команд бота."""

from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message

from app.db import get_session_factory
from app.services.booking_confirm import confirm_booking_by_payload
from app.services.staff_access import get_active_staff_by_telegram_id
from bot.staff_handlers import send_staff_welcome

logger = logging.getLogger(__name__)

router = Router(name="booking")

# Заглушки из seed/.env.example — на них нельзя слать сообщения
PLACEHOLDER_TELEGRAM_IDS = frozenset(
    {
        2000000001,  # SEED_IWONA_TELEGRAM_ID по умолчанию
        123456789,  # старый демо-id
    }
)


def _is_notifiable_telegram_id(telegram_id: int | None) -> bool:
    """True только для похожего на реальный user id (не seed-заглушка)."""
    if telegram_id is None or telegram_id <= 0:
        return False
    return telegram_id not in PLACEHOLDER_TELEGRAM_IDS


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, bot: Bot) -> None:
    """
    /start — приветствие (клиент или staff)
    /start confirm_<uuid> — подтверждение брони с сайта
    """
    args = (command.args or "").strip()

    # Приветствие без payload — staff или клиент
    if not args:
        try:
            user = message.from_user
            if user is not None:
                session = get_session_factory()()
                try:
                    staff = get_active_staff_by_telegram_id(session, user.id)
                    if staff is not None:
                        await send_staff_welcome(message, staff)
                        return
                finally:
                    session.close()

            await message.answer(
                "Hej! Jag är bokningsboten för Människans Resurser.\n\n"
                "När du bokat tid på webbplatsen, tryck på knappen "
                "«Bekräfta i Telegram» i bekräftelsen — då syns din tid här."
            )
        except Exception:
            logger.exception("Не удалось отправить приветствие /start")
        return

    try:
        session = get_session_factory()()
        try:
            result = confirm_booking_by_payload(
                session,
                args,
                client_telegram_id=(
                    message.from_user.id if message.from_user else None
                ),
            )
        finally:
            session.close()

        await message.answer(result.message_sv)

        # Уведомление терапевту (если telegram_id не заглушка)
        if (
            result.ok
            and result.booking is not None
            and result.therapist is not None
            and result.client is not None
        ):
            therapist_tg = result.therapist.telegram_id
            if _is_notifiable_telegram_id(therapist_tg):
                try:
                    time_label = result.booking.booking_time.strftime("%H:%M")
                    text = (
                        "Ny bokning bekräftad ✅\n\n"
                        f"Klient: {result.client.name}\n"
                        f"Telefon: {result.client.phone}\n"
                        f"E-post: {result.client.email}\n"
                        f"Tjänst: {result.booking.service_name}\n"
                        f"Datum: {result.booking.booking_date.isoformat()} "
                        f"kl. {time_label}\n"
                        f"Behandlare: {result.therapist.name}"
                    )
                    await bot.send_message(chat_id=therapist_tg, text=text)
                except Exception:
                    logger.exception(
                        "Не удалось уведомить терапевта telegram_id=%s",
                        therapist_tg,
                    )
    except Exception:
        logger.exception("Ошибка подтверждения брони (args=%r)", command.args)
        try:
            await message.answer(
                "Något gick fel när bokningen skulle bekräftas. "
                "Försök igen om en stund eller kontakta kliniken."
            )
        except Exception:
            logger.exception("Не удалось отправить сообщение об ошибке подтверждения")
