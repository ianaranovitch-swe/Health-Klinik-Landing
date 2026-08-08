"""Таблица staff_members — кто может смотреть брони в Telegram-боте."""

from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StaffRole(str, enum.Enum):
    """Роль в боте: терапевт или суперпользователь (контроль процесса)."""

    therapist = "therapist"
    superuser = "superuser"


class StaffMember(Base):
    __tablename__ = "staff_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[StaffRole] = mapped_column(
        Enum(
            StaffRole,
            name="staff_role",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        index=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    def __repr__(self) -> str:
        return (
            f"StaffMember(id={self.id!r}, name={self.name!r}, "
            f"role={self.role!r}, active={self.active!r})"
        )
