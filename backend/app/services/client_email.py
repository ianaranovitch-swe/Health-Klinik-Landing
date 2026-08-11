"""Утилиты e-post klient — без тяжёлых зависимостей (Resend и т.д.)."""

from __future__ import annotations

SYNTHETIC_EMAIL_DOMAIN = "noemail.mrboka.local"


def synthetic_telegram_client_email(telegram_id: int) -> str:
    """Placeholder e-post för klienter utan riktig adress i Telegram-flow."""
    return f"tg_{telegram_id}@{SYNTHETIC_EMAIL_DOMAIN}"


def is_synthetic_client_email(email: str) -> bool:
    """Синтетический адрес — только для БД, не показывать пользователю."""
    return email.lower().endswith(f"@{SYNTHETIC_EMAIL_DOMAIN}")
