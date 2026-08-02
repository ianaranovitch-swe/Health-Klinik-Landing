"""GET /api/therapists."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession
from app.models import Therapist
from app.schemas.therapist import TherapistOut

router = APIRouter(prefix="/therapists", tags=["therapists"])


@router.get("", response_model=list[TherapistOut])
def list_active_therapists(db: DbSession) -> list[Therapist]:
    """Список активных терапевтов."""
    stmt = (
        select(Therapist)
        .where(Therapist.active.is_(True))
        .order_by(Therapist.name.asc())
    )
    return list(db.scalars(stmt).all())
