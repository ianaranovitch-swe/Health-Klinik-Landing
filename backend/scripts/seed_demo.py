"""Демо-данные и актуальный каталог услуг: python -m scripts.seed_demo"""

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
from app.models import Booking, Service, Therapist  # noqa: E402

# Актуальный прайс для формы бронирования
SERVICE_CATALOG: list[tuple[str, int, Decimal]] = [
    ("Alfa skanning", 40, Decimal("600.00")),
    (
        'Hälsoundersökning med "EIS"-system',
        50,
        Decimal("950.00"),
    ),
    (
        'Uppföljning: EIS-system (efterskanning)',
        45,
        Decimal("500.00"),
    ),
    ("Hälsoundersökning med Monicor-system", 90, Decimal("1200.00")),
    ("Uppföljning: Monicor-system (återbesök)", 80, Decimal("600.00")),
    ("Paket: Monicor, EIS och Alfa", 120, Decimal("2200.00")),
    ("Paket: EIS + Monicor", 90, Decimal("1800.00")),
    ("Uppföljning: Paket EIS + Monicor", 90, Decimal("1000.00")),
]


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
                specialization="Monicor, EIS & Alfa",
                active=True,
            )
            session.add(therapist)
            print(f"Добавлен терапевт: {name} <{email}>")
        else:
            therapist.email = email
            therapist.name = name
            therapist.specialization = "Monicor, EIS & Alfa"
            therapist.active = True
            print(f"Обновлён терапевт id={therapist.id}")

        catalog_names = {name for name, _, _ in SERVICE_CATALOG}
        for svc_name, duration, price in SERVICE_CATALOG:
            existing = session.scalar(select(Service).where(Service.name == svc_name))
            if existing is None:
                session.add(
                    Service(name=svc_name, duration_minutes=duration, price=price)
                )
                print(f"Добавлена услуга: {svc_name}")
            else:
                existing.duration_minutes = duration
                existing.price = price
                print(f"Обновлена услуга: {svc_name}")

        # Удаляем устаревшие услуги, на которые нет записей
        stale = session.scalars(
            select(Service).where(Service.name.not_in(catalog_names))
        ).all()
        for svc in stale:
            has_booking = session.scalar(
                select(Booking.id).where(Booking.service_name == svc.name).limit(1)
            )
            if has_booking is None:
                session.delete(svc)
                print(f"Удалена устаревшая услуга: {svc.name}")
            else:
                print(
                    f"Оставлена устаревшая услуга (есть записи): {svc.name}"
                )

        session.commit()
        print("OK: сиды применены.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
