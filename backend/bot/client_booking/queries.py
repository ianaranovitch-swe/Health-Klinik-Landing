"""Запросы к БД — те же правила, что у REST API."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Service, Therapist


def list_bookable_services(db: Session) -> list[Service]:
    """Услуги с хотя бы одним активным терапевтом."""
    stmt = (
        select(Service)
        .where(Service.therapists.any(Therapist.active.is_(True)))
        .order_by(Service.name.asc())
    )
    return list(db.scalars(stmt).unique().all())


def list_therapists_for_service(db: Session, service_id: int) -> list[Therapist]:
    """Активные терапевты для выбранной услуги."""
    service = db.scalar(
        select(Service)
        .options(selectinload(Service.therapists))
        .where(Service.id == service_id)
    )
    if service is None:
        return []
    active = [t for t in service.therapists if t.active]
    return sorted(active, key=lambda t: t.name)
