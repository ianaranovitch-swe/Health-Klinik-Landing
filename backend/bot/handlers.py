"""Обработчики команд бота."""

from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.db import get_session_factory
from app.services.booking_confirm import confirm_booking_by_payload
from app.services.staff_access import get_active_staff_by_telegram_id
from bot.client_booking.handlers import start_client_booking
from bot.staff_handlers import send_staff_welcome
from bot.therapist_notify import notify_therapist_confirmed_booking

logger = logging.getLogger(__name__)

router = Router(name="booking")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    bot: Bot,
    state: FSMContext,
) -> None:
    """
    /start — staff-meny, guidad klientbokning eller confirm_<uuid> från webben
    """
    args = (command.args or "").strip()

    # Приветствие без payload — staff или guidad bokning
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

            await start_client_booking(message, state)
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

        if (
            result.ok
            and result.booking is not None
            and result.therapist is not None
            and result.client is not None
        ):
            await notify_therapist_confirmed_booking(
                bot,
                booking=result.booking,
                client=result.client,
                therapist=result.therapist,
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
