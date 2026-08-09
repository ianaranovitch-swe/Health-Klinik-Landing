"""Фоновый цикл напоминаний (рядом с long polling)."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.db import get_session_factory
from app.services.reminders import (
    collect_due_reminders,
    format_client_reminder,
    format_staff_reminder,
    mark_reminder_sent,
    staff_recipient_ids,
)

logger = logging.getLogger(__name__)

# Как часто проверяем БД (секунды)
_POLL_SECONDS = 60


async def _safe_send(bot: Bot, chat_id: int, text: str) -> None:
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except TelegramAPIError:
        logger.exception("Не удалось отправить напоминание chat_id=%s", chat_id)
    except Exception:
        logger.exception("Ошибка отправки напоминания chat_id=%s", chat_id)


async def process_reminders_once(bot: Bot) -> int:
    """
    Один проход: найти due-напоминания, разослать staff + клиенту, пометить sent.
    Возвращает число обработанных jobs.
    """
    session = get_session_factory()()
    sent = 0
    try:
        jobs = collect_due_reminders(session)
        if not jobs:
            return 0
        staff_ids = staff_recipient_ids(session)

        for job in jobs:
            booking = job.booking
            staff_text = format_staff_reminder(booking, job.kind)
            client_text = format_client_reminder(booking, job.kind)

            for tg_id in staff_ids:
                await _safe_send(bot, tg_id, staff_text)

            client_tg = (
                booking.client.telegram_id if booking.client is not None else None
            )
            if (
                client_text is not None
                and client_tg is not None
                and client_tg > 0
            ):
                await _safe_send(bot, client_tg, client_text)

            mark_reminder_sent(session, booking, job.kind)
            sent += 1
            logger.info(
                "Напоминание %s отправлено для booking_id=%s status=%s",
                job.kind.value,
                booking.id,
                booking.status.value,
            )
    except Exception:
        logger.exception("Сбой в process_reminders_once")
        session.rollback()
    finally:
        session.close()
    return sent


async def reminder_loop(bot: Bot) -> None:
    """Бесконечный цикл до отмены задачи при остановке бота."""
    logger.info(
        "Цикл напоминаний запущен (интервал %s с, виды: 24h и 2h)",
        _POLL_SECONDS,
    )
    while True:
        try:
            await process_reminders_once(bot)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Неожиданная ошибка цикла напоминаний")
        await asyncio.sleep(_POLL_SECONDS)
