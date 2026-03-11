"""Ground Truth API — Geopolitical Context Engine.

FastAPI application serving historical context and intelligence briefings
from authoritative primary sources.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from groundtruth import __version__

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


@app.get("/")
async def root():
    """Health check and API info."""
    return {
        "name": "Ground Truth",
        "version": __version__,
        "status": "operational",
        "description": "Geopolitical context engine — primary sources, no spin.",
        "docs": "/docs",
    }


@app.get("/v1/context/{query}")
async def get_context(
    query: str,
    depth: str = Query("standard", enum=["brief", "standard", "comprehensive"]),
    region: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
):
    """Generate historical context for a geopolitical event or situation.

    Returns a structured intelligence briefing with timeline, multiple
    interpretive frameworks, economic context, and every claim linked
    to its primary source.
    """
    # TODO: Wire up ingestion + synthesis pipeline
    return {
        "query": query,
        "depth": depth,
        "status": "not_implemented",
        "message": "Context engine coming soon. Data pipeline under construction.",
        "sources": [],
    }


@app.get("/v1/timeline/{region}")
async def get_timeline(
    region: str,
    start_year: int = 1945,
    end_year: int = 2026,
    categories: str | None = None,
):
    """Get chronological event timeline for a geographic region.

    Pulls from GDELT, ACLED, UCDP, and historical archives to build
    a comprehensive event chain showing how the current situation developed.
    """
    # TODO: Wire up timeline generation
    return {
        "region": region,
        "start_year": start_year,
        "end_year": end_year,
        "status": "not_implemented",
        "events": [],
    }


@app.get("/v1/briefing/{topic}")
async def get_briefing(
    topic: str,
    format: str = Query("full", enum=["full", "summary", "executive"]),
):
    """Generate a full intelligence briefing on a topic.

    Combines historical context, current events, economic data,
    military posture, and treaty/legal frameworks into a comprehensive
    briefing with multiple interpretive frameworks.
    """
    # TODO: Wire up briefing generation
    return {
        "topic": topic,
        "format": format,
        "status": "not_implemented",
        "briefing": None,
    }


@app.get("/v1/compare/{event_a}/{event_b}")
async def compare_events(event_a: str, event_b: str):
    """Compare historical patterns between two events or situations.

    Identifies parallels, differences, and recurring patterns
    across different geopolitical situations.
    """
    # TODO: Wire up comparison engine
    return {
        "event_a": event_a,
        "event_b": event_b,
        "status": "not_implemented",
        "parallels": [],
        "differences": [],
    }


@app.get("/v1/sources/{report_id}")
async def get_sources(report_id: str):
    """Get all primary sources cited in a context report.

    Returns full citation details including source name, URL,
    archive location, access date, and reliability assessment.
    """
    # TODO: Wire up source retrieval
    return {
        "report_id": report_id,
        "status": "not_implemented",
        "sources": [],
    }
