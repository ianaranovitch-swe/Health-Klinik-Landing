"""Точка входа Telegram-бота: python -m bot.main"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .env: корень репо и/или backend/
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _BACKEND_DIR.parent
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_BACKEND_DIR / ".env")

# Чтобы `python -m bot.main` видел пакет app
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from aiogram import Bot, Dispatcher  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.enums import ParseMode  # noqa: E402
from aiogram.fsm.storage.memory import MemoryStorage  # noqa: E402

from bot.client_booking.handlers import router as client_booking_router  # noqa: E402
from bot.handlers import router  # noqa: E402
from bot.reminder_loop import reminder_loop  # noqa: E402
from bot.staff_handlers import router as staff_router  # noqa: E402


async def main() -> None:
    token = (os.getenv("BOT_TOKEN") or "").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN не задан. Создай бота у @BotFather и добавь переменную."
        )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger = logging.getLogger("bot")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    dp.include_router(client_booking_router)
    dp.include_router(staff_router)

    me = await bot.get_me()
    logger.info("Бот запущен: @%s (id=%s)", me.username, me.id)

    # Сбрасываем webhook, иначе long polling не получает сообщения
    await bot.delete_webhook(drop_pending_updates=True)

    # Напоминания 24h / 2h в том же процессе, что и polling
    reminders_task = asyncio.create_task(
        reminder_loop(bot),
        name="booking-reminders",
    )
    try:
        await dp.start_polling(bot)
    finally:
        reminders_task.cancel()
        try:
            await reminders_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
