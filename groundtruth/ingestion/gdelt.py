"""GDELT DOC 2.0 ingestion client."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
SUPPORTED_MODES = {"artlist", "timelinevol", "tonechart"}


@dataclass
class GDELTEvent:
    source: str
    source_id: str
    event_type: str
    date: date
    country_code: str | None
    description: str
    source_url: str
    raw_data: dict[str, Any]


class GDELTIngestor:
    """Async GDELT client with cache + rate limiting."""

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        http_client: httpx.AsyncClient | None = None,
        request_interval_seconds: float = 5.0,
    ) -> None:
        self.cache_dir = Path(cache_dir or Path(__file__).parent.parent.parent / ".cache" / "gdelt")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._http_client = http_client
        self._request_interval = request_interval_seconds
        self._last_request_ts = 0.0
        self._rate_lock = asyncio.Lock()

    async def query(
        self,
        query: str,
        mode: str = "artlist",
        maxrecords: int = 50,
        start_date: str | None = None,
        end_date: str | None = None,
        country_code: str | None = None,
    ) -> dict[str, Any]:
        if mode not in SUPPORTED_MODES:
            raise ValueError(f"Unsupported GDELT mode: {mode}")

        params: dict[str, Any] = {
            "query": query,
            "mode": mode,
            "format": "json",
            "maxrecords": maxrecords,
        }
        if start_date:
            params["startdatetime"] = self._to_gdelt_datetime(start_date, is_start=True)
        if end_date:
            params["enddatetime"] = self._to_gdelt_datetime(end_date, is_start=False)
        if country_code:
            params["query"] = f"{query} sourcecountry:{country_code.upper()}"

        cache_key = self._cache_key(params)
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        async with self._get_client() as client:
            await self._wait_for_rate_limit()
            response = await client.get(GDELT_DOC_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        cache_path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    async def fetch_events(
        self,
        query: str,
        maxrecords: int = 50,
        start_date: str | None = None,
        end_date: str | None = None,
        country_code: str | None = None,
    ) -> list[dict[str, Any]]:
        payload = await self.query(
            query=query,
            mode="artlist",
            maxrecords=maxrecords,
            start_date=start_date,
            end_date=end_date,
            country_code=country_code,
        )
        return [event.__dict__ for event in self.parse_artlist(payload, country_code=country_code)]

    def parse_artlist(
        self,
        payload: dict[str, Any],
        country_code: str | None = None,
    ) -> list[GDELTEvent]:
        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        target_country = country_code.upper() if country_code else None
        events: list[GDELTEvent] = []

        for article in articles:
            if not isinstance(article, dict):
                continue
            source_country = (article.get("sourcecountry") or "").upper() or None
            if target_country and source_country and source_country != target_country:
                continue

            date_value = self._parse_date(article.get("seendate") or article.get("date"))
            title = article.get("title") or article.get("url") or "GDELT Article"
            url = article.get("url") or ""
            source_id = (
                hashlib.sha256(url.encode("utf-8")).hexdigest()
                if url
                else hashlib.sha256(json.dumps(article, sort_keys=True).encode("utf-8")).hexdigest()
            )

            events.append(
                GDELTEvent(
                    source="gdelt",
                    source_id=source_id,
                    event_type=article.get("domain") or "article",
                    date=date_value,
                    country_code=source_country,
                    description=title,
                    source_url=url,
                    raw_data=article,
                )
            )

        return events

    def parse_timeline(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        timeline = payload.get("timeline", []) if isinstance(payload, dict) else []
        return [point for point in timeline if isinstance(point, dict)]

    def parse_tonechart(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        tone = payload.get("timeline", []) if isinstance(payload, dict) else []
        return [point for point in tone if isinstance(point, dict)]

    def _cache_key(self, params: dict[str, Any]) -> str:
        blob = json.dumps(params, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _to_gdelt_datetime(self, value: str, *, is_start: bool) -> str:
        dt = datetime.fromisoformat(value)
        if is_start:
            return dt.strftime("%Y%m%d000000")
        return dt.strftime("%Y%m%d235959")

    def _parse_date(self, value: str | None) -> date:
        if not value:
            return datetime.utcnow().date()
        for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return datetime.utcnow().date()

    async def _wait_for_rate_limit(self) -> None:
        async with self._rate_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_ts
            wait_for = self._request_interval - elapsed
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last_request_ts = time.monotonic()

    def _get_client(self):
        if self._http_client is not None:
            return _NoCloseClient(self._http_client)
        return httpx.AsyncClient(timeout=20.0)


class _NoCloseClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self.client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None
