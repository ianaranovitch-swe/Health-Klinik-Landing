"""ORM-модели. Импорт всех таблиц нужен для Alembic autogenerate."""

from app.models.associations import therapist_services
from app.models.base import Base
from app.models.booking import Booking, BookingStatus
from app.models.client import Client
from app.models.service import Service
from app.models.staff import StaffMember, StaffRole
from app.models.therapist import Therapist

__all__ = [
    "Base",
    "Booking",
    "BookingStatus",
    "Client",
    "Service",
    "StaffMember",
    "StaffRole",
    "Therapist",
    "therapist_services",
]
