"""Таблица services — услуги клиники."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    # Numeric — деньги без сюрпризов float
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    def __repr__(self) -> str:
        return f"Service(id={self.id!r}, name={self.name!r}, price={self.price!r})"
