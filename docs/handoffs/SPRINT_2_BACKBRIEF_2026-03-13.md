# SPRINT 2 BACKBRIEF — Events + Military Data + AI Synthesis
**Date:** 2026-03-13  
**From:** Codex (Implementation)  
**To:** Opus (COO / Product Owner) via Lawrence  
**Sprint:** 2

---

## What Was Built

### 1) GDELT Ingestion
**File:** `groundtruth/ingestion/gdelt.py`

Implemented `GDELTIngestor` with:
- Async DOC 2.0 API client (`artlist`, `timelinevol`, `tonechart`)
- Query parameters for topic, date range, and country filter
- Local cache under `.cache/gdelt/`
- Rate limit guard (1 request / 5 seconds)
- Parsing to normalized event records suitable for `Event` persistence

### 2) ACLED Ingestion
**File:** `groundtruth/ingestion/acled.py`

Implemented `ACLEDIngestor` with:
- OAuth2 token acquisition (`password` grant)
- Refresh token flow (`refresh_token` grant)
- Token lifetime handling with automatic refresh
- Query support for country/date range/event type/year
- Pagination support (`page`, `limit`, bounded by `max_pages`)
- Local cache under `.cache/acled/`
- Graceful skip behavior when credentials are missing (`ACLED_USERNAME`, `ACLED_PASSWORD`)
- Base data endpoint wired to `https://acleddata.com/acled/read`

### 3) SIPRI Loader
**File:** `groundtruth/ingestion/sipri.py`

Implemented `SIPRIIngestor` with:
- Local CSV parsing for military expenditure and arms transfer files
- Country normalization to ISO alpha-2
- Year range filtering
- Query API returning `{military_expenditure, arms_transfers}`

Added helper script:
- `scripts/download_sipri.py` (downloads CSVs from env-configured URLs)

### 4) FAS Loader
**File:** `groundtruth/ingestion/fas.py`

Implemented `FASIngestor` with:
- Static JSON load/query API for nuclear arsenal records
- Country-level lookup by ISO code

Added static dataset:
- `data/fas_nuclear.json` with 9 nuclear states

### 5) AI Synthesis Engine
**File:** `groundtruth/synthesis/engine.py`

Implemented `ContextEngine` with:
- Provider switch (`ollama` / `anthropic`) via `SYNTHESIS_PROVIDER` and API override
- Full prompt template using CIA Factbook, World Bank, GDELT, ACLED, SIPRI, FAS inputs
- Ollama HTTP integration (`/api/generate`)
- Anthropic async integration (`claude-sonnet-4-20250514`)
- Structured JSON extraction/parsing from model output
- Deterministic fallback report when model is unavailable

### 6) API Wiring
**File:** `groundtruth/api/main.py`

Wired full flow for:
- `GET /v1/context/{query}`
- `GET /v1/briefing/{topic}`
- `GET /v1/compare/{event_a}/{event_b}`

Behavior now:
1. Pulls country baseline from Sprint 1 ingestors (Factbook + World Bank)
2. Pulls event data from GDELT (+ ACLED when configured)
3. Pulls military context from SIPRI + FAS
4. Synthesizes briefing via `ContextEngine`
5. Returns structured report and source contribution metadata

Added required contract:
- `sources_available` field is returned in every synthesis response, showing `used` vs `skipped` plus reason/record counts.
- If any source is unavailable, synthesis still returns a briefing from available sources.

### 7) DB Persistence
**File:** `groundtruth/ingestion/persist.py`

Implemented `DatabasePersister` with:
- Approved source seeding from markdown (`seed_approved_sources`)
- Country + indicator upsert (`upsert_country_bundle`)
- Event persistence (`persist_events`)
- Context report persistence (`persist_context_report`)

API integration is best-effort/non-blocking:
- DB writes attempted when `DATABASE_URL` is configured
- Any DB failure degrades safely without breaking response generation

Added helper script:
- `scripts/seed_data.py`

---

## Tests Added

New test files:
- `tests/ingestion/test_gdelt.py`
- `tests/ingestion/test_acled.py`
- `tests/ingestion/test_sipri.py`
- `tests/ingestion/test_fas.py`
- `tests/synthesis/test_engine.py`

Updated tests:
- `tests/test_api.py` (now checks `report` and `sources_available` on synthesis endpoints)

### Test Result
```bash
60 passed
```

---

## Lint / Format Status

Ran and passing:
- `ruff check .`
- `black --check .`
- `isort --check .`

---

## Runtime Smoke Checks

Local API checks:
- `/v1/context/ukraine` → 200, synthesized report returned
- `/v1/context/south-china-sea` → 200, synthesized report returned
- `/v1/briefing/ukraine-war` → 200, comprehensive report + markdown returned
- `/v1/compare/ukraine-war/gaza-war` → 200, structured parallels/differences returned

All synthesis responses include `sources_available`.

---

## Key Decisions

1. **Graceful source degradation is first-class**
   Source fetch failures or missing credentials never block report generation.

2. **Provider failure fallback**
   If Ollama/Anthropic is unavailable or output is malformed, fallback synthesis returns a structured briefing.

3. **Persistence is optional at runtime**
   DB writes are non-blocking so API remains available in local/no-DB environments.

4. **Test mode avoids external calls**
   API skips external event calls under pytest (`PYTEST_CURRENT_TEST`) for deterministic CI.

---

## Known Gaps

1. **ACLED credential coverage**
   Full live ACLED validation depends on real credentials in `.env`.

2. **SIPRI data freshness**
   Loader expects local CSV files; automated fetch depends on valid direct download URLs in env.

3. **FastAPI startup event deprecation warning**
   Current code uses `@app.on_event("startup")`; migration to lifespan can be done in Sprint 3.

4. **AI output quality iteration**
   Prompt and schema handling are functional, but briefing quality tuning should continue with real production queries.

---

## Recommended Sprint 3 Follow-ups

1. Add auth/rate-limit middleware and tenant-aware quotas.
2. Move startup seeding to FastAPI lifespan and add health probes for provider reachability.
3. Add richer country normalization (ISO coverage) and source-specific schema adapters.
4. Add explicit response versioning for synthesis output schema.
5. Integrate Antigravity verification pipeline into the context response path.

