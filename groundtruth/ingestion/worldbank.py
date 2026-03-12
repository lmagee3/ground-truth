"""World Bank ingestion client."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"

INDICATOR_IDS: dict[str, str] = {
    "MS.MIL.XPND.GD.ZS": "Military expenditure (% of GDP)",
    "MS.MIL.XPND.CD": "Military expenditure (current USD)",
    "NY.GDP.MKTP.CD": "GDP (current USD)",
    "NY.GDP.MKTP.KD.ZG": "GDP growth (annual %)",
    "NE.TRD.GNFS.ZS": "Trade (% of GDP)",
    "SP.POP.TOTL": "Population total",
    "FP.CPI.TOTL.ZG": "Inflation (consumer prices, annual %)",
    "BN.CAB.XOKA.CD": "Current account balance",
}


@dataclass
class IndicatorPoint:
    country_code: str
    country_name: str
    indicator_id: str
    indicator_name: str
    year: int
    value: float | None


class WorldBankIngestor:
    """Async World Bank ingestion with local cache + client-side rate limiting."""

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        http_client: httpx.AsyncClient | None = None,
        request_interval_seconds: float = 1.0,
    ) -> None:
        self.cache_dir = Path(cache_dir or Path(__file__).parent.parent.parent / ".cache" / "worldbank")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._http_client = http_client
        self._request_interval = request_interval_seconds
        self._last_request_ts: float = 0.0
        self._rate_lock = asyncio.Lock()

    async def fetch_indicator(
        self,
        country_code: str,
        indicator_id: str,
        start_year: int = 2000,
        end_year: int = 2026,
    ) -> list[IndicatorPoint]:
        country = country_code.upper()
        if indicator_id not in INDICATOR_IDS:
            raise ValueError(f"Unsupported indicator id: {indicator_id}")

        cache_path = self._cache_path(country, indicator_id, start_year, end_year)
        if cache_path.exists():
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            return self._parse_indicator_response(country, indicator_id, data)

        url = f"{WORLD_BANK_BASE_URL}/country/{country}/indicator/{indicator_id}"
        params = {"format": "json", "date": f"{start_year}:{end_year}", "per_page": 5000}

        async with self._get_client() as client:
            await self._wait_for_rate_limit()
            response = await client.get(url, params=params)

        if response.status_code == 404:
            raise ValueError(f"Invalid country code: {country}")
        response.raise_for_status()

        payload = response.json()
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            message = payload[0].get("message")
            if message:
                raise ValueError(f"World Bank API error for {country}: {message}")

        cache_path.write_text(json.dumps(payload), encoding="utf-8")
        return self._parse_indicator_response(country, indicator_id, payload)

    async def fetch_country_indicators(
        self,
        country_code: str,
        start_year: int = 2000,
        end_year: int = 2026,
        indicator_ids: list[str] | None = None,
    ) -> dict[str, list[IndicatorPoint]]:
        target_indicators = indicator_ids or list(INDICATOR_IDS.keys())
        results: dict[str, list[IndicatorPoint]] = {}
        for indicator_id in target_indicators:
            points = await self.fetch_indicator(country_code, indicator_id, start_year, end_year)
            results[indicator_id] = points
        return results

    def _parse_indicator_response(
        self, country_code: str, indicator_id: str, payload: list[dict] | dict
    ) -> list[IndicatorPoint]:
        if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
            raise ValueError(f"Unexpected World Bank response format for {country_code} {indicator_id}")

        rows = payload[1]
        points: list[IndicatorPoint] = []
        for row in rows:
            year_raw = row.get("date")
            if year_raw is None:
                continue
            try:
                year = int(year_raw)
            except (TypeError, ValueError):
                continue

            value_raw = row.get("value")
            value = None if value_raw is None else float(value_raw)

            points.append(
                IndicatorPoint(
                    country_code=row.get("countryiso3code") or country_code,
                    country_name=(row.get("country") or {}).get("value") or country_code,
                    indicator_id=indicator_id,
                    indicator_name=((row.get("indicator") or {}).get("value") or INDICATOR_IDS[indicator_id]),
                    year=year,
                    value=value,
                )
            )

        points.sort(key=lambda p: p.year)
        return points

    def _cache_path(self, country_code: str, indicator_id: str, start_year: int, end_year: int) -> Path:
        name = f"{country_code}_{indicator_id}_{start_year}_{end_year}.json".replace("/", "_")
        return self.cache_dir / name

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
        return httpx.AsyncClient(timeout=30.0)


class _NoCloseClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self.client

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None
