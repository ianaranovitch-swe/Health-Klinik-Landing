"""Демо-данные и каталог: python -m scripts.seed_demo

Два терапевта:
- Iwona — Alfa + Monicor
- Viktoria — Alfa + Monicor + EIS
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT.parent / ".env")
load_dotenv(ROOT / ".env")

from app.db import get_session_factory  # noqa: E402
from app.models import Booking, Service, StaffMember, StaffRole, Therapist  # noqa: E402

# name, duration, price, набор методов (для привязки к терапевту)
SERVICE_CATALOG: list[tuple[str, int, Decimal, frozenset[str]]] = [
    ("Alfa skanning", 40, Decimal("600.00"), frozenset({"alfa"})),
    (
        'Hälsoundersökning med "EIS"-system',
        50,
        Decimal("950.00"),
        frozenset({"eis"}),
    ),
    (
        "Uppföljning: EIS-system (efterskanning)",
        45,
        Decimal("500.00"),
        frozenset({"eis"}),
    ),
    (
        "Hälsoundersökning med Monicor-system",
        90,
        Decimal("1200.00"),
        frozenset({"monicor"}),
    ),
    (
        "Uppföljning: Monicor-system (återbesök)",
        80,
        Decimal("600.00"),
        frozenset({"monicor"}),
    ),
    (
        "Paket: Monicor, EIS och Alfa",
        120,
        Decimal("2200.00"),
        frozenset({"alfa", "monicor", "eis"}),
    ),
    (
        "Paket: EIS + Monicor",
        90,
        Decimal("1800.00"),
        frozenset({"monicor", "eis"}),
    ),
    (
        "Uppföljning: Paket EIS + Monicor",
        90,
        Decimal("1000.00"),
        frozenset({"monicor", "eis"}),
    ),
]

# Ключ → разрешённые методы
IWONA_METHODS = frozenset({"alfa", "monicor"})
VIKTORIA_METHODS = frozenset({"alfa", "monicor", "eis"})

# Дефолтные Telegram ID — все разные (unique на therapists / staff_members)
DEFAULT_VIKTORIA_TG = "1030716946"
DEFAULT_IWONA_TG = "2000000001"  # заглушка, пока нет реального ID в env
DEFAULT_BORIS_TG = "1647802523"
DEFAULT_JAN_TG = "7973899604"


def _env(name: str, default: str) -> str:
    return (os.getenv(name) or default).strip()


def _assert_unique_telegram_ids(labeled_ids: list[tuple[str, int]]) -> None:
    """Падаем с понятной ошибкой, если два человека получили один telegram_id."""
    seen: dict[int, str] = {}
    for label, tg_id in labeled_ids:
        prev = seen.get(tg_id)
        if prev is not None:
            raise ValueError(
                f"Одинаковый telegram_id={tg_id} у «{prev}» и «{label}». "
                "Задай разные SEED_*_TELEGRAM_ID в env."
            )
        seen[tg_id] = label


def _upsert_therapist(
    session: Session,
    *,
    telegram_id: int,
    name: str,
    email: str,
    specialization: str,
) -> Therapist:
    email_norm = email.lower()
    therapist = session.scalar(
        select(Therapist).where(Therapist.email == email_norm)
    )
    if therapist is None:
        therapist = session.scalar(
            select(Therapist).where(Therapist.telegram_id == telegram_id)
        )
    if therapist is None:
        therapist = Therapist(
            telegram_id=telegram_id,
            name=name,
            email=email_norm,
            specialization=specialization,
            active=True,
        )
        session.add(therapist)
        session.flush()
        print(f"Добавлен терапевт: {name} <{email_norm}>")
    else:
        # telegram_id уникален — не конфликтуем с другим рядом
        clash = session.scalar(
            select(Therapist).where(
                Therapist.telegram_id == telegram_id,
                Therapist.id != therapist.id,
            )
        )
        if clash is None:
            therapist.telegram_id = telegram_id
        therapist.name = name
        therapist.email = email_norm
        therapist.specialization = specialization
        therapist.active = True
        print(f"Обновлён терапевт: {name} (id={therapist.id})")
    return therapist


def _upsert_staff(
    session: Session,
    *,
    telegram_id: int,
    name: str,
    role: StaffRole,
) -> StaffMember:
    """Добавить/обновить сотрудника бота (доступ к списку броней)."""
    member = session.scalar(
        select(StaffMember).where(StaffMember.telegram_id == telegram_id)
    )
    if member is None:
        # Имя могло смениться у того же человека — ищем по имени+роли редко нужно;
        # telegram_id — главный ключ доступа.
        member = StaffMember(
            telegram_id=telegram_id,
            name=name,
            role=role,
            active=True,
        )
        session.add(member)
        session.flush()
        print(f"Добавлен staff: {name} ({role.value}, tg={telegram_id})")
    else:
        member.name = name
        member.role = role
        member.active = True
        print(f"Обновлён staff: {name} ({role.value}, tg={telegram_id})")
    return member


def _sync_services(session: Session) -> dict[str, Service]:
    catalog_names = {row[0] for row in SERVICE_CATALOG}
    by_name: dict[str, Service] = {}
    for svc_name, duration, price, _methods in SERVICE_CATALOG:
        existing = session.scalar(select(Service).where(Service.name == svc_name))
        if existing is None:
            existing = Service(
                name=svc_name, duration_minutes=duration, price=price
            )
            session.add(existing)
            session.flush()
            print(f"Добавлена услуга: {svc_name}")
        else:
            existing.duration_minutes = duration
            existing.price = price
            print(f"Обновлена услуга: {svc_name}")
        by_name[svc_name] = existing

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
            # Сохраняем запись для истории броней; убираем из формы (без terapeutов)
            svc.therapists = []
            print(
                f"Оставлена устаревшая услуга (есть записи), снята с terapeutов: {svc.name}"
            )
    return by_name


def _link_services(
    therapist: Therapist,
    services_by_name: dict[str, Service],
    allowed_methods: frozenset[str],
) -> None:
    linked: list[Service] = []
    for svc_name, _d, _p, methods in SERVICE_CATALOG:
        if methods <= allowed_methods:
            linked.append(services_by_name[svc_name])
    therapist.services = linked
    print(f"  → {therapist.name}: {len(linked)} услуг")


def main() -> None:
    # Явные SEED_VIKTORIA_* / SEED_IWONA_*. Старые SEED_THERAPIST_* —
    # только для Viktoria, и только если там не указана Iwona.
    legacy_email = _env("SEED_THERAPIST_EMAIL", "")
    legacy_name = _env("SEED_THERAPIST_NAME", "")
    legacy_is_iwona = "iwona" in legacy_email.lower() or "iwona" in legacy_name.lower()

    if legacy_is_iwona:
        viktoria_tg = int(_env("SEED_VIKTORIA_TELEGRAM_ID", DEFAULT_VIKTORIA_TG))
        viktoria_email = _env("SEED_VIKTORIA_EMAIL", "mail@mr-ab.se")
        viktoria_name = _env("SEED_VIKTORIA_NAME", "Viktoria Antropova")
        iwona_tg = int(
            _env(
                "SEED_IWONA_TELEGRAM_ID",
                _env("SEED_THERAPIST_TELEGRAM_ID", DEFAULT_IWONA_TG),
            )
        )
        iwona_email = _env(
            "SEED_IWONA_EMAIL",
            legacy_email or "iwona@mr-ab.se",
        )
        iwona_name = _env(
            "SEED_IWONA_NAME",
            legacy_name or "Iwona Aranovitch",
        )
    else:
        viktoria_tg = int(
            _env(
                "SEED_VIKTORIA_TELEGRAM_ID",
                _env("SEED_THERAPIST_TELEGRAM_ID", DEFAULT_VIKTORIA_TG),
            )
        )
        viktoria_email = _env(
            "SEED_VIKTORIA_EMAIL",
            legacy_email or "mail@mr-ab.se",
        )
        viktoria_name = _env(
            "SEED_VIKTORIA_NAME",
            legacy_name or "Viktoria Antropova",
        )
        iwona_tg = int(_env("SEED_IWONA_TELEGRAM_ID", DEFAULT_IWONA_TG))
        iwona_email = _env("SEED_IWONA_EMAIL", "iwona@mr-ab.se")
        iwona_name = _env("SEED_IWONA_NAME", "Iwona Aranovitch")

    session = get_session_factory()()
    try:
        services_by_name = _sync_services(session)

        viktoria = _upsert_therapist(
            session,
            telegram_id=viktoria_tg,
            name=viktoria_name,
            email=viktoria_email,
            specialization="Monicor, EIS & Alfa",
        )
        iwona = _upsert_therapist(
            session,
            telegram_id=iwona_tg,
            name=iwona_name,
            email=iwona_email,
            specialization="Monicor & Alfa",
        )

        keep_ids = {viktoria.id, iwona.id}
        others = session.scalars(
            select(Therapist).where(Therapist.id.not_in(keep_ids))
        ).all()
        for other in others:
            other.active = False
            print(f"Деактивирован терапевт: {other.name} (id={other.id})")

        _link_services(viktoria, services_by_name, VIKTORIA_METHODS)
        _link_services(iwona, services_by_name, IWONA_METHODS)

        # Staff для бота: оба терапевта + суперпользователи (контроль процесса)
        boris_tg = int(_env("SEED_BORIS_TELEGRAM_ID", DEFAULT_BORIS_TG))
        boris_name = _env("SEED_BORIS_NAME", "Boris")
        jan_tg = int(_env("SEED_JAN_TELEGRAM_ID", DEFAULT_JAN_TG))
        jan_name = _env("SEED_JAN_NAME", "Jan")

        _assert_unique_telegram_ids(
            [
                ("Viktoria", viktoria_tg),
                ("Iwona", iwona_tg),
                ("Boris", boris_tg),
                ("Jan", jan_tg),
            ]
        )

        staff_keep_ids: set[int] = set()
        for member in (
            _upsert_staff(
                session,
                telegram_id=viktoria_tg,
                name=viktoria_name,
                role=StaffRole.therapist,
            ),
            _upsert_staff(
                session,
                telegram_id=iwona_tg,
                name=iwona_name,
                role=StaffRole.therapist,
            ),
            _upsert_staff(
                session,
                telegram_id=boris_tg,
                name=boris_name,
                role=StaffRole.superuser,
            ),
            _upsert_staff(
                session,
                telegram_id=jan_tg,
                name=jan_name,
                role=StaffRole.superuser,
            ),
        ):
            staff_keep_ids.add(member.id)

        stale_staff = session.scalars(
            select(StaffMember).where(StaffMember.id.not_in(staff_keep_ids))
        ).all()
        for stale in stale_staff:
            stale.active = False
            print(f"Деактивирован staff: {stale.name} (id={stale.id})")

        session.commit()
        print("OK: сиды применены.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
