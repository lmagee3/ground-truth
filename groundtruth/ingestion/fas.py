"""FAS nuclear data loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FASIngestor:
    """Loads static nuclear arsenal data for the nine nuclear states."""

    def __init__(self, data_path: str | Path | None = None) -> None:
        self.data_path = Path(
            data_path or Path(__file__).parent.parent.parent / "data" / "fas_nuclear.json"
        )

    def load_data(self) -> dict[str, Any]:
        if not self.data_path.exists():
            return {}
        return json.loads(self.data_path.read_text(encoding="utf-8"))

    def get_country_data(self, iso_code: str) -> dict[str, Any]:
        data = self.load_data()
        return data.get(iso_code.upper(), {})
