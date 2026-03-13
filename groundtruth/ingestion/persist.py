"""Database persistence helpers for ingestion and synthesized reports."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from groundtruth.models import (
    ApprovedSource,
    ContextReport,
    Country,
    Event,
    Indicator,
    parse_approved_sources_markdown,
)


class DatabasePersister:
    """Async persistence layer with safe no-op behavior when DB is unavailable."""

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL", "")
        self.engine = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        if self.database_url:
            async_url = self._to_async_url(self.database_url)
            self.engine = create_async_engine(async_url, future=True)
            self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    @property
    def enabled(self) -> bool:
        return self.session_factory is not None

    async def seed_approved_sources(self, markdown_path: str | Path | None = None) -> int:
        if not self.enabled:
            return 0
        source_path = Path(
            markdown_path or Path(__file__).parent.parent.parent / "docs" / "APPROVED_SOURCES.md"
        )
        parsed = parse_approved_sources_markdown(source_path)
        count = 0

        async with self.session_factory() as session:
            for item in parsed:
                existing = await session.get(ApprovedSource, item["domain"])
                if existing:
                    continue
                session.add(
                    ApprovedSource(
                        domain=str(item["domain"]),
                        organization=str(item["organization"]),
                        source_type=str(item["source_type"]),
                        reliability_score=int(item["reliability_score"]),
                        notes=str(item["notes"]),
                    )
                )
                count += 1
            await session.commit()

        return count

    async def upsert_country_bundle(self, country_payload: dict[str, Any]) -> None:
        if not self.enabled:
            return

        country = country_payload.get("country", {})
        iso = str(country.get("iso_code") or "").upper()
        if not iso:
            return

        async with self.session_factory() as session:
            db_country = await session.get(Country, iso)
            if not db_country:
                db_country = Country(
                    iso_code=iso,
                    name=str(country.get("name") or iso),
                    region=None,
                    factbook_data=country_payload.get("factbook", {}),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(db_country)
            else:
                db_country.name = str(country.get("name") or db_country.name)
                db_country.factbook_data = country_payload.get("factbook", {})
                db_country.updated_at = datetime.now(timezone.utc)

            # Replace indicators for this country/source to keep latest fetch simple.
            existing = await session.execute(select(Indicator).where(Indicator.country_code == iso))
            for row in existing.scalars().all():
                await session.delete(row)

            for indicator_id, points in country_payload.get("worldbank", {}).items():
                for point in points:
                    session.add(
                        Indicator(
                            country_code=iso,
                            indicator_id=indicator_id,
                            indicator_name=str(point.get("indicator_name") or indicator_id),
                            year=int(point.get("year")),
                            value=(
                                float(point.get("value"))
                                if point.get("value") is not None
                                else None
                            ),
                            source="worldbank",
                            fetched_at=datetime.now(timezone.utc),
                        )
                    )

            await session.commit()

    async def persist_events(self, events: list[dict[str, Any]]) -> int:
        if not self.enabled:
            return 0

        inserted = 0
        async with self.session_factory() as session:
            for event in events:
                source = str(event.get("source") or "")
                source_id = str(event.get("source_id") or "")
                if not source or not source_id:
                    continue

                event_pk = f"{source}:{source_id}"
                existing = await session.get(Event, event_pk)
                if existing:
                    continue

                event_date = self._parse_event_date(event.get("date"))
                session.add(
                    Event(
                        id=event_pk,
                        source=source,
                        source_id=source_id,
                        event_type=str(event.get("event_type") or "unknown"),
                        date=event_date,
                        country_code=event.get("country_code"),
                        latitude=event.get("latitude"),
                        longitude=event.get("longitude"),
                        description=event.get("description"),
                        actors=event.get("actors") or [],
                        source_url=event.get("source_url"),
                        raw_data=event.get("raw_data") or {},
                    )
                )
                inserted += 1

            await session.commit()

        return inserted

    async def persist_context_report(
        self,
        query: str,
        depth: str,
        content: dict[str, Any],
        verification_status: str = "pending",
        model_used: str | None = None,
    ) -> None:
        if not self.enabled:
            return

        async with self.session_factory() as session:
            session.add(
                ContextReport(
                    query=query,
                    depth=depth,
                    content=content,
                    sources_cited=content.get("sources_cited", []),
                    verification_status=verification_status,
                    verification_report={},
                    model_used=model_used,
                    generated_at=datetime.now(timezone.utc),
                    cache_expires=None,
                )
            )
            await session.commit()

    def _to_async_url(self, url: str) -> str:
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    def _parse_event_date(self, value: Any):
        if hasattr(value, "year"):
            return value
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    return datetime.strptime(value[:10], fmt).date()
                except ValueError:
                    continue
        return datetime.now(timezone.utc).date()
