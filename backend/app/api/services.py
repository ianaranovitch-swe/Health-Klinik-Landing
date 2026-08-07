"""GET /api/services."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.models import Service, Therapist
from app.schemas.service import ServiceOut

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceOut])
def list_services(
    db: DbSession,
    therapist_id: int | None = Query(
        default=None,
        ge=1,
        description="Если задан — только услуги этого терапевта",
    ),
) -> list[Service]:
    """Список услуг (только с привязанным активным терапевтом, если без фильтра)."""
    if therapist_id is not None:
        therapist = db.scalar(
            select(Therapist)
            .options(selectinload(Therapist.services))
            .where(Therapist.id == therapist_id)
        )
        if therapist is None or not therapist.active:
            raise HTTPException(
                status_code=404, detail="Терапевт не найден или неактивен"
            )
        return sorted(therapist.services, key=lambda s: s.name)

    # В форме бронирования не показываем «сиротские» услуги без terapeutа
    stmt = (
        select(Service)
        .where(Service.therapists.any(Therapist.active.is_(True)))
        .order_by(Service.name.asc())
    )
    return list(db.scalars(stmt).unique().all())
