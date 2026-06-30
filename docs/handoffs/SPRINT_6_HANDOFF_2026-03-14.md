# Sprint 6 Handoff — Ground Truth
**Date:** 2026-03-14
**From:** Opus (COO / Product Owner)
**To:** Codex (Infrastructure / Feature Dev)
**Status:** Ready for execution

---

## Sprint Objective
Add three new primary source ingestors — Library of Congress, Congress.gov, and NARA (National Archives) — bringing GT's source count from 6 to 9. These sources add **congressional testimony, treaty texts, declassified intelligence, and historical documents** that no competitor has. Every query for every nation should benefit from deeper historical primary source material.

---

## Task 1: Library of Congress Ingestor (`loc.py`)

### What It Gives Us
Congressional Research Service reports, historical documents, maps, manuscripts, digital collections. Searchable across all LoC collections. When someone searches "Taiwan strait tensions," we can pull actual congressional hearing references and CRS policy reports.

### API Details
- **Base URL:** `https://www.loc.gov/search/`
- **Auth:** None required. Public access. No API key.
- **Rate Limit:** Enforced but undocumented. Be respectful — add 1s delay between requests.
- **Format:** Append `?fo=json` to any loc.gov URL to get JSON response.
- **Pagination:** Max 100,000 results navigable. Use `sp=` parameter for page number.
- **Collections:** Can filter by collection (e.g., `fa=partof:congressional+research+service+reports`)

### Search Endpoint
```
GET https://www.loc.gov/search/?q={query}&fo=json&c=25
```

Parameters:
- `q` — keyword search (searches metadata + full text)
- `fo` — format, always `json`
- `c` — results per page (max 100)
- `sp` — page number
- `fa` — facet filter (pipe-separated). Useful filters:
  - `fa=partof:congressional+research+service+reports` — CRS reports only
  - `fa=original-format:document` — documents only
  - `fa=subject:international+relations` — IR topic filter
  - `fa=location:iran` — location-based filter

### Response Structure
```json
{
  "results": [
    {
      "id": "https://www.loc.gov/item/2023689142/",
      "title": "Iran: Politics, Human Rights, and U.S. Policy",
      "description": ["Congressional Research Service report..."],
      "date": "2023-01-15",
      "contributor": ["Congressional Research Service"],
      "subject": ["Iran", "Foreign relations"],
      "original_format": ["document"],
      "url": "https://www.loc.gov/item/2023689142/",
      "aka": ["http://hdl.loc.gov/loc.crs/R44017"]
    }
  ],
  "pagination": {
    "current": 1,
    "total": 247,
    "perpage": 25
  }
}
```

### Ingestor Implementation

**New file:** `groundtruth/ingestion/loc.py`

