"""GET /api/therapists."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.models import Service, Therapist
from app.schemas.therapist import TherapistOut

router = APIRouter(prefix="/therapists", tags=["therapists"])


@router.get("", response_model=list[TherapistOut])
def list_active_therapists(
    db: DbSession,
    service_id: int | None = Query(
        default=None,
        ge=1,
        description="Если задан — только терапевты, оказывающие эту услугу",
    ),
) -> list[Therapist]:
    """Список активных терапевтов (опционально по услуге)."""
    if service_id is None:
        stmt = (
            select(Therapist)
            .where(Therapist.active.is_(True))
            .order_by(Therapist.name.asc())
        )
        return list(db.scalars(stmt).all())

    service = db.scalar(
        select(Service)
        .options(selectinload(Service.therapists))
        .where(Service.id == service_id)
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    active = [t for t in service.therapists if t.active]
    return sorted(active, key=lambda t: t.name)
