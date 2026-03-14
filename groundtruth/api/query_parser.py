"""AI-powered geopolitical query parser."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

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
}

QUERY_PARSE_PROMPT = """You are a geopolitical query parser. Given a user query, extract structured information.

Return ONLY valid JSON with this schema:
{{
  "query_type": "country" | "bilateral" | "regional" | "topical",
  "countries": ["ISO-2 codes"],
  "region": "middle-east" | "europe" | "asia" | "africa" | "americas" | null,
  "topic": "brief description of the core topic",
  "time_period": {{"start_year": 1953, "end_year": 2026}},
  "key_entities": ["organizations, treaties, leaders mentioned"],
  "suggested_depth": "brief" | "standard" | "comprehensive"
}}

Examples:
- "US-Iran Tensions" -> {{"query_type": "bilateral", "countries": ["US", "IR"], "topic": "US-Iran geopolitical tensions", "time_period": {{"start_year": 1953, "end_year": 2026}}}}
- "Ukraine war" -> {{"query_type": "country", "countries": ["UA", "RU"], "topic": "Russia-Ukraine conflict", "time_period": {{"start_year": 2014, "end_year": 2026}}}}
- "South China Sea tensions" -> {{"query_type": "regional", "countries": ["CN", "PH", "VN", "TW"], "region": "asia", "topic": "South China Sea territorial disputes"}}
- "NATO expansion history" -> {{"query_type": "topical", "countries": ["US", "DE", "FR", "GB"], "topic": "NATO expansion since 1949", "key_entities": ["NATO", "Warsaw Pact"]}}

Query: {query}
"""


def _extract_countries_fallback(query: str) -> list[str]:
    q = query.strip().lower()
    found: list[str] = []

    for word in query.split():
        clean = word.strip(" -–—,.!?()[]").upper()
        if len(clean) == 2 and clean.isalpha() and clean not in found:
            found.append(clean)

    sorted_names = sorted(QUERY_COUNTRY_MAP.keys(), key=len, reverse=True)
    for name in sorted_names:
        if name in q:
            iso = QUERY_COUNTRY_MAP[name]
            if iso not in found:
                found.append(iso)

    return found


def _fallback_parse(query: str) -> dict[str, Any]:
    countries = _extract_countries_fallback(query)
    query_type = "country"
    if len(countries) >= 2:
        query_type = "bilateral"

    return {
        "query_type": query_type,
        "countries": countries,
        "region": None,
        "topic": query,
        "time_period": {"start_year": 2000, "end_year": 2026},
        "key_entities": [],
        "suggested_depth": "standard",
    }


async def parse_query(query: str) -> dict[str, Any]:
    """Use Ollama for fast query understanding; fallback to local heuristics."""
    if "PYTEST_CURRENT_TEST" in os.environ:
        return _fallback_parse(query)

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.1")

    prompt = QUERY_PARSE_PROMPT.format(query=query)

    try:
        timeout = httpx.Timeout(10.0, read=60.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 512},
                },
            )
            response.raise_for_status()
            raw = str(response.json().get("response", ""))

        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            parsed = json.loads(raw[start : end + 1])
            if isinstance(parsed, dict):
                parsed.setdefault("query_type", "country")
                parsed.setdefault("countries", [])
                parsed.setdefault("region", None)
                parsed.setdefault("topic", query)
                parsed.setdefault("time_period", {"start_year": 2000, "end_year": 2026})
                parsed.setdefault("key_entities", [])
                parsed.setdefault("suggested_depth", "standard")
                return parsed
    except Exception:
        pass

    return _fallback_parse(query)
