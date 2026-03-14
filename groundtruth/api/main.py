"""Ground Truth API — Geopolitical Context Engine."""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from groundtruth import __version__
from groundtruth.api.auth import AuthMiddleware
from groundtruth.api.query_parser import parse_query
from groundtruth.ingestion.acled import ACLEDIngestor
from groundtruth.ingestion.cia_factbook import CIAFactbookIngestor
from groundtruth.ingestion.fas import FASIngestor
from groundtruth.ingestion.gdelt import GDELTIngestor
from groundtruth.ingestion.persist import DatabasePersister
from groundtruth.ingestion.sipri import SIPRIIngestor
from groundtruth.ingestion.worldbank import INDICATOR_IDS, WorldBankIngestor
from groundtruth.synthesis.engine import ContextEngine
from groundtruth.verification.pipeline import VerificationPipeline

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


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Application lifespan — replaces deprecated @app.on_event('startup')."""
    if persister.enabled:
        try:
            await persister.seed_approved_sources()
        except Exception:  # noqa: BLE001
            pass
    yield


app = FastAPI(
    title="Ground Truth",
    description="Open-source geopolitical context engine. The intelligence briefing behind the radar blip.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)


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


@app.get("/v1/events/{iso_code}.geojson", summary="Events as GeoJSON FeatureCollection")
async def get_events_geojson(
    iso_code: str,
    days: int = Query(30, ge=1, le=365, description="Number of days back to fetch events"),
) -> dict[str, Any]:
    """Return GDELT + ACLED events as a GeoJSON FeatureCollection.

    Compatible with World Monitor map layer format. Each feature includes
    geometry (Point) and properties (event_type, date, description, source, actors).
    Coordinates default to [0, 0] for GDELT events without geo data.
    """
    iso = iso_code.upper().replace(".GEOJSON", "")
    features: list[dict[str, Any]] = []

    if not _is_test_mode():
        try:
            gdelt_events = await gdelt.fetch_events(query=iso, country_code=iso, maxrecords=50)
            for ev in gdelt_events:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [
                                float(ev.get("longitude") or 0),
                                float(ev.get("latitude") or 0),
                            ],
                        },
                        "properties": {
                            "event_type": ev.get("event_type", "article"),
                            "date": str(ev.get("date", "")),
                            "description": ev.get("description", ""),
                            "source": "GDELT",
                            "actors": [],
                            "source_url": ev.get("source_url", ""),
                        },
                    }
                )
        except Exception:  # noqa: BLE001
            pass

        if acled.configured:
            try:
                from datetime import timedelta

                start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
                end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                acled_events = await acled.fetch_events(start_date=start, end_date=end)
                for ev in acled_events:
                    lat = ev.get("latitude") or 0
                    lon = ev.get("longitude") or 0
                    features.append(
                        {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                            "properties": {
                                "event_type": ev.get("event_type", "unknown"),
                                "date": str(ev.get("date", "")),
                                "description": ev.get("description", ""),
                                "source": "ACLED",
                                "actors": ev.get("actors", []),
                                "source_url": ev.get("source_url", ""),
                            },
                        }
                    )
            except Exception:  # noqa: BLE001
                pass

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "iso_code": iso,
            "days": days,
            "total": len(features),
        },
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

    # F-001: include sources_available so callers know what data was loaded
    wb_records = sum(len(v) for v in indicators_payload.values())
    fb_records = len(profile_payload)
    country_sources_available: dict[str, dict[str, Any]] = {
        "cia_factbook": {
            "status": "used" if fb_records else "skipped",
            "records": fb_records,
            "reason": "no factbook data" if not fb_records else None,
        },
        "worldbank": {
            "status": "used" if wb_records else "skipped",
            "records": wb_records,
            "reason": "no world bank data" if not wb_records else None,
        },
    }

    payload = {
        "country": {"iso_code": iso, "name": country_name},
        "factbook": profile_payload,
        "worldbank": indicators_payload,
        "sources_available": country_sources_available,
    }

    if persister.enabled:
        try:
            await persister.upsert_country_bundle(payload)
        except Exception:  # noqa: BLE001
            pass

    return payload


@app.get("/v1/context/{query}")
async def get_context(
    query: str,
    depth: str | None = Query(None, enum=["brief", "standard", "comprehensive"]),
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


@app.get("/v1/context/{query}/stream")
async def get_context_stream(
    query: str,
    depth: str | None = Query(None, enum=["brief", "standard", "comprehensive"]),
    region: str | None = None,
    start_year: int = 2000,
    end_year: int = 2026,
    provider: str | None = Query(None, enum=["ollama", "anthropic"]),
):
    queue: asyncio.Queue[tuple[str, dict[str, Any]] | None] = asyncio.Queue()

    async def emit_progress(stage: str, message: str, percent: int) -> None:
        await queue.put(
            (
                "progress",
                {"stage": stage, "message": message, "percent": max(0, min(100, percent))},
            )
        )

    async def worker() -> None:
        try:
            result = await _build_context_response(
                query=query,
                depth=depth,
                region=region,
                start_year=start_year,
                end_year=end_year,
                provider=provider,
                progress_cb=emit_progress,
            )
            await emit_progress("complete", "Briefing ready", 100)
            await queue.put(("result", result))
        except Exception as exc:  # noqa: BLE001
            await queue.put(("error", {"detail": str(exc)}))
        finally:
            await queue.put(None)

    async def event_generator():
        task = asyncio.create_task(worker())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                event_type, payload = event
                yield _sse_event(event_type, payload)
        finally:
            if not task.done():
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/v1/parse/{query}")
async def parse_query_endpoint(query: str):
    """Parse a raw user query into structured geopolitical intent/entities."""
    return await parse_query(query)


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
    depth: str | None,
    region: str | None = None,
    start_year: int = 2000,
    end_year: int = 2026,
    provider: str | None = None,
    progress_cb: Callable[[str, str, int], Awaitable[None]] | None = None,
) -> dict[str, Any]:
    await _emit_progress(progress_cb, "parsing", "Parsing query...", 5)
    try:
        parsed_query = await parse_query(query)
    except Exception:
        parsed_query = {
            "countries": [],
            "time_period": {"start_year": start_year, "end_year": end_year},
            "suggested_depth": "standard",
        }
    await _emit_progress(progress_cb, "parsing_done", "Query parsed", 10)

    if depth is None:
        depth = str(parsed_query.get("suggested_depth") or "standard")

    parsed_period = parsed_query.get("time_period", {})
    if start_year == 2000 and isinstance(parsed_period, dict) and parsed_period.get("start_year"):
        start_year = int(parsed_period.get("start_year", start_year))
    if end_year == 2026 and isinstance(parsed_period, dict) and parsed_period.get("end_year"):
        end_year = int(parsed_period.get("end_year", end_year))

    # Extract ALL countries from the query (e.g., "US-Iran Tensions" → ["IR", "US"])
    all_countries = _extract_countries(query)
    if not all_countries:
        parsed_countries = parsed_query.get("countries", [])
        if isinstance(parsed_countries, list):
            all_countries = [str(item).upper() for item in parsed_countries if str(item).strip()]
    iso = _to_iso(query)  # primary country for the response envelope
    if iso == "XX" and all_countries:
        iso = all_countries[0]
    country_name = query
    display_countries = ", ".join(all_countries) if all_countries else query
    await _emit_progress(
        progress_cb,
        "parsing_done",
        f"Identified: {display_countries}",
        12,
    )

    # Fetch data for primary country
    await _emit_progress(progress_cb, "factbook", "Fetching CIA Factbook profiles...", 15)
    try:
        country_data = await get_country(iso, start_year=start_year, end_year=end_year)
        country_name = country_data["country"]["name"]
    except HTTPException:
        country_data = {
            "country": {"iso_code": iso, "name": query},
            "factbook": {},
            "worldbank": {},
        }
    await _emit_progress(progress_cb, "factbook_done", "Factbook data loaded", 25)

    # For bilateral/multi-country queries, fetch secondary countries and merge
    secondary_data: list[dict[str, Any]] = []
    secondary_isos = [c for c in all_countries if c != iso]
    for sec_iso in secondary_isos[:3]:  # cap at 3 secondary countries
        try:
            sec_data = await get_country(sec_iso, start_year=start_year, end_year=end_year)
            secondary_data.append(sec_data)
        except HTTPException:
            pass

    await _emit_progress(progress_cb, "worldbank", "Fetching World Bank indicators...", 30)

    # Merge secondary factbook/worldbank into country_data for richer synthesis
    if secondary_data:
        merged_factbook = dict(country_data.get("factbook", {}))
        merged_worldbank = dict(country_data.get("worldbank", {}))

        for sec in secondary_data:
            sec_name = sec.get("country", {}).get("name", "Unknown")
            sec_fb = sec.get("factbook", {})
            if sec_fb:
                for key, val in sec_fb.items():
                    merged_factbook[f"{sec_name}_{key}"] = val

            sec_wb = sec.get("worldbank", {})
            if sec_wb:
                for key, val in sec_wb.items():
                    merged_worldbank[f"{sec_name}_{key}"] = val

        country_data["factbook"] = merged_factbook
        country_data["worldbank"] = merged_worldbank
        # Add secondary country names for the synthesis prompt
        country_data["secondary_countries"] = [
            s.get("country", {}).get("name", "Unknown") for s in secondary_data
        ]

    # Track total records across all countries for source status
    wb_records = sum(len(v) for v in country_data.get("worldbank", {}).values())
    fb_records = len(country_data.get("factbook", {}))
    await _emit_progress(
        progress_cb,
        "worldbank_done",
        f"Loaded {wb_records} economic indicators across {max(1, len(all_countries))} countries",
        40,
    )

    sources_available: dict[str, dict[str, Any]] = {
        "worldbank": {
            "status": "used" if wb_records else "skipped",
            "records": wb_records,
            "reason": "no world bank data" if not wb_records else None,
        },
        "cia_factbook": {
            "status": "used" if fb_records else "skipped",
            "records": fb_records,
            "reason": "no factbook data" if not fb_records else None,
        },
        "gdelt": {"status": "skipped", "records": 0, "reason": "not requested"},
        "acled": {"status": "skipped", "records": 0, "reason": "not requested"},
        "sipri": {"status": "skipped", "records": 0, "reason": "no local data"},
        "fas": {"status": "skipped", "records": 0, "reason": "no local data"},
    }

    gdelt_events: list[dict[str, Any]] = []
    acled_events: list[dict[str, Any]] = []

    if not _is_test_mode():
        await _emit_progress(progress_cb, "gdelt", "Scanning GDELT event database...", 45)
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
        await _emit_progress(
            progress_cb,
            "gdelt_done",
            f"Found {len(gdelt_events)} GDELT events in the last 30 days",
            55,
        )

        await _emit_progress(progress_cb, "acled", "Querying ACLED conflict data...", 60)
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
        await _emit_progress(
            progress_cb,
            "acled_done",
            f"Loaded {len(acled_events)} ACLED conflict records",
            65,
        )
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
        await _emit_progress(progress_cb, "gdelt_done", "GDELT skipped in test mode", 55)
        await _emit_progress(progress_cb, "acled_done", "ACLED skipped in test mode", 65)

    # Fetch SIPRI/FAS for ALL countries, merge results
    await _emit_progress(progress_cb, "military", "Loading SIPRI/FAS military data...", 70)
    sipri_data: dict[str, Any] = sipri.get_country_military_data(
        iso, start_year=start_year, end_year=end_year
    )
    fas_data: dict[str, Any] | None = fas.get_country_data(iso)

    for sec_iso in secondary_isos[:3]:
        sec_sipri = sipri.get_country_military_data(
            sec_iso, start_year=start_year, end_year=end_year
        )
        if sec_sipri.get("military_expenditure"):
            sipri_data.setdefault("military_expenditure", []).extend(
                sec_sipri["military_expenditure"]
            )
        if sec_sipri.get("arms_transfers"):
            sipri_data.setdefault("arms_transfers", []).extend(sec_sipri["arms_transfers"])

        sec_fas = fas.get_country_data(sec_iso)
        if sec_fas and not fas_data:
            fas_data = sec_fas
        elif sec_fas and fas_data:
            # Merge: store as list of country nuclear profiles
            if not isinstance(fas_data, list):
                fas_data = [fas_data]
            fas_data.append(sec_fas)

    sipri_records = len(sipri_data.get("military_expenditure", [])) + len(
        sipri_data.get("arms_transfers", [])
    )
    if sipri_records:
        sources_available["sipri"] = {"status": "used", "records": sipri_records, "reason": None}

    if fas_data:
        fas_count = len(fas_data) if isinstance(fas_data, list) else 1
        sources_available["fas"] = {"status": "used", "records": fas_count, "reason": None}
    else:
        fas_count = 0

    await _emit_progress(
        progress_cb,
        "military_done",
        (
            "SIPRI: "
            f"{len(sipri_data.get('military_expenditure', []))} military expenditure records, "
            f"{len(sipri_data.get('arms_transfers', []))} arms transfers; "
            f"FAS profiles: {fas_count}"
        ),
        75,
    )

    military_data = {
        "sipri": sipri_data,
        "fas": fas_data,
    }
    events = {
        "gdelt": gdelt_events,
        "acled": acled_events,
    }

    await _emit_progress(progress_cb, "synthesis", "AI synthesis in progress...", 80)
    report = await engine.generate_context(
        query=query,
        depth=depth,
        country_data=country_data,
        events=events,
        military_data=military_data,
        sources_available=sources_available,
        provider=provider,
    )
    await _emit_progress(progress_cb, "synthesis_done", "Briefing generated", 88)

    # --- Verification pipeline ---
    await _emit_progress(progress_cb, "verification", "Verifying sources and claims...", 90)
    pipeline = VerificationPipeline()
    verification = await pipeline.run(
        {"query": query, "report": report, "sources": report.get("sources_cited", [])},
        depth=depth or "standard",
    )
    verification_status = verification.verification_summary
    await _emit_progress(progress_cb, "verification_done", "Verification complete", 95)

    if persister.enabled:
        try:
            await persister.persist_events(gdelt_events + acled_events)
            await persister.persist_context_report(
                query=query,
                depth=depth,
                content=report,
                verification_status=verification_status["overall_status"],
                model_used=provider or engine.provider,
            )
        except Exception:  # noqa: BLE001
            pass

    return {
        "query": query,
        "depth": depth,
        "region": region,
        "country": country_data["country"],
        "report": report,
        "sources": report.get("sources_cited", []),
        "sources_available": sources_available,
        "verification_status": verification_status,
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


async def _emit_progress(
    progress_cb: Callable[[str, str, int], Awaitable[None]] | None,
    stage: str,
    message: str,
    percent: int,
) -> None:
    if progress_cb is not None:
        await progress_cb(stage, message, percent)


def _sse_event(event_type: str, payload: dict[str, Any]) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"


QUERY_COUNTRY_MAP: dict[str, str] = {
    "iran": "IR",
    "iraq": "IQ",
    "israel": "IL",
    "palestine": "PS",
    "gaza": "PS",
    "ukraine": "UA",
    "russia": "RU",
    "china": "CN",
    "taiwan": "TW",
    "north korea": "KP",
    "south korea": "KR",
    "syria": "SY",
    "yemen": "YE",
    "libya": "LY",
    "afghanistan": "AF",
    "pakistan": "PK",
    "india": "IN",
    "georgia": "GE",
    "armenia": "AM",
    "azerbaijan": "AZ",
    "us": "US",
    "usa": "US",
    "united states": "US",
    "uk": "GB",
    "united kingdom": "GB",
    "france": "FR",
    "germany": "DE",
    "japan": "JP",
    "saudi arabia": "SA",
    "turkey": "TR",
    "nato": "US",
    "eu": "DE",
}


def _extract_countries(query: str) -> list[str]:
    """Extract all country ISO codes from a complex query string."""
    q = query.strip().lower()
    found: list[str] = []

    # Check for 2-letter ISO codes in the query (e.g., "US" in "US-Iran")
    for word in query.split():
        clean = word.strip(" -–—,.!?()[]").upper()
        if len(clean) == 2 and clean.isalpha():
            if clean in (
                "US",
                "UK",
                "IR",
                "UA",
                "RU",
                "CN",
                "IN",
                "IL",
                "PS",
                "IQ",
                "SY",
                "KP",
                "KR",
                "JP",
                "DE",
                "FR",
                "GB",
                "SA",
                "TR",
                "TW",
                "YE",
                "LY",
                "AF",
                "PK",
                "GE",
                "AM",
                "AZ",
            ):
                if clean not in found:
                    found.append(clean)

    # Check for country names in the query (longer names first to avoid partial matches)
    sorted_names = sorted(QUERY_COUNTRY_MAP.keys(), key=len, reverse=True)
    for name in sorted_names:
        if name in q:
            iso = QUERY_COUNTRY_MAP[name]
            if iso not in found:
                found.append(iso)

    return found


def _to_iso(query: str) -> str:
    """Get the primary country ISO code from a query."""
    countries = _extract_countries(query)
    if countries:
        # Return the first non-US country if available (for "US-Iran", we want Iran data)
        # But if only US, return US
        non_us = [c for c in countries if c != "US"]
        return non_us[0] if non_us else countries[0]

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
