"""Связь many-to-many: какой терапевт какие услуги оказывает."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, Table

from app.models.base import Base

therapist_services = Table(
    "therapist_services",
    Base.metadata,
    Column(
        "therapist_id",
        Integer,
        ForeignKey("therapists.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "service_id",
        Integer,
        ForeignKey("services.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
