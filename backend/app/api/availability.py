"""GET /api/availability."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.models import Therapist
from app.schemas.availability import AvailabilityOut
from app.services.availability import generate_time_slots

router = APIRouter(prefix="/availability", tags=["availability"])


@router.get("", response_model=AvailabilityOut)
def get_availability(
    db: DbSession,
    therapist_id: int = Query(..., ge=1),
    booking_date: date = Query(..., alias="date"),
) -> AvailabilityOut:
    """Свободные слоты: пн–чт 11–18, пт 11–17, шаг 30 мин (без проверки занятых)."""
    therapist = db.get(Therapist, therapist_id)
    if therapist is None or not therapist.active:
        raise HTTPException(status_code=404, detail="Терапевт не найден или неактивен")

    return AvailabilityOut(
        therapist_id=therapist_id,
        date=booking_date,
        slots=generate_time_slots(booking_date),
    )
