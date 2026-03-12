# SPRINT 1 BACKBRIEF — Tasks 1-4 (Ingestion + Models + API)
**Date:** 2026-03-12  
**From:** Codex (Implementation)  
**To:** Opus (COO / Product Owner) via Lawrence  
**Sprint:** 1 — Tasks 1-4 Complete

---

## What Was Built

### Task 1 — World Bank Ingestion
**File:** `groundtruth/ingestion/worldbank.py`

Implemented `WorldBankIngestor` with:
- Async `httpx` client integration for World Bank v2 endpoints
- Support for required indicators:
  - `MS.MIL.XPND.GD.ZS`
  - `MS.MIL.XPND.CD`
  - `NY.GDP.MKTP.CD`
  - `NY.GDP.MKTP.KD.ZG`
  - `NE.TRD.GNFS.ZS`
  - `SP.POP.TOTL`
  - `FP.CPI.TOTL.ZG`
  - `BN.CAB.XOKA.CD`
- Country + date range querying
- Local response caching under `.cache/worldbank/`
- Client-side rate limiting (1 request/second)
- Structured parsed output via `IndicatorPoint`

### Task 2 — CIA Factbook Ingestion
**File:** `groundtruth/ingestion/cia_factbook.py`

Implemented `CIAFactbookIngestor` with:
- Dataset load + cache (`.cache/cia_factbook.json`)
- Parsing country profiles into `CountryProfile`
- Extraction of:
  - government
  - military/security
  - geography
  - economy
  - demographics
  - transnational issues
  - international organization participation
- Country normalization to ISO for cross-reference
- Compatibility with current JSON schema from:
  `https://raw.githubusercontent.com/iancoleman/cia_world_factbook_api/master/data/factbook.json`

### Task 3 — PostgreSQL Models + Alembic
**Files:** `groundtruth/models.py`, `alembic/`, `alembic.ini`

Added SQLAlchemy models:
- `Country`
- `Indicator`
- `Event`
- `ContextReport`
- `ApprovedSource`

Added:
- Country ↔ Indicator relationship
- uniqueness constraint for indicator points
- parser helper to seed approved sources from `docs/APPROVED_SOURCES.md`

Alembic setup:
- `alembic/env.py`
- `alembic/script.py.mako`
- initial migration `alembic/versions/20260312_0001_initial.py`

Packaging fix included:
- `pyproject.toml` now explicitly limits package discovery to `groundtruth*` to avoid picking up top-level `alembic` as a Python package.

### Task 4 — Wire Ingestion Into API
**File:** `groundtruth/api/main.py`

Implemented:
- `GET /v1/country/{iso_code}`  
  Returns combined Factbook + World Bank data
- `GET /v1/context/{query}`  
  Returns raw country context (Factbook + World Bank) for current sprint
- `GET /v1/timeline/{region}`  
  Returns indicator time series by configured regional country groups
- `GET /v1/health`  
  Returns source load state and cache freshness timestamps

---

## Tests Added / Updated

New tests:
- `tests/ingestion/test_worldbank.py`
- `tests/ingestion/test_cia_factbook.py`
- `tests/test_models.py`

Existing tests kept passing:
- `tests/test_api.py`
- `tests/verification/test_source_validator.py`

Result:
```bash
45 passed
```

---

## Runtime Verification

`uvicorn groundtruth.api.main:app` startup check:
- App starts cleanly
- Startup and shutdown complete with no import/runtime errors

API smoke check:
- `/v1/country/US` returns HTTP 200
- Response contains populated World Bank indicator series (all 8 categories)
- Response contains real Factbook profile fields for United States
- `/v1/country/CN` returns HTTP 200 with real Factbook + World Bank data

---

## Architectural Decisions

1. **Cache-first ingestion clients**  
   Both ingestion modules persist raw upstream payloads under `.cache/` for speed and reduced source load.

2. **Best-effort API behavior during source outages**  
   API endpoints return structured payloads even if one source is temporarily unavailable, instead of hard-failing the whole request.

3. **Schema-aligned model design for Sprint 1 scope**  
   Core entities were created as specified, without overextending fields before Sprint 2 sources arrive.

4. **Mirror update for CIA dataset reliability**  
   The original listed mirror path returned 404. Ingestion now targets a currently live public JSON mirror.

---

## Known Gaps / Follow-ups

1. **ISO normalization map is intentionally minimal**  
   Covers key countries used in sprint testing; expand mapping for full 260-country precision.

2. **Source freshness metadata is cache-file based**  
   `/v1/health` reports cache timestamps, not per-record provenance timestamps.

3. **DB write pipeline not yet wired into API endpoints**  
   Models/migrations are in place; ingest-to-DB persistence is a natural Sprint 2 enhancement.

---

## Recommended Next Steps (Sprint 2)

1. Add DB persistence jobs for World Bank + Factbook loaders.
2. Seed `approved_sources` table automatically from markdown parser during migration/bootstrap.
3. Integrate verification pipeline output (`verification_status`) into context responses.
4. Expand ISO mapping and Factbook field normalization for full-country coverage.
5. Add ingestion refresh command(s) under `scripts/` for scheduled updates.
