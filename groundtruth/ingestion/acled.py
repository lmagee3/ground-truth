"""ACLED ingestion client with OAuth2 token management."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

TOKEN_URL = "https://acleddata.com/oauth/token"
DATA_URL = "https://acleddata.com/acled/read"

COUNTRY_TO_ISO: dict[str, str] = {
    "united states": "US",
    "ukraine": "UA",
    "russia": "RU",
    "china": "CN",
    "iran": "IR",
    "georgia": "GE",
    "armenia": "AM",
    "israel": "IL",
    "palestine": "PS",
}


class ACLEDIngestor:
    """Async ACLED client with credential-aware graceful degradation."""

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        http_client: httpx.AsyncClient | None = None,
        username: str | None = None,
        password: str | None = None,
        request_interval_seconds: float = 2.0,
        token_url: str = TOKEN_URL,
        data_url: str = DATA_URL,
    ) -> None:
        self.cache_dir = Path(cache_dir or Path(__file__).parent.parent.parent / ".cache" / "acled")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._http_client = http_client
        self.username = username or os.getenv("ACLED_USERNAME")
        self.password = password or os.getenv("ACLED_PASSWORD")
        self.token_url = token_url
        self.data_url = data_url
        self._request_interval = request_interval_seconds
        self._last_request_ts = 0.0
        self._rate_lock = asyncio.Lock()

        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: datetime | None = None

    @property
    def configured(self) -> bool:
        return bool(self.username and self.password)

    async def fetch_events(
        self,
        country: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        event_type: str | None = None,
        year: int | None = None,
        limit: int = 200,
        max_pages: int = 3,
    ) -> list[dict[str, Any]]:
        if not self.configured:
            return []

        params: dict[str, Any] = {"_format": "json", "limit": limit}
        if country:
            params["country"] = country
        if start_date and end_date:
            params["event_date"] = f"{start_date}|{end_date}"
            params["event_date_where"] = "BETWEEN"
        if event_type:
            params["event_type"] = event_type
        if year:
            params["year"] = year

        cache_key = self._cache_key(params)
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            return self._parse_events(payload)

        try:
            token = await self._get_access_token()
        except Exception:  # noqa: BLE001
            return []  # Graceful skip when all token acquisition paths fail
        headers = {"Authorization": f"Bearer {token}"}

        combined: list[dict[str, Any]] = []
        async with self._get_client() as client:
            for page in range(1, max_pages + 1):
                page_params = dict(params)
                page_params["page"] = page
                await self._wait_for_rate_limit()
                response = await client.get(self.data_url, params=page_params, headers=headers)
                if response.status_code == 401:
                    try:
                        token = await self._get_access_token(force_refresh=True)
                    except Exception:  # noqa: BLE001
                        break  # Can't re-auth, return whatever we have so far
                    headers = {"Authorization": f"Bearer {token}"}
                    response = await client.get(self.data_url, params=page_params, headers=headers)

                response.raise_for_status()
                payload = response.json()
                data_rows = payload.get("data", []) if isinstance(payload, dict) else []
                if not isinstance(data_rows, list):
                    break
                combined.extend(data_rows)
                if len(data_rows) < limit:
                    break

        wrapped = {"data": combined}
        cache_path.write_text(json.dumps(wrapped), encoding="utf-8")
        return self._parse_events(wrapped)

    async def _get_access_token(self, force_refresh: bool = False) -> str:
        now = datetime.utcnow()
        if (
            not force_refresh
            and self._access_token
            and self._expires_at
            and now < (self._expires_at - timedelta(minutes=5))
        ):
            return self._access_token

        if self._refresh_token:
            refreshed = await self._refresh_access_token()
            if refreshed:
                return refreshed

        return await self._password_grant_token()

    async def _password_grant_token(self) -> str:
        if not self.configured:
            raise RuntimeError("ACLED credentials not configured")

        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
            "client_id": "acled",
        }
        async with self._get_client() as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            payload = response.json()
        return self._set_tokens(payload)

    async def _refresh_access_token(self) -> str | None:
        data = {
            "refresh_token": self._refresh_token,
            "grant_type": "refresh_token",
            "client_id": "acled",
        }
        try:
            async with self._get_client() as client:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                payload = response.json()
            return self._set_tokens(payload)
        except httpx.HTTPError:
            return None

    def _set_tokens(self, payload: dict[str, Any]) -> str:
        access = payload.get("access_token")
        if not access:
            raise RuntimeError("ACLED token response missing access_token")
        self._access_token = access
        self._refresh_token = payload.get("refresh_token", self._refresh_token)
        expires = int(payload.get("expires_in", 86400))
        self._expires_at = datetime.utcnow() + timedelta(seconds=expires)
        return access

    def _parse_events(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        events: list[dict[str, Any]] = []

        for row in rows:
            if not isinstance(row, dict):
                continue
            row_country = str(row.get("country") or "").strip()
            actors = [
                str(row.get("assoc_actor_1") or "").strip(),
                str(row.get("assoc_actor_2") or "").strip(),
            ]
            actors = [actor for actor in actors if actor]
            events.append(
                {
                    "source": "acled",
                    "source_id": str(row.get("event_id_cnty") or row.get("event_id_no_cnty") or ""),
                    "event_type": row.get("event_type") or "unknown",
                    "date": self._parse_date(row.get("event_date")).isoformat(),
                    "country_code": self.country_to_iso(row_country),
                    "latitude": self._to_float(row.get("latitude")),
                    "longitude": self._to_float(row.get("longitude")),
                    "description": row.get("notes") or row.get("sub_event_type") or "",
                    "actors": actors,
                    "source_url": "https://acleddata.com/data-export-tool/",
                    "raw_data": row,
                }
            )

        return events

    def country_to_iso(self, country: str) -> str | None:
        key = country.strip().lower()
        if not key:
            return None
        return COUNTRY_TO_ISO.get(key)

    def _cache_key(self, params: dict[str, Any]) -> str:
        blob = json.dumps(params, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _parse_date(self, value: str | None) -> date:
        if not value:
            return datetime.utcnow().date()
        for fmt in ("%Y-%m-%d", "%d %B %Y", "%d-%b-%y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return datetime.utcnow().date()

    def _to_float(self, value: Any) -> float | None:
        try:
            return None if value in (None, "") else float(value)
        except (TypeError, ValueError):
            return None

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
