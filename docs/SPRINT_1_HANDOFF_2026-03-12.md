# SPRINT 1 HANDOFF — Ground Truth Data Pipeline + Source Validator
**Date:** 2026-03-12
**From:** Opus (COO / Product Owner)
**To:** Antigravity (QA) + Sonnet (Dev) — working together in one environment
**Project:** Ground Truth — Open-Source Geopolitical Context Engine
**Repo:** https://github.com/lmagee3/ground-truth

---

## OBJECTIVE
Wire up the first two data source integrations (World Bank + CIA Factbook), build the database layer, and get the Source Validator running. By end of sprint, we should be able to query real geopolitical data through the API and validate that sources are authoritative.

---

## SPRINT 1 TASKS (in order)

### Task 1: World Bank Indicators Ingestion
**Owner:** Sonnet
**File:** `groundtruth/ingestion/worldbank.py`
**Priority:** Do this first — proves the pipeline works

The World Bank Indicators API requires NO API key. Base URL: `https://api.worldbank.org/v2/`

**What to build:**
- Async HTTP client (httpx) that queries World Bank API
- Fetch these indicator categories per country:
  - `MS.MIL.XPND.GD.ZS` — Military expenditure (% of GDP)
  - `MS.MIL.XPND.CD` — Military expenditure (current USD)
  - `NY.GDP.MKTP.CD` — GDP (current USD)
  - `NY.GDP.MKTP.KD.ZG` — GDP growth (annual %)
  - `NE.TRD.GNFS.ZS` — Trade (% of GDP)
  - `SP.POP.TOTL` — Population total
  - `FP.CPI.TOTL.ZG` — Inflation (consumer prices, annual %)
  - `BN.CAB.XOKA.CD` — Current account balance
- Parse JSON response into structured data models
- Support querying by country code (ISO 3166-1 alpha-2) and year range
- Cache responses locally (avoid hammering the API)
- Rate limit: be respectful, 1 request/second max

**Example API call:**
```
GET https://api.worldbank.org/v2/country/CN/indicator/MS.MIL.XPND.GD.ZS?format=json&date=2000:2025
```