```python
"""Library of Congress ingestor — congressional records, CRS reports, historical documents."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

LOC_BASE_URL = "https://www.loc.gov"
LOC_SEARCH_URL = f"{LOC_BASE_URL}/search/"
LOC_CACHE_DIR = Path("data/cache/loc")

# Prioritize these collections for geopolitical relevance
PRIORITY_COLLECTIONS = [
    "congressional+research+service+reports",
    "foreign+affairs+oral+history+collection",
    "country+studies",
]


@dataclass
class LOCDocument:
    id: str
    title: str
    description: str
    date: str | None
    subjects: list[str]
    contributors: list[str]
    url: str
    collection: str | None


class LOCIngestor:
    """Fetch documents from the Library of Congress JSON API."""

    cache_dir: Path = LOC_CACHE_DIR

    def __init__(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def search_documents(
        self,
        query: str,
        max_results: int = 10,
        collection_filter: str | None = None,
    ) -> list[LOCDocument]:
        """Search LoC for documents matching a geopolitical query.

        Args:
            query: Search term (country name, topic, etc.)
            max_results: Maximum documents to return.
            collection_filter: Optional fa= filter for specific collection.

        Returns:
            List of LOCDocument objects.
        """
        params: dict[str, str] = {
            "q": query,
            "fo": "json",
            "c": str(min(max_results, 100)),
        }
        if collection_filter:
            params["fa"] = f"partof:{collection_filter}"

        documents: list[LOCDocument] = []
        timeout = httpx.Timeout(15.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            # Search priority collections first, then general
            collections = PRIORITY_COLLECTIONS if not collection_filter else [collection_filter]
            seen_ids: set[str] = set()

            for collection in collections:
                if len(documents) >= max_results:
                    break

                search_params = {**params, "fa": f"partof:{collection}"}
                try:
                    resp = await client.get(LOC_SEARCH_URL, params=search_params)
                    resp.raise_for_status()
                    data = resp.json()

                    for item in data.get("results", []):
                        item_id = item.get("id", "")
                        if item_id in seen_ids:
                            continue
                        seen_ids.add(item_id)

                        doc = LOCDocument(
                            id=item_id,
                            title=item.get("title", "Untitled"),
                            description=self._first_str(item.get("description", [])),
                            date=item.get("date", None),
                            subjects=item.get("subject", []),
                            contributors=item.get("contributor", []),
                            url=item.get("url", item_id),
                            collection=collection,
                        )
                        documents.append(doc)

                        if len(documents) >= max_results:
                            break

                except Exception:  # noqa: BLE001
                    continue

                # Rate limit: 1s between collection queries
                await asyncio.sleep(1.0)

            # If priority collections didn't fill quota, do a general search
            if len(documents) < max_results:
                try:
                    resp = await client.get(LOC_SEARCH_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                    for item in data.get("results", []):
                        item_id = item.get("id", "")
                        if item_id in seen_ids:
                            continue
                        seen_ids.add(item_id)

                        doc = LOCDocument(
                            id=item_id,
                            title=item.get("title", "Untitled"),
                            description=self._first_str(item.get("description", [])),
                            date=item.get("date", None),
                            subjects=item.get("subject", []),
                            contributors=item.get("contributor", []),
                            url=item.get("url", item_id),
                            collection=None,
                        )
                        documents.append(doc)

                        if len(documents) >= max_results:
                            break
                except Exception:  # noqa: BLE001
                    pass

        return documents

    def format_for_synthesis(self, documents: list[LOCDocument]) -> str:
        """Format LoC documents into a concise summary for the synthesis prompt."""
        if not documents:
            return "No Library of Congress documents found."

        lines: list[str] = []
        for doc in documents:
            date_str = f" ({doc.date})" if doc.date else ""
            subjects = ", ".join(doc.subjects[:5]) if doc.subjects else ""
            desc = doc.description[:200] + "..." if len(doc.description) > 200 else doc.description
            lines.append(
                f"[LoC] {doc.title}{date_str}\n"
                f"  Source: {', '.join(doc.contributors[:2]) or 'Library of Congress'}\n"
                f"  Topics: {subjects}\n"
                f"  Summary: {desc}\n"
                f"  URL: {doc.url}"
            )

        return "\n\n".join(lines)

    @staticmethod
    def _first_str(val: Any) -> str:
        if isinstance(val, list):
            return str(val[0]) if val else ""
        return str(val) if val else ""
```

---

## Task 2: Congress.gov Ingestor (`congress.py`)

### What It Gives Us
Treaty texts, hearing transcripts, committee reports, bill summaries — the actual legislative record on any foreign policy topic. When someone asks about "NATO expansion," we can cite the actual Senate ratification debates.

