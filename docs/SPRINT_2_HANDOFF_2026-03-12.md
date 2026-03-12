# SPRINT 2 HANDOFF — GDELT + ACLED + Military Data + AI Synthesis
**Date:** 2026-03-12
**From:** Opus (COO / Product Owner)
**To:** Codex (Dev) → Antigravity (QA after delivery)
**Project:** Ground Truth — Open-Source Geopolitical Context Engine
**Repo:** https://github.com/lmagee3/ground-truth

---

## OBJECTIVE
Add real-time event data (GDELT + ACLED), military/defense data (SIPRI + FAS), and the AI synthesis layer that generates actual context reports from raw data. By end of sprint, `/v1/context/` should return a real intelligence briefing — not raw data dumps.

**Sprint 1 delivered:** World Bank + CIA Factbook ingestion, DB models, Source Validator (45 tests passing).
**Sprint 2 delivers:** Event data, military context, and the AI brain that turns it all into briefings.

---

## SPRINT 2 TASKS

### Task 1: GDELT Ingestion
**File:** `groundtruth/ingestion/gdelt.py`
**Priority:** HIGH — this is our real-time event backbone

GDELT provides global events updated every 15 minutes. Use the GDELT DOC 2.0 API (no key needed).

**DOC 2.0 API endpoint:**
```
https://api.gdeltproject.org/api/v2/doc/doc?query={query}&mode={mode}&format=json
```

**Modes to support:**
- `artlist` — returns list of articles matching query
- `timelinevol` — returns volume of coverage over time
- `tonechart` — returns sentiment/tone analysis over time

**What to build:**
- Async httpx client for GDELT DOC 2.0
- Query by: keyword/topic, country, date range
- Parse response into structured event records
- Support geographic filtering (country code or lat/lon bounding box)
- Cache responses (GDELT data is massive — cache aggressively)
- Rate limit: 1 request per 5 seconds (GDELT is free but rate-sensitive)

**Example queries:**
```
# Events related to South China Sea in last 7 days
https://api.gdeltproject.org/api/v2/doc/doc?query=south%20china%20sea&mode=artlist&maxrecords=50&format=json

# Tone timeline for Iran nuclear
https://api.gdeltproject.org/api/v2/doc/doc?query=iran%20nuclear&mode=timelinevol&format=json
```

**Map to our Event model:**
```python
Event(
    source="gdelt",
    source_id=gdelt_url_hash,
    event_type=category,  # from GDELT taxonomy
    date=published_date,
    country_code=iso_from_source_country,
    description=title,
    source_url=article_url,
    raw_data=full_gdelt_record,
)
```

