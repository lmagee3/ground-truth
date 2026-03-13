"""Seed top-country baseline data into the database."""

from __future__ import annotations

import asyncio

from groundtruth.ingestion.persist import DatabasePersister


async def main() -> None:
    persister = DatabasePersister()
    if not persister.enabled:
        print("DATABASE_URL not configured; skipping seed")
        return
    count = await persister.seed_approved_sources()
    print(f"Seeded approved sources: {count}")


if __name__ == "__main__":
    asyncio.run(main())
