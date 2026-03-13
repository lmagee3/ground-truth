"""Download helper for SIPRI CSV datasets.

Set SIPRI download URLs with env vars if you have direct CSV links:
  SIPRI_MILEX_CSV_URL
  SIPRI_ARMS_CSV_URL
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "sipri"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MILEX_URL = os.getenv("SIPRI_MILEX_CSV_URL", "")
ARMS_URL = os.getenv("SIPRI_ARMS_CSV_URL", "")


def _download(url: str, output: Path) -> None:
    if not url:
        print(f"Skipping {output.name}: URL is not configured")
        return
    response = httpx.get(url, timeout=60.0)
    response.raise_for_status()
    output.write_bytes(response.content)
    print(f"Downloaded {output}")


def main() -> None:
    _download(MILEX_URL, DATA_DIR / "military_expenditure.csv")
    _download(ARMS_URL, DATA_DIR / "arms_transfers.csv")


if __name__ == "__main__":
    main()
