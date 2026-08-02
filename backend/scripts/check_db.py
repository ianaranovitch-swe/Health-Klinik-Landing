"""Проверка подключения к БД: python -m scripts.check_db"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Подтянуть .env из корня проекта или backend/
load_dotenv(ROOT.parent / ".env")
load_dotenv(ROOT / ".env")

from app.db import check_connection, get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    # Не печатаем пароль целиком
    safe = settings.database_url.split("@")[-1]
    print(f"Подключаюсь к хосту/БД: ...@{safe}")
    check_connection()
    print("OK: соединение с PostgreSQL работает.")


if __name__ == "__main__":
    main()