**Test:** `tests/ingestion/test_gdelt.py`
- Mock HTTP responses (don't hit live GDELT in CI)
- Test query construction with different parameters
- Test parsing of artlist, timelinevol, and tonechart responses
- Test geographic filtering
- Test cache behavior

---

### Task 2: ACLED Ingestion
**File:** `groundtruth/ingestion/acled.py`
**Priority:** HIGH — gold standard conflict data

ACLED uses OAuth 2.0 authentication. Lawrence has a myACLED account. Credentials go in `.env`.

**Authentication flow (OAuth — MUST implement this):**
```
# Step 1: Get access token (valid 24 hours)
POST https://acleddata.com/oauth/token
Content-Type: application/x-www-form-urlencoded

username=EMAIL@DOMAIN.COM
password=YOUR_PASSWORD
grant_type=password
client_id=acled

# Response:
{
  "token_type": "Bearer",
  "expires_in": 86400,
  "access_token": "ACCESS-TOKEN-HERE",
  "refresh_token": "REFRESH-TOKEN-HERE"
}

# Step 2: Use token in API requests
GET https://acleddata.com/api/acled/read?_format=json&country=Georgia&limit=50
Authorization: Bearer {ACCESS_TOKEN}

# Step 3: Refresh token when expired (refresh token valid 14 days)
POST https://acleddata.com/oauth/token
refresh_token=YOUR_REFRESH_TOKEN
grant_type=refresh_token
client_id=acled
```

**API base URL:**
```
https://acleddata.com/api/acled/read?_format=json
```

**Parameters:**
- `country` — country name (e.g., `Georgia`). Multiple: `country=Georgia:OR:country=Armenia`
- `event_date` — date filter (YYYY-MM-DD format)
- `event_date_where` — `BETWEEN` with pipe separator: `event_date=2022-01-01|2023-02-01&event_date_where=BETWEEN`
- `event_type` — filter by type (Battles, Violence against civilians, Protests, Riots, Strategic developments, Explosions/Remote violence)
- `year` — filter by year
- `fields` — pipe-separated list of fields to return: `fields=event_id_cnty|event_date|event_type|country|fatalities`
- `limit` — max records (default 5000)

**What to build:**
- OAuth token manager: get token, cache it, auto-refresh when expired
- Async httpx client using Bearer token auth
- Query by: country name, date range (BETWEEN), event type, year
- Parse JSON response into our Event model
- Handle pagination for large result sets (requests beyond 5000 rows)
- Cache by query hash
- Rate limit: be respectful, 1 req/2 seconds
- Graceful degradation: if no ACLED credentials in .env, skip ACLED data silently

**Map to our Event model:**
```python
Event(
    source="acled",
    source_id=str(acled_data_id),
    event_type=event_type,       # "Battles", "Protests", etc.
    date=event_date,
    country_code=iso_alpha2,
    latitude=latitude,
    longitude=longitude,
    description=notes,
    actors=[actor1, actor2],     # assoc_actor_1, assoc_actor_2
    source_url=f"https://acleddata.com/data-export-tool/",
    raw_data=full_acled_record,
)
```

**Env vars needed (add to .env.example):**
```
ACLED_API_KEY=
ACLED_EMAIL=
```

**Test:** `tests/ingestion/test_acled.py`
- Mock HTTP responses
- Test query construction
- Test ISO alpha-2 → numeric conversion
- Test event type filtering
- Test date range queries
- Test pagination handling

---

### Task 3: SIPRI Military Data Loader
**File:** `groundtruth/ingestion/sipri.py`
**Priority:** MEDIUM — critical for military context layer

SIPRI provides structured data as downloadable CSV/Excel files. No API — we download and parse.

**Data sources:**
1. **Military Expenditure Database:** https://www.sipri.org/databases/milex
   - CSV download: military spending by country, 1949-2024
   - Constant USD + current USD + % of GDP
2. **Arms Transfers Database:** https://www.sipri.org/databases/armstransfers
   - TIV (Trend Indicator Values) of arms exports/imports by country

**What to build:**
- Download and parse SIPRI CSV data files
- Store as structured records: country, year, spending (USD), spending (% GDP), exports, imports
- Normalize country names to ISO codes (SIPRI uses full country names)
- Cache downloaded files locally
- Provide query interface: get military spending for country X over years Y-Z

**Data model (extend Indicator or create new):**
```python
# Can reuse Indicator model with source="sipri"
Indicator(
    country_code="US",
    indicator_id="SIPRI.MIL.EXP.USD",
    indicator_name="Military expenditure (current USD)",
    year=2023,
    value=916000000000,
    source="sipri",
)
```

**Note:** SIPRI data needs to be pre-downloaded. Add a script at `scripts/download_sipri.py` that fetches the latest CSVs. The ingestor reads from local files, not live HTTP on every query.

**Test:** `tests/ingestion/test_sipri.py`
- Test CSV parsing with sample data fixture
- Test country name → ISO normalization
- Test year range filtering

---

### Task 4: FAS Military Data Loader
**File:** `groundtruth/ingestion/fas.py`
**Priority:** MEDIUM — weapons systems + nuclear data

Federation of American Scientists (fas.org) provides:
- **Nuclear Notebook:** Nuclear warhead counts by country
- **Weapons systems profiles:** Capabilities, operators, specifications

FAS data is available as structured web content. We'll need to parse it into structured records.

**What to build:**
- Nuclear arsenal data by country (warheads: strategic, nonstrategic, total, deployed, reserve, retired)
- Map to our data model: country code, weapon system name, category, key specs
- Initial focus: nuclear warhead counts for the 9 nuclear states (US, Russia, UK, France, China, India, Pakistan, Israel, North Korea)
- Static data file approach: create `data/fas_nuclear.json` with current figures, update periodically

**Data structure:**
```json
{
  "US": {
    "total_warheads": 5044,
    "deployed": 1670,
    "reserve": 1938,
    "retired_awaiting_dismantlement": 1436,
    "last_updated": "2024",
    "source_url": "https://fas.org/issues/nuclear-weapons/status-world-nuclear-forces/"
  }
}
```

**Test:** `tests/ingestion/test_fas.py`
- Test loading nuclear data
- Test querying by country
- Test data structure validation

---

### Task 5: AI Synthesis Layer
**File:** `groundtruth/synthesis/engine.py`
**Priority:** CRITICAL — this is what turns data into intelligence

This is the core brain. Takes raw data from all ingestion sources and generates structured context reports.

**What to build:**

```python
class ContextEngine:
    """Generates intelligence briefings from raw geopolitical data."""

    def __init__(self, provider: str = "ollama"):
        """
        provider: "ollama" (free, local) or "anthropic" (paid, Claude API)
        """

    async def generate_context(
        self,
        query: str,
        depth: str = "standard",  # brief, standard, comprehensive
        country_data: dict = None,
        events: list[dict] = None,
        military_data: dict = None,
    ) -> ContextReport:
        """Generate a structured context report."""

    def _build_prompt(self, query, depth, data) -> str:
        """Construct the synthesis prompt with all available data."""

    async def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama instance."""

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Claude API (production only)."""
```

**The synthesis prompt is critical. Here's the template:**

```
You are Ground Truth, a geopolitical context engine. Your role is to generate
intelligence briefings that explain HOW and WHY geopolitical situations developed.

RULES:
1. Use ONLY the data provided below. Do not hallucinate facts.
2. Present MULTIPLE interpretive frameworks — do not pick sides.
3. Every factual claim must reference its source from the provided data.
4. Use military briefing style: clear, direct, no editorial language.
5. Structure: Background → Key Events → Economic Context → Military Context →
   Multiple Perspectives → Current Assessment

QUERY: {query}
DEPTH: {depth}

AVAILABLE DATA:
--- CIA FACTBOOK ---
{factbook_data}

--- WORLD BANK INDICATORS ---
{worldbank_data}

--- GDELT EVENTS (Recent) ---
{gdelt_events}

--- ACLED CONFLICT DATA ---
{acled_events}

--- MILITARY DATA (SIPRI/FAS) ---
{military_data}

Generate a structured intelligence briefing. For each factual claim, cite the
source dataset (e.g., [World Bank], [CIA Factbook], [ACLED], [SIPRI]).

Output as JSON:
{
  "title": "...",
  "summary": "...",  // 2-3 sentence executive summary
  "background": "...",  // Historical context
  "timeline": [
    {"year": 2020, "event": "...", "source": "..."},
  ],
  "economic_context": "...",
  "military_context": "...",
  "perspectives": [
    {"framework": "...", "argument": "...", "evidence": "..."},
  ],
  "current_assessment": "...",
  "sources_cited": ["..."],
  "confidence_notes": "..."  // What data is missing or uncertain
}
```

**Ollama integration:**
```python
# Local Ollama endpoint (default)
POST http://localhost:11434/api/generate
{
    "model": "llama3.1",  # or mistral, gemma
    "prompt": "<the synthesis prompt>",
    "stream": false,
    "options": {
        "temperature": 0.3,  # Low temp for factual output
        "num_predict": 4096
    }
}
```

**Anthropic integration (paid tier):**
```python
import anthropic
client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
response = await client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    temperature=0.3,
    messages=[{"role": "user", "content": prompt}]
)
```

**Env vars (add to .env.example):**
```
# AI Synthesis
SYNTHESIS_PROVIDER=ollama  # or "anthropic"
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
ANTHROPIC_API_KEY=  # Only needed for paid tiers
```

**Test:** `tests/synthesis/test_engine.py`
- Test prompt construction with various data combinations
- Test Ollama client (mock HTTP)
- Test Anthropic client (mock)
- Test response parsing (JSON extraction from LLM output)
- Test fallback behavior when Ollama is unavailable
- Test depth variants (brief vs comprehensive prompt differences)

---

### Task 6: Wire Everything Into API
**File:** Update `groundtruth/api/main.py`

Replace the remaining stub endpoints:

**`/v1/context/{query}`** — Full flow:
1. Resolve query to country/region
2. Fetch World Bank + Factbook data (existing)
3. Fetch GDELT events for the query
4. Fetch ACLED conflict events (if API key configured)
5. Fetch military data (SIPRI + FAS)
6. Pass everything to ContextEngine.generate_context()
7. Return structured report with sources

**`/v1/briefing/{topic}`** — Similar to context but:
- Uses "comprehensive" depth by default
- Adds executive summary section
- Returns formatted markdown in addition to JSON

**`/v1/compare/{event_a}/{event_b}`** —
- Generate context for both events
- Prompt AI to identify parallels and differences
- Return structured comparison

**Add query parameter to control AI provider:**
```
/v1/context/south-china-sea?provider=ollama  # Free tier
/v1/context/south-china-sea?provider=anthropic  # Paid tier
```

---

### Task 7: Persist to Database
**File:** `groundtruth/ingestion/persist.py` or integrate into existing modules

Wire the ingestion modules to actually write to PostgreSQL:
- On first query for a country, fetch and persist World Bank + Factbook data
- Cache GDELT/ACLED results in the Event table
- Store generated ContextReports with verification_status="pending"
- Seed ApprovedSource table from markdown on startup
- Add a `scripts/seed_data.py` that pre-loads top 20 countries

---

## DEFINITION OF DONE

Sprint 2 is complete when:
- [ ] `/v1/context/south-china-sea` returns a real AI-generated context report (using Ollama)
- [ ] `/v1/context/ukraine` returns a report with World Bank + Factbook + GDELT data synthesized
- [ ] GDELT events are fetched and parsed for any query
- [ ] ACLED integration works when API key is configured (graceful skip when not)
- [ ] SIPRI military spending data is loaded for major countries
- [ ] FAS nuclear data is available for the 9 nuclear states
- [ ] Context reports include source citations
- [ ] `/v1/briefing/{topic}` returns a comprehensive formatted briefing
- [ ] All new tests pass (target: 70+ total tests)
- [ ] Code formatted (black, isort, ruff)
- [ ] Changes committed and pushed

---

## WHAT NOT TO DO

- Don't build the frontend — Sprint 3
- Don't build auth/rate limiting — Sprint 3
- Don't build the full DB persistence pipeline if it slows you down — cache-first is fine, DB persistence is a nice-to-have this sprint
- Don't over-engineer the AI prompt — get it working, we'll iterate
- Don't try to parse all of GDELT's taxonomy — start with basic article list and tone
- Don't worry about Bias Detector or Fact Checker — Antigravity handles those after this sprint

---

## HANDOFF TO ANTIGRAVITY (After Sprint 2)

Once this sprint ships, Antigravity takes over to:
1. Wire Source Validator into the API response pipeline
2. Build Fact Checker against real context reports
3. Build Bias Detector against real AI-generated text
4. Add `verification_status` field to all context report responses

---

## BACKBRIEF

When Sprint 2 is complete, write:
`docs/handoffs/SPRINT_2_BACKBRIEF_YYYY-MM-DD.md`

Include: what was built, test count, example API response from a real query, architectural decisions, known gaps, recommended Sprint 3 tasks.

---

**This is the sprint that makes Ground Truth real. After this, we have a working geopolitical context engine. Ship it.**
