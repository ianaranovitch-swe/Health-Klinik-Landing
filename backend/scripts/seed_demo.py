"""Демо-данные: python -m scripts.seed_demo"""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT.parent / ".env")
load_dotenv(ROOT / ".env")

from app.db import get_session_factory  # noqa: E402
from app.models import Service, Therapist  # noqa: E402


def main() -> None:
    telegram_id = int(os.getenv("SEED_THERAPIST_TELEGRAM_ID", "123456789"))
    email = os.getenv("SEED_THERAPIST_EMAIL", "therapist@example.com")
    name = os.getenv("SEED_THERAPIST_NAME", "Anna Svensson")

    session = get_session_factory()()
    try:
        therapist = session.scalar(
            select(Therapist).where(Therapist.telegram_id == telegram_id)
        )
        if therapist is None:
            therapist = Therapist(
                telegram_id=telegram_id,
                name=name,
                email=email,
                specialization="Monicor & Alfa",
                active=True,
            )
            session.add(therapist)
            print(f"Добавлен терапевт: {name} <{email}>")
        else:
            therapist.email = email
            therapist.name = name
            therapist.active = True
            print(f"Обновлён терапевт id={therapist.id}")

        demo_services = [
            ("Monicor-session", 90, Decimal("1500.00")),
            ("Monicor + Alfa", 120, Decimal("2000.00")),
        ]
        for svc_name, duration, price in demo_services:
            existing = session.scalar(select(Service).where(Service.name == svc_name))
            if existing is None:
                session.add(
                    Service(name=svc_name, duration_minutes=duration, price=price)
                )
                print(f"Добавлена услуга: {svc_name}")

        session.commit()
        print("OK: сиды применены.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
