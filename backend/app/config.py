"""Настройки из переменных окружения."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def normalize_database_url(url: str) -> str:
    """Railway часто отдаёт postgres:// — SQLAlchemy + psycopg ждут postgresql+psycopg://."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _split_origins(raw: str | None) -> list[str]:
    if not raw:
        return ["*"]
    return [part.strip() for part in raw.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    """Конфиг приложения."""

    database_url: str
    bot_username: str = ""
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    resend_api_key: str | None = None
    email_from: str = "bokning@example.com"

    @classmethod
    def from_env(cls) -> Settings:
        raw = os.getenv("DATABASE_URL")
        if not raw:
            raise RuntimeError(
                "Переменная DATABASE_URL не задана. "
                "Пример: postgresql://user:pass@host:5432/railway"
            )
        return cls(
            database_url=normalize_database_url(raw),
            bot_username=(os.getenv("BOT_USERNAME") or "").lstrip("@"),
            cors_origins=_split_origins(os.getenv("CORS_ORIGINS")),
            resend_api_key=os.getenv("RESEND_API_KEY") or None,
            email_from=os.getenv("EMAIL_FROM") or "bokning@example.com",
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
