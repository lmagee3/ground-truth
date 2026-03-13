"""SIPRI CSV ingestion for military spending and arms transfers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

COUNTRY_TO_ISO: dict[str, str] = {
    "united states": "US",
    "russia": "RU",
    "china": "CN",
    "india": "IN",
    "ukraine": "UA",
    "united kingdom": "GB",
    "france": "FR",
}


class SIPRIIngestor:
    """Read SIPRI datasets from local CSV files."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir or Path(__file__).parent.parent.parent / "data" / "sipri")
        self.military_csv = self.data_dir / "military_expenditure.csv"
        self.arms_csv = self.data_dir / "arms_transfers.csv"

    def load_military_expenditure(self) -> list[dict[str, Any]]:
        if not self.military_csv.exists():
            return []
        return self._parse_military_csv(self.military_csv)

    def load_arms_transfers(self) -> list[dict[str, Any]]:
        if not self.arms_csv.exists():
            return []
        return self._parse_arms_csv(self.arms_csv)

    def get_country_military_data(
        self,
        iso_code: str,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        iso = iso_code.upper()
        military = [
            row
            for row in self.load_military_expenditure()
            if row.get("country_code") == iso
            and self._in_range(row.get("year"), start_year, end_year)
        ]
        arms = [
            row
            for row in self.load_arms_transfers()
            if row.get("country_code") == iso
            and self._in_range(row.get("year"), start_year, end_year)
        ]
        return {"military_expenditure": military, "arms_transfers": arms}

    def country_to_iso(self, country: str) -> str | None:
        return COUNTRY_TO_ISO.get(country.strip().lower())

    def _parse_military_csv(self, path: Path) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                iso = self.country_to_iso(str(row.get("country") or ""))
                rows.append(
                    {
                        "country_code": iso,
                        "country": row.get("country"),
                        "year": self._to_int(row.get("year")),
                        "indicator_id": "SIPRI.MIL.EXP.USD",
                        "indicator_name": "Military expenditure (current USD)",
                        "value": self._to_float(row.get("military_expenditure_usd")),
                        "pct_gdp": self._to_float(row.get("military_expenditure_pct_gdp")),
                        "source": "sipri",
                    }
                )
        return rows

    def _parse_arms_csv(self, path: Path) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                iso = self.country_to_iso(str(row.get("country") or ""))
                rows.append(
                    {
                        "country_code": iso,
                        "country": row.get("country"),
                        "year": self._to_int(row.get("year")),
                        "exports_tiv": self._to_float(row.get("exports_tiv")),
                        "imports_tiv": self._to_float(row.get("imports_tiv")),
                        "source": "sipri",
                    }
                )
        return rows

    def _in_range(self, year: int | None, start_year: int | None, end_year: int | None) -> bool:
        if year is None:
            return False
        if start_year is not None and year < start_year:
            return False
        if end_year is not None and year > end_year:
            return False
        return True

    def _to_float(self, value: Any) -> float | None:
        try:
            return None if value in (None, "") else float(value)
        except (TypeError, ValueError):
            return None

    def _to_int(self, value: Any) -> int | None:
        try:
            return None if value in (None, "") else int(value)
        except (TypeError, ValueError):
            return None
