"""Database models for Ground Truth."""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Country(Base):
    __tablename__ = "countries"

    iso_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    factbook_data: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    indicators: Mapped[list[Indicator]] = relationship(
        back_populates="country", cascade="all, delete-orphan"
    )


class Indicator(Base):
    __tablename__ = "indicators"
    __table_args__ = (
        UniqueConstraint("country_code", "indicator_id", "year", "source", name="uq_indicator_point"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.iso_code"), nullable=False)
    indicator_id: Mapped[str] = mapped_column(String(64), nullable=False)
    indicator_name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="worldbank")
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    country: Mapped[Country] = relationship(back_populates="indicators")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    actors: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)


class ContextReport(Base):
    __tablename__ = "context_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    depth: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    sources_cited: Mapped[list[str]] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    verification_report: Mapped[dict] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    model_used: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cache_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApprovedSource(Base):
    __tablename__ = "approved_sources"

    domain: Mapped[str] = mapped_column(String(255), primary_key=True)
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reliability_score: Mapped[int] = mapped_column(Integer, nullable=False, default=9)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


def parse_approved_sources_markdown(path: str | Path) -> list[dict[str, str | int]]:
    text = Path(path).read_text(encoding="utf-8")
    results: list[dict[str, str | int]] = []
    section = "institutional"

    for line in text.splitlines():
        if line.startswith("## US Government"):
            section = "us_gov"
        elif line.startswith("## International"):
            section = "international"
        elif line.startswith("## Allied"):
            section = "allied"
        elif line.startswith("## Academic"):
            section = "academic"
        elif line.startswith("## Geographic"):
            section = "geographic"
            continue

        match = re.match(
            r"^\|\s*([a-z0-9][\w.-]*\.[a-z]{2,})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$",
            line,
        )
        if not match:
            continue

        domain, org, notes = match.groups()
        results.append(
            {
                "domain": domain,
                "organization": org,
                "source_type": section,
                "reliability_score": 9,
                "notes": notes,
            }
        )

    deduped: dict[str, dict[str, str | int]] = {}
    for item in results:
        deduped[item["domain"]] = item
    return list(deduped.values())