**Test:** `tests/ingestion/test_worldbank.py`
- Test that we can fetch GDP for a known country (US, China)
- Test date range filtering works
- Test error handling for invalid country codes
- Mock the HTTP calls for CI (don't hit live API in tests)

---

### Task 2: CIA World Factbook Ingestion
**Owner:** Sonnet
**File:** `groundtruth/ingestion/cia_factbook.py`

The CIA World Factbook is available as structured JSON. Multiple GitHub mirrors exist:
- Primary: `https://github.com/factbook/factbook.json` (organized by region)
- Alternative: `https://raw.githubusercontent.com/iancoleman/cia_world_factbook_api/master/data/` (single files per country)

**What to build:**
- Load country profiles from the JSON data
- Extract per country:
  - Government type, chief of state, head of government
  - Military branches, service age, military expenditure
  - Geography (area, borders, coastline, natural resources)
  - Economy (GDP, industries, exports/imports, major trade partners)
  - Demographics (population, ethnic groups, languages, religions)
  - Transnational issues (disputes, refugees, trafficking)
  - International organization memberships
- Normalize country names to ISO codes for cross-referencing with World Bank
- Store as structured data that the synthesis engine can query

**Test:** `tests/ingestion/test_cia_factbook.py`
- Test parsing a known country profile (e.g., China, Iran, Ukraine)
- Test that military data fields are extracted correctly
- Test cross-reference capability (Factbook country → ISO code → World Bank data)

---

### Task 3: Database Models
**Owner:** Sonnet
**File:** `groundtruth/models.py` + `alembic/`

**What to build:**
```python
# Core tables needed:

class Country:
    """Country reference table."""
    iso_code: str          # ISO 3166-1 alpha-2 (primary key)
    name: str
    region: str
    factbook_data: dict    # Full CIA Factbook JSON blob
    updated_at: datetime

class Indicator:
    """World Bank indicator values."""
    country_code: str      # FK to Country
    indicator_id: str      # e.g., MS.MIL.XPND.GD.ZS
    indicator_name: str
    year: int
    value: float
    source: str            # 'worldbank', 'sipri', etc.
    fetched_at: datetime

class Event:
    """Geopolitical events from GDELT/ACLED/UCDP."""
    id: uuid
    source: str            # 'gdelt', 'acled', 'ucdp'
    source_id: str         # Original ID from source
    event_type: str
    date: date
    country_code: str
    latitude: float
    longitude: float
    description: str
    actors: list[str]
    source_url: str
    raw_data: dict

class ContextReport:
    """Generated context reports (cached)."""
    id: uuid
    query: str
    depth: str             # 'brief', 'standard', 'comprehensive'
    content: dict          # Structured report JSON
    sources_cited: list[str]  # URLs of all cited sources
    verification_status: str  # 'pending', 'passed', 'failed', 'flagged'
    verification_report: dict
    generated_at: datetime
    model_used: str        # 'ollama/llama3', 'claude-sonnet', etc.
    cache_expires: datetime

class ApprovedSource:
    """Approved authoritative source domains."""
    domain: str            # Primary key
    organization: str
    source_type: str       # 'us_gov', 'international', 'allied', 'academic'
    reliability_score: int # 1-10
    notes: str
```

- Set up Alembic for migrations
- Use async SQLAlchemy with asyncpg
- Create initial migration with all tables
- Seed `ApprovedSource` table from `docs/APPROVED_SOURCES.md`

**Test:** `tests/test_models.py`
- Test model creation
- Test Country ↔ Indicator relationship
- Test ApprovedSource seeding

---

### Task 4: Wire Ingestion to API
**Owner:** Sonnet
**File:** Update `groundtruth/api/main.py`

Replace the stub endpoints with real data:
- `/v1/context/{query}` — For now, return raw World Bank + Factbook data for a country (synthesis comes later)
- `/v1/timeline/{region}` — Return World Bank indicators over time for a region
- Add a `/v1/country/{iso_code}` endpoint — return combined Factbook profile + World Bank indicators
- Add a `/v1/health` endpoint — show which data sources are loaded and their freshness

---

### Task 5: Source Validator (Parallel with Tasks 1-4)
**Owner:** Antigravity
**File:** `groundtruth/verification/source_validator.py`

This is the first piece of the verification pipeline. Build it in parallel while Sonnet wires ingestion.

**What to build:**
```python
class SourceValidator:
    """Validates that all sources in a context report are authoritative."""

    async def validate_report(self, report: dict) -> ValidationResult:
        """Run all validation checks on a context report."""

    async def check_url_live(self, url: str) -> bool:
        """Verify URL resolves (HEAD request, follow redirects)."""

    def check_domain_approved(self, url: str) -> tuple[bool, str]:
        """Check if URL domain is on the approved sources list."""

    async def check_wayback_fallback(self, url: str) -> str | None:
        """If URL is dead, check Wayback Machine for archived version."""

    def check_date_freshness(self, source_date: str, report_context_date: str) -> str:
        """Flag if source is significantly older than the context period."""
```

**Load approved domains from:** `docs/APPROVED_SOURCES.md` (parse the markdown table) or from the `ApprovedSource` DB table once Task 3 is done.

**Output format:**
```python
@dataclass
class SourceValidation:
    url: str
    domain: str
    is_approved: bool
    is_live: bool  # or None if not checked
    wayback_url: str | None
    freshness: str  # 'current', 'dated', 'stale'
    status: str  # 'pass', 'warn', 'fail'
    notes: str

@dataclass
class ValidationResult:
    total_sources: int
    passed: int
    warned: int
    failed: int
    details: list[SourceValidation]
    overall_status: str  # 'pass', 'warn', 'fail'
```

**Also build:** `groundtruth/verification/pipeline.py` — skeleton orchestrator that runs Source Validator (and later Bias Detector + Fact Checker).

**Test:** `tests/verification/test_source_validator.py`
- Test approved domain check against known good/bad domains
- Test URL liveness check (mock HTTP)
- Test date freshness flagging
- Test full report validation with mixed good/bad sources

---

## DEFINITION OF DONE

Sprint 1 is complete when:
- [ ] `python -m uvicorn groundtruth.api.main:app` starts without errors
- [ ] `/v1/country/US` returns real World Bank + CIA Factbook data
- [ ] `/v1/country/CN` returns real data for China
- [ ] World Bank data for at least 5 countries is fetched and stored
- [ ] CIA Factbook profiles for all 260 countries are loaded
- [ ] Source Validator correctly flags non-approved domains
- [ ] Source Validator correctly validates approved domain URLs
- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`black`, `isort`, `ruff`)
- [ ] Changes committed and pushed to GitHub

---

## WHAT NOT TO DO

- Don't build the synthesis (AI) layer yet — that's Sprint 2
- Don't build the frontend — that's Sprint 3 at earliest
- Don't build auth/rate limiting yet — not needed until we have something worth protecting
- Don't build Bias Detector or Fact Checker yet — they need real AI-generated reports to test against
- Don't over-engineer the DB schema — we'll add fields as needed
- Don't try to ingest GDELT or ACLED yet — those are Sprint 2

---

## BACKBRIEF

When Sprint 1 is complete, write:
`docs/handoffs/SPRINT_1_BACKBRIEF_YYYY-MM-DD.md`

Include: what was built, what works, what doesn't, test results, any architectural decisions made during implementation, and recommended next steps for Sprint 2.

---

## SPRINT 2 PREVIEW (so you know where this is going)

1. GDELT ingestion (real-time events)
2. ACLED ingestion (conflict data)
3. FAS.org military/weapons data loader
4. SIPRI arms transfers + military spending loader
5. AI synthesis layer (Ollama local)
6. Fact Checker module
7. Bias Detector module
8. First real context report generation

---

**Questions?** Escalate to Opus via Lawrence. Ship > perfect.
