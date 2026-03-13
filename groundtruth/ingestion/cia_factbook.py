"""CIA Factbook ingestion client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import httpx

FACTBOOK_URL = (
    "https://raw.githubusercontent.com/iancoleman/cia_world_factbook_api/master/data/factbook.json"
)

COUNTRY_NAME_TO_ISO: dict[str, str] = {
    "united states": "US",
    "china": "CN",
    "iran": "IR",
    "ukraine": "UA",
    "russia": "RU",
    "united kingdom": "GB",
    "united_states": "US",
}


@dataclass
class CountryProfile:
    iso_code: str
    name: str
    government: dict
    military: dict
    geography: dict
    economy: dict
    demographics: dict
    transnational_issues: dict
    international_orgs: list[str]
    raw_data: dict


class CIAFactbookIngestor:
    """Load and normalize CIA Factbook country profiles."""

    def __init__(
        self,
        cache_path: str | Path | None = None,
        http_client: httpx.AsyncClient | None = None,
        source_url: str = FACTBOOK_URL,
    ) -> None:
        self.cache_path = Path(
            cache_path or Path(__file__).parent.parent.parent / ".cache" / "cia_factbook.json"
        )
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._http_client = http_client
        self.source_url = source_url

    async def load_dataset(self, force_refresh: bool = False) -> dict:
        if self.cache_path.exists() and not force_refresh:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))

        async with self._get_client() as client:
            response = await client.get(self.source_url)
            response.raise_for_status()
            payload = response.json()

        self.cache_path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    async def get_country_profile(
        self, iso_code: str | None = None, country_name: str | None = None
    ) -> CountryProfile:
        if not iso_code and not country_name:
            raise ValueError("Provide iso_code or country_name")

        dataset = await self.load_dataset()
        raw_country = self._find_country(dataset, iso_code=iso_code, country_name=country_name)
        if raw_country is None:
            raise ValueError(f"Country not found: iso={iso_code} name={country_name}")

        name = (
            raw_country.get("name")
            or raw_country.get("country_name")
            or country_name
            or iso_code
            or "unknown"
        )
        normalized_iso = self.normalize_country_to_iso(name, fallback=iso_code)

        return CountryProfile(
            iso_code=normalized_iso,
            name=name,
            government=self._get_section(raw_country, "government"),
            military=self._get_section(raw_country, "military_and_security"),
            geography=self._get_section(raw_country, "geography"),
            economy=self._get_section(raw_country, "economy"),
            demographics=self._get_section(raw_country, "people_and_society")
            or self._get_section(raw_country, "people"),
            transnational_issues=self._get_section(raw_country, "transnational_issues"),
            international_orgs=self._extract_orgs(raw_country),
            raw_data=raw_country,
        )

    async def load_all_profiles(self) -> list[CountryProfile]:
        dataset = await self.load_dataset()
        countries = self._collect_countries(dataset)
        profiles: list[CountryProfile] = []
        for country in countries:
            name = country.get("name") or country.get("country_name") or "unknown"
            profiles.append(
                CountryProfile(
                    iso_code=self.normalize_country_to_iso(name),
                    name=name,
                    government=self._get_section(country, "government"),
                    military=self._get_section(country, "military_and_security"),
                    geography=self._get_section(country, "geography"),
                    economy=self._get_section(country, "economy"),
                    demographics=self._get_section(country, "people_and_society")
                    or self._get_section(country, "people"),
                    transnational_issues=self._get_section(country, "transnational_issues"),
                    international_orgs=self._extract_orgs(country),
                    raw_data=country,
                )
            )
        return profiles

    def normalize_country_to_iso(self, country_name: str, fallback: str | None = None) -> str:
        key = country_name.strip().lower()
        if key in COUNTRY_NAME_TO_ISO:
            return COUNTRY_NAME_TO_ISO[key]
        if fallback:
            return fallback.upper()
        guess = "".join(part[0] for part in key.split()[:2]).upper()
        return guess or "XX"

    def _find_country(
        self, dataset: dict, iso_code: str | None, country_name: str | None
    ) -> dict | None:
        countries = self._collect_countries(dataset)
        iso = iso_code.upper() if iso_code else None
        target_name = country_name.strip().lower() if country_name else None

        for country in countries:
            name = (country.get("name") or country.get("country_name") or "").strip().lower()
            country_key = str(country.get("country_key", "")).strip().lower()
            normalized_iso = self.normalize_country_to_iso(name)
            if iso and normalized_iso == iso:
                return country
            if iso and self.normalize_country_to_iso(country_key) == iso:
                return country
            if target_name and name == target_name:
                return country
        return None

    def _collect_countries(self, dataset: dict) -> list[dict]:
        if isinstance(dataset, list):
            return [item for item in dataset if isinstance(item, dict)]

        if "countries" in dataset and isinstance(dataset["countries"], list):
            return [item for item in dataset["countries"] if isinstance(item, dict)]
        if "countries" in dataset and isinstance(dataset["countries"], dict):
            countries: list[dict] = []
            for key, value in dataset["countries"].items():
                if not isinstance(value, dict):
                    continue
                data = value.get("data") if isinstance(value.get("data"), dict) else value
                if isinstance(data, dict):
                    country_data = dict(data)
                    country_data["country_key"] = key
                    countries.append(country_data)
            return countries

        countries: list[dict] = []
        for value in dataset.values() if isinstance(dataset, dict) else []:
            if isinstance(value, list):
                countries.extend(item for item in value if isinstance(item, dict))
            elif isinstance(value, dict):
                countries.extend(item for item in value.values() if isinstance(item, dict))
        return countries

    def _get_section(self, country: dict, key: str) -> dict:
        section = country.get(key, {})
        return section if isinstance(section, dict) else {}

    def _extract_orgs(self, country: dict) -> list[str]:
        section = self._get_section(country, "government")
        memberships = section.get("international_organization_participation")
        if isinstance(memberships, str):
            return [item.strip() for item in memberships.split(",") if item.strip()]
        if isinstance(memberships, list):
            return [str(item).strip() for item in memberships if str(item).strip()]
        return []

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
