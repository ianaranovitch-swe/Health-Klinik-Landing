"""GET /api/services."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession
from app.models import Service
from app.schemas.service import ServiceOut

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceOut])
def list_services(db: DbSession) -> list[Service]:
    """Список услуг."""
    stmt = select(Service).order_by(Service.name.asc())
    return list(db.scalars(stmt).all())
