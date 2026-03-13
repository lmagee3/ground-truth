"""Ground Truth API — Geopolitical Context Engine."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from groundtruth import __version__
from groundtruth.ingestion.cia_factbook import CIAFactbookIngestor
from groundtruth.ingestion.worldbank import INDICATOR_IDS, WorldBankIngestor

app = FastAPI(
    title="Ground Truth",
    description="Open-source geopolitical context engine. The intelligence briefing behind the radar blip.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

worldbank = WorldBankIngestor()
factbook = CIAFactbookIngestor()

REGION_COUNTRIES: dict[str, list[str]] = {
    "north-america": ["US", "CA", "MX"],
    "europe": ["GB", "DE", "FR", "UA"],
    "asia": ["CN", "JP", "IN", "KR"],
    "middle-east": ["IR", "IQ", "IL", "SA"],
}


@app.get("/")
async def root():
    return {
        "name": "Ground Truth",
        "version": __version__,
        "status": "operational",
        "description": "Geopolitical context engine — primary sources, no spin.",
        "docs": "/docs",
    }


@app.get("/v1/health")
async def health():
    return {
        "status": "ok",
        "sources": {
            "worldbank": _cache_status(worldbank.cache_dir),
            "cia_factbook": _cache_status(factbook.cache_path),
        },
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/v1/country/{iso_code}")
async def get_country(iso_code: str, start_year: int = 2000, end_year: int = 2026):
    iso = iso_code.upper()

    profile_payload = {
        "government": {},
        "military": {},
        "geography": {},
        "economy": {},
        "demographics": {},
        "transnational_issues": {},
        "international_orgs": [],
    }
    country_name = iso

    try:
        profile = await factbook.get_country_profile(iso_code=iso)
        country_name = profile.name
        profile_payload = {
            "government": profile.government,
            "military": profile.military,
            "geography": profile.geography,
            "economy": profile.economy,
            "demographics": profile.demographics,
            "transnational_issues": profile.transnational_issues,
            "international_orgs": profile.international_orgs,
        }
    except Exception:
        if len(iso) != 2 or not iso.isalpha():
            raise HTTPException(status_code=404, detail=f"Invalid country code: {iso}")

    indicators_payload: dict[str, list[dict]] = {}
    try:
        indicators = await worldbank.fetch_country_indicators(
            iso, start_year=start_year, end_year=end_year
        )
        indicators_payload = {
            indicator: [point.__dict__ for point in points if point.value is not None]
            for indicator, points in indicators.items()
        }
    except Exception:
        indicators_payload = {}

    return {
        "country": {"iso_code": iso, "name": country_name},
        "factbook": profile_payload,
        "worldbank": indicators_payload,
    }


@app.get("/v1/context/{query}")
async def get_context(
    query: str,
    depth: str = Query("standard", enum=["brief", "standard", "comprehensive"]),
    region: str | None = None,
    start_year: int = 2000,
    end_year: int = 2026,
):
    iso = _to_iso(query)
    try:
        country_data = await get_country(iso, start_year=start_year, end_year=end_year)
    except HTTPException:
        country_data = {
            "country": {"iso_code": iso, "name": query},
            "factbook": {},
            "worldbank": {},
        }
    return {
        "query": query,
        "depth": depth,
        "region": region,
        "country": country_data["country"],
        "context": {
            "factbook": country_data["factbook"],
            "worldbank": country_data["worldbank"],
        },
        "sources": [
            "https://api.worldbank.org/v2/",
            "https://www.cia.gov/the-world-factbook/",
        ],
    }


@app.get("/v1/timeline/{region}")
async def get_timeline(
    region: str,
    start_year: int = 2000,
    end_year: int = 2026,
    categories: str | None = None,
):
    countries = REGION_COUNTRIES.get(region.lower())
    if not countries:
        raise HTTPException(status_code=404, detail=f"Unsupported region: {region}")

    include = set((categories or "").split(",")) if categories else set(INDICATOR_IDS)
    timeline: dict[str, dict[str, list[dict]]] = {}
    for iso in countries:
        try:
            indicators = await worldbank.fetch_country_indicators(iso, start_year, end_year)
        except Exception:
            timeline[iso] = {}
            continue

        timeline[iso] = {
            indicator_id: [p.__dict__ for p in points if p.value is not None]
            for indicator_id, points in indicators.items()
            if indicator_id in include
        }

    return {
        "region": region,
        "start_year": start_year,
        "end_year": end_year,
        "categories": sorted(include),
        "timeline": timeline,
        "events": [],
    }


@app.get("/v1/briefing/{topic}")
async def get_briefing(
    topic: str,
    format: str = Query("full", enum=["full", "summary", "executive"]),
):
    return {
        "topic": topic,
        "format": format,
        "status": "not_implemented",
        "briefing": None,
    }


@app.get("/v1/compare/{event_a}/{event_b}")
async def compare_events(event_a: str, event_b: str):
    return {
        "event_a": event_a,
        "event_b": event_b,
        "status": "not_implemented",
        "parallels": [],
        "differences": [],
    }


@app.get("/v1/sources/{report_id}")
async def get_sources(report_id: str):
    return {
        "report_id": report_id,
        "status": "not_implemented",
        "sources": [],
    }


def _to_iso(query: str) -> str:
    q = query.strip()
    if len(q) == 2 and q.isalpha():
        return q.upper()
    return factbook.normalize_country_to_iso(q)


def _cache_status(path: Path) -> dict:
    target = Path(path)
    if not target.exists():
        return {"loaded": False, "freshness": None}

    mtime = datetime.fromtimestamp(target.stat().st_mtime, tz=timezone.utc).isoformat()
    return {"loaded": True, "freshness": mtime}
