"""Схемы доступности слотов."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class AvailabilityOut(BaseModel):
    therapist_id: int
    date: date
    slots: list[str] = Field(description="Свободные слоты HH:MM")
