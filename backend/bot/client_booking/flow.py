"""Вспомогательные функции flow: отправка шагов, сводка, валидация."""

from __future__ import annotations

import re
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, Message

from app.services.client_email import is_synthetic_client_email
from bot.client_booking.texts import STEPS

# Шведский мобильный: 07…, +46…, пробелы/дефисы допустимы
_PHONE_RE = re.compile(
    r"^(?:\+46|0)\s*7[\d\s\-]{7,12}$",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


async def send_step(
    message: Message,
    step_key: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
    extra: str = "",
) -> None:
    """Отправить текст шага; позже можно добавить image_url."""
    step = STEPS[step_key]
    text = step["text"]
    if extra:
        text = f"{extra}\n\n{text}"
    image_url = step.get("image_url")
    if image_url:
        await message.answer_photo(photo=image_url, caption=text, reply_markup=reply_markup)
    else:
        await message.answer(text, reply_markup=reply_markup)


def format_summary(data: dict) -> str:
    """Sammanfattning перед bekräftelse."""
    lines = [
        "<b>Sammanfattning</b>",
        f"Namn: {data.get('name', '—')}",
        f"Tjänst: {data.get('service_name', '—')}",
        f"Behandlare: {data.get('therapist_name', '—')}",
        f"Datum: {data.get('date', '—')}",
        f"Tid: {data.get('time', '—')}",
        f"Telefon: {data.get('phone', '—')}",
    ]
    email = data.get("email")
    # Синтетический placeholder — только для БД, не показываем клиенту
    if email and not is_synthetic_client_email(email):
        lines.append(f"E-post: {email}")
    return "\n".join(lines)


def is_valid_name(value: str) -> bool:
    return len(value.strip()) >= 2


def normalize_phone(value: str) -> str | None:
    """Проверить и вернуть очищенный номер или None."""
    raw = value.strip()
    if not _PHONE_RE.match(raw):
        return None
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("46"):
        return f"+{digits}"
    if digits.startswith("0"):
        return f"+46{digits[1:]}"
    return None


def is_valid_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


def parse_booking_time(time_str: str):
    """HH:MM → time."""
    return datetime.strptime(time_str, "%H:%M").time()
