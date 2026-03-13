"""Ground Truth API — Geopolitical Context Engine."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from groundtruth import __version__
from groundtruth.ingestion.acled import ACLEDIngestor
from groundtruth.ingestion.cia_factbook import CIAFactbookIngestor
from groundtruth.ingestion.fas import FASIngestor
from groundtruth.ingestion.gdelt import GDELTIngestor
from groundtruth.ingestion.persist import DatabasePersister
from groundtruth.ingestion.sipri import SIPRIIngestor
from groundtruth.ingestion.worldbank import INDICATOR_IDS, WorldBankIngestor
from groundtruth.synthesis.engine import ContextEngine

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
gdelt = GDELTIngestor()
acled = ACLEDIngestor()
sipri = SIPRIIngestor()
fas = FASIngestor()
engine = ContextEngine()
persister = DatabasePersister()

REGION_COUNTRIES: dict[str, list[str]] = {
    "north-america": ["US", "CA", "MX"],
    "europe": ["GB", "DE", "FR", "UA"],
    "asia": ["CN", "JP", "IN", "KR"],
    "middle-east": ["IR", "IQ", "IL", "SA"],
}


@app.on_event("startup")
async def startup_seed() -> None:
    if persister.enabled:
        try:
            await persister.seed_approved_sources()
        except Exception:
            pass


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
            "gdelt": _cache_status(gdelt.cache_dir),
            "acled": _cache_status(acled.cache_dir) | {"configured": acled.configured},
            "sipri": {"loaded": sipri.military_csv.exists() and sipri.arms_csv.exists()},
            "fas": {"loaded": fas.data_path.exists()},
        },
        "synthesis": {"provider": engine.provider},
        "database": {"enabled": persister.enabled},
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

    indicators_payload: dict[str, list[dict[str, Any]]] = {}
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

    payload = {
        "country": {"iso_code": iso, "name": country_name},
        "factbook": profile_payload,
        "worldbank": indicators_payload,
    }

    if persister.enabled:
        try:
            await persister.upsert_country_bundle(payload)
        except Exception:
            pass

    return payload


@app.get("/v1/context/{query}")
async def get_context(
    query: str,
    depth: str = Query("standard", enum=["brief", "standard", "comprehensive"]),
    region: str | None = None,
    start_year: int = 2000,
    end_year: int = 2026,
    provider: str | None = Query(None, enum=["ollama", "anthropic"]),
):
    result = await _build_context_response(
        query=query,
        depth=depth,
        region=region,
        start_year=start_year,
        end_year=end_year,
        provider=provider,
    )
    return result


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
    timeline: dict[str, dict[str, list[dict[str, Any]]]] = {}
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
    provider: str | None = Query(None, enum=["ollama", "anthropic"]),
):
    context = await _build_context_response(
        query=topic,
        depth="comprehensive",
        provider=provider,
    )

    report = context["report"]
    markdown = _report_to_markdown(report)
    if format == "summary":
        markdown = f"# {report.get('title', topic)}\n\n{report.get('summary', '')}"
    elif format == "executive":
        markdown = (
            f"# {report.get('title', topic)}\n\n"
            f"## Executive Summary\n{report.get('summary', '')}\n\n"
            f"## Current Assessment\n{report.get('current_assessment', '')}"
        )

    return {
        "topic": topic,
        "format": format,
        "report": report,
        "markdown": markdown,
        "sources_available": context["sources_available"],
    }


@app.get("/v1/compare/{event_a}/{event_b}")
async def compare_events(
    event_a: str,
    event_b: str,
    provider: str | None = Query(None, enum=["ollama", "anthropic"]),
):
    context_a = await _build_context_response(query=event_a, depth="standard", provider=provider)
    context_b = await _build_context_response(query=event_b, depth="standard", provider=provider)

    comparison = await engine.generate_comparison(
        event_a=event_a,
        event_b=event_b,
        context_a=context_a["report"],
        context_b=context_b["report"],
        provider=provider,
    )

    return {
        "event_a": event_a,
        "event_b": event_b,
        "comparison": comparison,
        "sources_available": {
            "event_a": context_a["sources_available"],
            "event_b": context_b["sources_available"],
        },
    }


@app.get("/v1/sources/{report_id}")
async def get_sources(report_id: str):
    return {
        "report_id": report_id,
        "status": "not_implemented",
        "sources": [],
    }


async def _build_context_response(
    query: str,
    depth: str,
    region: str | None = None,
    start_year: int = 2000,
    end_year: int = 2026,
    provider: str | None = None,
) -> dict[str, Any]:
    iso = _to_iso(query)
    country_name = query

    try:
        country_data = await get_country(iso, start_year=start_year, end_year=end_year)
        country_name = country_data["country"]["name"]
    except HTTPException:
        country_data = {
            "country": {"iso_code": iso, "name": query},
            "factbook": {},
            "worldbank": {},
        }

    sources_available: dict[str, dict[str, Any]] = {
        "worldbank": {
            "status": "used" if country_data.get("worldbank") else "skipped",
            "records": sum(len(v) for v in country_data.get("worldbank", {}).values()),
            "reason": "no world bank data" if not country_data.get("worldbank") else None,
        },
        "cia_factbook": {
            "status": "used" if country_data.get("factbook") else "skipped",
            "records": len(country_data.get("factbook", {})),
            "reason": "no factbook data" if not country_data.get("factbook") else None,
        },
        "gdelt": {"status": "skipped", "records": 0, "reason": "not requested"},
        "acled": {"status": "skipped", "records": 0, "reason": "not requested"},
        "sipri": {"status": "skipped", "records": 0, "reason": "no local data"},
        "fas": {"status": "skipped", "records": 0, "reason": "no local data"},
    }

    gdelt_events: list[dict[str, Any]] = []
    acled_events: list[dict[str, Any]] = []

    if not _is_test_mode():
        try:
            gdelt_events = await gdelt.fetch_events(query=query, maxrecords=50, country_code=iso)
            sources_available["gdelt"] = {
                "status": "used" if gdelt_events else "skipped",
                "records": len(gdelt_events),
                "reason": "no matching events" if not gdelt_events else None,
            }
        except Exception as exc:  # noqa: BLE001
            sources_available["gdelt"] = {
                "status": "skipped",
                "records": 0,
                "reason": f"unavailable: {exc}",
            }

        try:
            acled_events = await acled.fetch_events(
                country=country_name,
                start_date=f"{start_year}-01-01",
                end_date=f"{end_year}-12-31",
                limit=100,
                max_pages=2,
            )
            reason = None
            status = "used"
            if not acled.configured:
                status = "skipped"
                reason = "missing ACLED credentials"
            elif not acled_events:
                status = "skipped"
                reason = "no matching events"

            sources_available["acled"] = {
                "status": status,
                "records": len(acled_events),
                "reason": reason,
            }
        except Exception as exc:  # noqa: BLE001
            sources_available["acled"] = {
                "status": "skipped",
                "records": 0,
                "reason": f"unavailable: {exc}",
            }
    else:
        sources_available["gdelt"] = {
            "status": "skipped",
            "records": 0,
            "reason": "test mode",
        }
        sources_available["acled"] = {
            "status": "skipped",
            "records": 0,
            "reason": "test mode",
        }

    sipri_data = sipri.get_country_military_data(iso, start_year=start_year, end_year=end_year)
    sipri_records = len(sipri_data.get("military_expenditure", [])) + len(
        sipri_data.get("arms_transfers", [])
    )
    if sipri_records:
        sources_available["sipri"] = {"status": "used", "records": sipri_records, "reason": None}

    fas_data = fas.get_country_data(iso)
    if fas_data:
        sources_available["fas"] = {"status": "used", "records": 1, "reason": None}

    military_data = {
        "sipri": sipri_data,
        "fas": fas_data,
    }
    events = {
        "gdelt": gdelt_events,
        "acled": acled_events,
    }

    report = await engine.generate_context(
        query=query,
        depth=depth,
        country_data=country_data,
        events=events,
        military_data=military_data,
        sources_available=sources_available,
        provider=provider,
    )

    if persister.enabled:
        try:
            await persister.persist_events(gdelt_events + acled_events)
            await persister.persist_context_report(
                query=query,
                depth=depth,
                content=report,
                verification_status="pending",
                model_used=provider or engine.provider,
            )
        except Exception:
            pass

    return {
        "query": query,
        "depth": depth,
        "region": region,
        "country": country_data["country"],
        "report": report,
        "sources": report.get("sources_cited", []),
        "sources_available": sources_available,
    }


def _report_to_markdown(report: dict[str, Any]) -> str:
    timeline_lines = (
        "\n".join(
            f"- {item.get('year')}: {item.get('event')} ({item.get('source')})"
            for item in report.get("timeline", [])
        )
        or "- No timeline data"
    )
    perspectives_lines = (
        "\n".join(
            f"- **{p.get('framework', 'Framework')}**: {p.get('argument', '')}"
            for p in report.get("perspectives", [])
        )
        or "- No perspective data"
    )

    return (
        f"# {report.get('title', 'Ground Truth Briefing')}\n\n"
        f"## Summary\n{report.get('summary', '')}\n\n"
        f"## Background\n{report.get('background', '')}\n\n"
        f"## Timeline\n{timeline_lines}\n\n"
        f"## Economic Context\n{report.get('economic_context', '')}\n\n"
        f"## Military Context\n{report.get('military_context', '')}\n\n"
        f"## Perspectives\n{perspectives_lines}\n\n"
        f"## Current Assessment\n{report.get('current_assessment', '')}\n\n"
        f"## Confidence Notes\n{report.get('confidence_notes', '')}\n"
    )


def _to_iso(query: str) -> str:
    q = query.strip()
    if len(q) == 2 and q.isalpha():
        return q.upper()
    return factbook.normalize_country_to_iso(q)


def _cache_status(path: Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {"loaded": False, "freshness": None}

    mtime = datetime.fromtimestamp(target.stat().st_mtime, tz=timezone.utc).isoformat()
    return {"loaded": True, "freshness": mtime}


def _is_test_mode() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ
