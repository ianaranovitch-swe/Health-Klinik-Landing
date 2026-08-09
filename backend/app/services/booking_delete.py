"""Жёсткое удаление брони из БД (staff-бот)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Booking, BookingStatus
from app.models.staff import StaffMember, StaffRole
from app.services.staff_bookings import find_therapist_for_staff


class BookingDeleteError(Exception):
    """Нельзя удалить (нет прав / не найдена)."""


def get_deletable_booking_for_staff(
    db: Session,
    staff: StaffMember,
    booking_id: int,
) -> Booking:
    """Вернуть бронь, если staff может её удалить."""
    booking = db.scalar(
        select(Booking)
        .options(
            joinedload(Booking.client),
            joinedload(Booking.therapist),
        )
        .where(Booking.id == booking_id)
    )
    if booking is None:
        raise BookingDeleteError("Bokningen hittades inte.")

    if booking.status not in (
        BookingStatus.pending,
        BookingStatus.confirmed,
    ):
        raise BookingDeleteError(
            "Bara väntande eller bekräftade bokningar kan raderas."
        )

    if staff.role is StaffRole.superuser:
        return booking

    if staff.role is StaffRole.therapist:
        therapist = find_therapist_for_staff(db, staff)
        if therapist is None or booking.therapist_id != therapist.id:
            raise BookingDeleteError(
                "Du kan bara radera dina egna bokningar."
            )
        return booking

    raise BookingDeleteError("Ingen behörighet.")


def hard_delete_booking(db: Session, booking: Booking) -> None:
    """Полностью стереть строку брони из БД."""
    db.delete(booking)
    db.commit()