### API Details
- **Base URL:** `https://api.congress.gov/v3/`
- **Auth:** API key required. Free from [api.data.gov](https://api.data.gov/signup/). Pass as `api_key=` query parameter.
- **Rate Limit:** 5,000 requests/hour per key.
- **Format:** JSON by default.

### Key Endpoints
```
GET /v3/treaty?api_key={key}&limit=10&offset=0
GET /v3/treaty/{congress}/{treatyNumber}?api_key={key}
GET /v3/hearing?api_key={key}&limit=10&offset=0
GET /v3/committee-report?api_key={key}&limit=10&offset=0
GET /v3/congressional-record?api_key={key}&limit=10&offset=0
```

Search isn't keyword-based on most endpoints — they're structured by congress number, chamber, and topic. The best approach is:
1. Search the **Congressional Record** endpoint with keywords (this covers floor debates)
2. Query **treaties** by congress number
3. Query **committee reports** which often contain foreign relations committee analysis

### Env Variable
```
CONGRESS_API_KEY=your_key_here
```

### Ingestor Implementation

**New file:** `groundtruth/ingestion/congress.py`

```python
"""Congress.gov API ingestor — treaties, hearings, committee reports."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

CONGRESS_BASE_URL = "https://api.congress.gov/v3"


@dataclass
class CongressRecord:
    record_type: str  # treaty | hearing | committee_report | floor_debate
    title: str
    date: str | None
    congress: int | None
    chamber: str | None
    url: str
    summary: str


class CongressIngestor:
    """Fetch legislative records from the Congress.gov API."""

    def __init__(self) -> None:
        self.api_key = os.getenv("CONGRESS_API_KEY", "")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def fetch_treaties(
        self,
        query_hint: str | None = None,
        congress: int | None = None,
        limit: int = 10,
    ) -> list[CongressRecord]:
        """Fetch treaty records. Note: Congress.gov treaty endpoint doesn't support
        keyword search — we fetch recent treaties and filter client-side if query_hint provided."""
        if not self.configured:
            return []

        params: dict[str, str] = {
            "api_key": self.api_key,
            "limit": str(limit),
            "format": "json",
        }

        url = f"{CONGRESS_BASE_URL}/treaty"
        if congress:
            url = f"{CONGRESS_BASE_URL}/treaty/{congress}"

        records: list[CongressRecord] = []
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

                for treaty in data.get("treaties", []):
                    title = treaty.get("topic", treaty.get("treatySubject", "Untitled"))
                    # Client-side keyword filter if provided
                    if query_hint and query_hint.lower() not in str(treaty).lower():
                        continue

                    records.append(CongressRecord(
                        record_type="treaty",
                        title=title,
                        date=treaty.get("dateTransmittedToSenate"),
                        congress=treaty.get("congressReceived"),
                        chamber="Senate",
                        url=treaty.get("url", ""),
                        summary=treaty.get("resolutionText", "")[:500],
                    ))
        except Exception:  # noqa: BLE001
            pass

        return records

    async def fetch_committee_reports(
        self,
        query_hint: str | None = None,
        congress: int | None = None,
        limit: int = 10,
    ) -> list[CongressRecord]:
        """Fetch committee reports (especially Senate Foreign Relations Committee)."""
        if not self.configured:
            return []

        # Default to recent congresses (118th = 2023-2024, 119th = 2025-2026)
        target_congress = congress or 119
        params: dict[str, str] = {
            "api_key": self.api_key,
            "limit": str(limit),
            "format": "json",
        }

        records: list[CongressRecord] = []
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                url = f"{CONGRESS_BASE_URL}/committee-report/{target_congress}"
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

                for report in data.get("reports", []):
                    title = report.get("title", "Untitled")
                    if query_hint and query_hint.lower() not in str(report).lower():
                        continue

                    records.append(CongressRecord(
                        record_type="committee_report",
                        title=title,
                        date=report.get("issueDate"),
                        congress=target_congress,
                        chamber=report.get("chamber"),
                        url=report.get("url", ""),
                        summary=report.get("text", "")[:500],
                    ))
        except Exception:  # noqa: BLE001
            pass

        return records

    async def fetch_records(
        self,
        query: str,
        limit: int = 10,
    ) -> list[CongressRecord]:
        """Fetch all relevant congressional records for a geopolitical query."""
        all_records: list[CongressRecord] = []

        treaties = await self.fetch_treaties(query_hint=query, limit=limit)
        all_records.extend(treaties)

        reports = await self.fetch_committee_reports(query_hint=query, limit=limit)
        all_records.extend(reports)

        # Sort by date descending (most recent first)
        all_records.sort(key=lambda r: r.date or "", reverse=True)
        return all_records[:limit]

    def format_for_synthesis(self, records: list[CongressRecord]) -> str:
        """Format congressional records for the synthesis prompt."""
        if not records:
            return "No Congress.gov records found."

        lines: list[str] = []
        for rec in records:
            date_str = f" ({rec.date})" if rec.date else ""
            congress_str = f" — {rec.congress}th Congress" if rec.congress else ""
            lines.append(
                f"[Congress.gov] [{rec.record_type.upper()}] {rec.title}{date_str}{congress_str}\n"
                f"  Chamber: {rec.chamber or 'N/A'}\n"
                f"  {rec.summary[:200]}"
            )

        return "\n\n".join(lines)
```

---

## Task 3: NARA Ingestor (`nara.py`)

### What It Gives Us
Declassified intelligence documents, diplomatic cables, presidential records, military operation records. The NSA, CIA, and State Department all transfer declassified materials to NARA. This is where the real intelligence gold lives.

### API Details
- **Base URL:** `https://catalog.archives.gov/api/v2/`
- **Auth:** API key required. Email `Catalog_API@nara.gov` with your email + catalog username.
- **Rate Limit:** 10,000 queries/month per key. That's tight — cache aggressively.
- **Format:** JSON.
- **Note:** If API key not available, ingestor should gracefully degrade (skip, don't crash).

### Search Endpoint
```
GET https://catalog.archives.gov/api/v2/records/search
Headers: x-api-key: {key}
Params:
  q={query}
  limit={limit}
  availableOnline=true
  typeOfMaterials=Textual Records
```

### Key Record Groups for Intelligence
- **RG 263** — Records of the CIA
- **RG 457** — Records of the NSA
- **RG 59** — Records of the Department of State
- **RG 218** — Records of the Joint Chiefs of Staff
- **RG 330** — Records of the Office of the Secretary of Defense

### Env Variable
```
NARA_API_KEY=your_key_here
```

### Ingestor Implementation

**New file:** `groundtruth/ingestion/nara.py`

```python
"""NARA (National Archives) ingestor — declassified intelligence, diplomatic records."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

NARA_BASE_URL = "https://catalog.archives.gov/api/v2"
NARA_CACHE_DIR = Path("data/cache/nara")

# Record groups most relevant to geopolitical intelligence
INTELLIGENCE_RECORD_GROUPS = {
    "263": "Central Intelligence Agency (CIA)",
    "457": "National Security Agency (NSA)",
    "59": "Department of State",
    "218": "Joint Chiefs of Staff",
    "330": "Office of the Secretary of Defense",
}


@dataclass
class NARDocument:
    nara_id: str
    title: str
    description: str
    date: str | None
    record_group: str | None
    record_group_name: str | None
    creators: list[str]
    url: str
    online: bool


class NARAIngestor:
    """Fetch declassified documents from the National Archives Catalog API v2."""

    cache_dir: Path = NARA_CACHE_DIR

    def __init__(self) -> None:
        self.api_key = os.getenv("NARA_API_KEY", "")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def search_records(
        self,
        query: str,
        max_results: int = 10,
        online_only: bool = True,
        record_groups: list[str] | None = None,
    ) -> list[NARDocument]:
        """Search NARA catalog for declassified documents.

        Args:
            query: Search term.
            max_results: Maximum records to return.
            online_only: Only return digitized/online records.
            record_groups: Filter to specific RGs (e.g., ["263", "457"] for CIA + NSA).

        Returns:
            List of NARDocument objects.
        """
        if not self.configured:
            return []

        params: dict[str, str] = {
            "q": query,
            "limit": str(min(max_results, 100)),
        }
        if online_only:
            params["availableOnline"] = "true"

        headers = {"x-api-key": self.api_key}
        documents: list[NARDocument] = []

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                resp = await client.get(
                    f"{NARA_BASE_URL}/records/search",
                    params=params,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("body", {}).get("hits", {}).get("hits", []):
                    source = item.get("_source", {})

                    rg = str(source.get("recordGroupNumber", ""))
                    rg_name = INTELLIGENCE_RECORD_GROUPS.get(rg) or source.get(
                        "recordGroupTitle", None
                    )

                    # If filtering by record groups, skip non-matching
                    if record_groups and rg not in record_groups:
                        continue

                    doc = NARDocument(
                        nara_id=str(item.get("_id", "")),
                        title=source.get("title", "Untitled"),
                        description=source.get("scopeAndContentNote", ""),
                        date=source.get("coverageDates", source.get("productionDateString")),
                        record_group=rg or None,
                        record_group_name=rg_name,
                        creators=source.get("creators", []),
                        url=f"https://catalog.archives.gov/id/{item.get('_id', '')}",
                        online=bool(source.get("hasDigitalObjects")),
                    )
                    documents.append(doc)

                    if len(documents) >= max_results:
                        break

        except Exception:  # noqa: BLE001
            pass

        return documents

    async def search_intelligence(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[NARDocument]:
        """Convenience method: search only intelligence record groups (CIA, NSA, State, JCS, SecDef)."""
        return await self.search_records(
            query=query,
            max_results=max_results,
            record_groups=list(INTELLIGENCE_RECORD_GROUPS.keys()),
        )

    def format_for_synthesis(self, documents: list[NARDocument]) -> str:
        """Format NARA documents for the synthesis prompt."""
        if not documents:
            return "No National Archives records found."

        lines: list[str] = []
        for doc in documents:
            date_str = f" ({doc.date})" if doc.date else ""
            rg_str = f" [RG {doc.record_group}: {doc.record_group_name}]" if doc.record_group else ""
            desc = doc.description[:200] + "..." if len(doc.description) > 200 else doc.description
            online_str = " [DIGITIZED]" if doc.online else ""
            lines.append(
                f"[NARA]{rg_str}{online_str} {doc.title}{date_str}\n"
                f"  {desc}\n"
                f"  URL: {doc.url}"
            )

        return "\n\n".join(lines)
```

---

## Task 4: Wire New Sources into the Pipeline

### 4a. Update `_build_context_response()` in `main.py`

Add the three new ingestors alongside existing ones. Follow the same pattern as GDELT/ACLED:

```python
# At top of main.py
from groundtruth.ingestion.loc import LOCIngestor
from groundtruth.ingestion.congress import CongressIngestor
from groundtruth.ingestion.nara import NARAIngestor

loc = LOCIngestor()
congress = CongressIngestor()
nara = NARAIngestor()
```

In `_build_context_response()`, after the SIPRI/FAS block and before synthesis:

```python
# Fetch LoC, Congress.gov, NARA documents
await _emit_progress(progress_cb, "loc", "Searching Library of Congress...", 76)
loc_docs = await loc.search_documents(query=query, max_results=5)
sources_available["loc"] = {
    "status": "used" if loc_docs else "skipped",
    "records": len(loc_docs),
    "reason": "no matching documents" if not loc_docs else None,
}

await _emit_progress(progress_cb, "congress", "Querying Congress.gov...", 77)
congress_records = await congress.fetch_records(query=query, limit=5)
sources_available["congress"] = {
    "status": "used" if congress_records else "skipped",
    "records": len(congress_records),
    "reason": "no API key" if not congress.configured else ("no matching records" if not congress_records else None),
}

await _emit_progress(progress_cb, "nara", "Searching National Archives...", 78)
nara_docs = await nara.search_intelligence(query=query, max_results=5)
sources_available["nara"] = {
    "status": "used" if nara_docs else "skipped",
    "records": len(nara_docs),
    "reason": "no API key" if not nara.configured else ("no matching records" if not nara_docs else None),
}
```

### 4b. Update the Synthesis Prompt

In `engine.py`, add three new data sections to `PROMPT_TEMPLATE`:

```
LIBRARY OF CONGRESS (Congressional Records / CRS Reports):
{loc_data}

CONGRESSIONAL RECORDS (Treaties / Committee Reports):
{congress_data}

DECLASSIFIED INTELLIGENCE (National Archives):
{nara_data}
```

Add corresponding `format_for_synthesis()` calls in `_build_prompt()`:

```python
loc_data=loc_formatted,
congress_data=congress_formatted,
nara_data=nara_formatted,
```

### 4c. Update `_build_prompt()` signature

The `generate_context()` method needs to pass the new data through. Add three new params:
- `loc_data: list[dict] | None = None`
- `congress_data: list[dict] | None = None`
- `nara_data: list[dict] | None = None`

And format them for the prompt using each ingestor's `format_for_synthesis()` method.

**IMPORTANT:** Keep the summarized data concise. These sources should add ~500-1000 tokens MAX to the prompt. The goal is reference material (titles, dates, brief descriptions), not full document text. The synthesis engine uses these as evidence anchors, not as reading material.

### 4d. Update `.env.example`

```bash
# Congress.gov API (free key from api.data.gov)
# CONGRESS_API_KEY=your_key_here

# NARA National Archives Catalog API v2 (email Catalog_API@nara.gov)
# NARA_API_KEY=your_key_here

# Library of Congress — no key needed
```

### 4e. Update Source Status Display

The frontend `SourceStatus.tsx` component already handles arbitrary source keys dynamically, so no frontend changes needed. The new sources will appear automatically in the source panel.

---

## Task 5: Update Approved Sources List

**File:** `docs/APPROVED_SOURCES.md`

The LoC and NARA are already listed. Add Congress.gov API explicitly:

```markdown
| api.congress.gov | Congress.gov API | Treaties, hearings, committee reports, Congressional Record |
```

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `groundtruth/ingestion/loc.py` | **NEW** — Library of Congress ingestor |
| `groundtruth/ingestion/congress.py` | **NEW** — Congress.gov API ingestor |
| `groundtruth/ingestion/nara.py` | **NEW** — NARA catalog ingestor |
| `groundtruth/api/main.py` | Wire new ingestors + SSE progress stages |
| `groundtruth/synthesis/engine.py` | Add LoC/Congress/NARA data sections to prompt template + `_build_prompt()` |
| `.env.example` | Add CONGRESS_API_KEY and NARA_API_KEY |
| `docs/APPROVED_SOURCES.md` | Add api.congress.gov |
| `groundtruth/models/cache.py` | **NEW** — SQLAlchemy model for `source_cache` table |
| `groundtruth/ingestion/cache.py` | **NEW** — Cache-first wrapper (get/set/key generation) |
| `scripts/precompute_nara.py` | **NEW** — Nightly batch job for top hotspot queries |
| `tests/ingestion/test_loc.py` | **NEW** — unit tests |
| `tests/ingestion/test_congress.py` | **NEW** — unit tests |
| `tests/ingestion/test_nara.py` | **NEW** — unit tests |
| `tests/ingestion/test_cache.py` | **NEW** — cache layer tests |

---

## Testing

1. **LoC (no key needed):** `curl "https://www.loc.gov/search/?q=iran+foreign+relations&fo=json&c=5"` — should return JSON with results array
2. **Congress.gov (needs key):** `curl "https://api.congress.gov/v3/treaty?api_key=YOUR_KEY&limit=5&format=json"` — should return treaties
3. **NARA (needs key):** `curl -H "x-api-key: YOUR_KEY" "https://catalog.archives.gov/api/v2/records/search?q=iran+intelligence&limit=5"` — should return hits
4. **Graceful degradation:** If Congress.gov or NARA keys are missing, those sources should show `"status": "skipped", "reason": "no API key"` — NOT crash
5. **Synthesis integration:** Run "US-Iran tensions" query — new sources should appear in `sources_available` and their data should influence the briefing content
6. **Full test suite:** `pytest` — all existing tests pass + new tests for the 3 ingestors

---

## Priority Order
1. LoC ingestor (Task 1) — no API key needed, immediate value
2. Wire into pipeline (Task 4) — connect LoC to synthesis
3. NARA ingestor (Task 3) — highest-value source for intelligence context
4. **Source cache layer (Task 6)** — MUST ship with NARA ingestor, not after. 10K/month limit is a hard wall.
5. Congress.gov ingestor (Task 2) — treaties + committee reports
6. Tests + approved sources update (Task 5)

---

## Credential Actions for Lawrence
Before Codex runs this sprint, Lawrence needs to:

1. **Congress.gov API key** — Sign up at https://api.data.gov/signup/ (free, instant)
   - Add to `.env` as `CONGRESS_API_KEY=your_key`

2. **NARA API key** — Email `Catalog_API@nara.gov` with:
   - Your email address
   - Your catalog.archives.gov username (create account first at https://catalog.archives.gov)
   - May take 1-3 business days to receive key
   - Add to `.env` as `NARA_API_KEY=your_key`

3. **LoC** — No action needed. No key required.

**NOTE:** Codex should build ALL three ingestors regardless of whether keys are available. The graceful degradation pattern (check `.configured`, skip if no key) means the code ships and works with whatever keys are present. LoC works immediately. Congress.gov and NARA activate as soon as Lawrence adds the keys.

---

## Task 6: NARA Rate Limit Caching Layer

### Problem
NARA Catalog API v2 limits to **10,000 queries/month** per key. With multiple production users, that's exhausted in days.

### Why Caching Works Perfectly Here
NARA holds **declassified historical documents**. A 1979 CIA cable doesn't change. Unlike GDELT (real-time events) or World Bank (annual updates), NARA results are effectively immutable. Cache them forever.

### Implementation

**6a. Query Result Cache (PostgreSQL)**

Add a `nara_cache` table (or a generic `source_cache` table usable by any ingestor):

```sql
CREATE TABLE source_cache (
    cache_key VARCHAR(255) PRIMARY KEY,  -- SHA256 of source_name + query + params
    source_name VARCHAR(50) NOT NULL,     -- 'nara', 'loc', 'congress'
    query_text TEXT NOT NULL,
    result_json JSONB NOT NULL,
    record_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NULL   -- NULL = never expires (for NARA)
);

CREATE INDEX idx_source_cache_source ON source_cache(source_name);
CREATE INDEX idx_source_cache_created ON source_cache(created_at);
```

**6b. Cache-First Pattern in NARAIngestor**

```python
import hashlib, json

async def search_records(self, query, max_results=10, ...):
    # 1. Check cache first
    cache_key = self._cache_key(query, record_groups)
    cached = await self._get_cached(cache_key)
    if cached:
        return cached  # Never hits NARA API

    # 2. Cache miss → fetch from NARA
    results = await self._fetch_from_api(query, max_results, ...)

    # 3. Store in cache (no expiry for NARA)
    await self._set_cached(cache_key, results, expires=None)
    return results

def _cache_key(self, query: str, record_groups: list[str] | None) -> str:
    raw = f"nara:{query.lower().strip()}:{sorted(record_groups or [])}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

**6c. Pre-Compute Batch Script**

New file: `scripts/precompute_nara.py`

Runs nightly via cron or the scheduler. Queries NARA for the top hotspot topics and populates the cache. Budget: ~100 queries/night = 3,000/month, leaving 7,000 for live novel queries.

```python
HOTSPOT_QUERIES = [
    "iran nuclear", "ukraine russia", "taiwan strait", "south china sea",
    "north korea", "syria civil war", "israel palestine", "yemen",
    "sudan conflict", "myanmar coup", "afghanistan taliban",
    "libya", "venezuela", "cuba", "ethiopia tigray",
    # ... top 50-100 hotspots
]
```

**6d. Rate Limit Tracking**

Track NARA API calls in Redis (or a simple counter table):
- Increment on each live NARA request
- If approaching 9,000/month, switch to cache-only mode (no new NARA fetches)
- Log warning when 80% consumed
- Reset counter on 1st of each month

**6e. Apply Same Cache to LoC and Congress.gov**

The `source_cache` table is generic — use it for all three new sources. LoC and Congress.gov have more generous limits but caching still saves latency:
- **LoC:** No documented limit, but caching avoids hammering a public service
- **Congress.gov:** 5,000/hour is generous, but cache anyway for speed (legislative records also rarely change)
- **NARA:** Cache with no expiry (documents are immutable)
- **Congress.gov/LoC:** Cache with 30-day expiry (new legislation may appear)

### Credential Note for Lawrence
When emailing `Catalog_API@nara.gov` for your API key, mention:
- You're building an open-source intelligence research tool (MIT license)
- 20-year US Army IT veteran background
- Ask if elevated rate limits are available for research/educational use
- Link the GitHub repo for credibility

---

## Definition of Done
- [ ] LoC ingestor returns CRS reports and congressional records for any country query
- [ ] Congress.gov ingestor returns treaties and committee reports (when key is present)
- [ ] NARA ingestor returns declassified intelligence documents (when key is present)
- [ ] All three sources appear in `sources_available` response
- [ ] Synthesis prompt includes LoC/Congress/NARA data sections
- [ ] Missing API keys result in graceful skip, not crash
- [ ] SSE progress bar shows new "Library of Congress" / "Congress.gov" / "National Archives" stages
- [ ] All existing tests pass + new ingestor tests
- [ ] `source_cache` table created with PostgreSQL migration
- [ ] NARA ingestor checks cache before hitting API (cache-first pattern)
- [ ] Rate limit counter tracks monthly NARA API usage
- [ ] Pre-compute batch script exists for top 50+ hotspot queries
- [ ] LoC and Congress.gov ingestors also use `source_cache` (30-day expiry)
