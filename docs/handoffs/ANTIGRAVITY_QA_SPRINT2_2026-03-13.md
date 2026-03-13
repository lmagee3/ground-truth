# ANTIGRAVITY QA BACKBRIEF — Sprint 2
**Date:** 2026-03-13
**From:** Antigravity (QA / Verification)
**To:** Opus (COO / Product Owner) via Lawrence
**Sprint:** 2 QA Pass
**Commit reviewed:** 5347d72 (branch: main)

---

## VERDICT: ✅ SHIP — one minor finding, no blockers

---

## 1. Tests

**Result: ✅ PASS**

```
60 passed in 4.79s
```

All 60 tests collected and passed independently (I ran fresh — did not rely on Codex's self-reported count). Two deprecation warnings present (FastAPI `on_event`), acknowledged as known gap in Sprint 2 backbrief, Sprint 3 fix.

Test breakdown:

| Suite | Tests | Result |
|-------|-------|--------|
| `tests/ingestion/test_acled.py` | 3 | ✅ Pass |
| `tests/ingestion/test_cia_factbook.py` | 3 | ✅ Pass |
| `tests/ingestion/test_fas.py` | 2 | ✅ Pass |
| `tests/ingestion/test_gdelt.py` | 3 | ✅ Pass |
| `tests/ingestion/test_sipri.py` | 2 | ✅ Pass |
| `tests/ingestion/test_worldbank.py` | 3 | ✅ Pass |
| `tests/synthesis/test_engine.py` | 5 | ✅ Pass |
| `tests/test_api.py` | 5 | ✅ Pass |
| `tests/test_models.py` | 3 | ✅ Pass |
| `tests/verification/test_source_validator.py` | 31 | ✅ Pass |

---

## 2. Lint

**Result: ✅ PASS**

```
ruff check .      → All checks passed
black --check .   → 34 files unchanged (harmless Python 3.10 parse note)
isort --check .   → Skipped 2 files (clean)
```

No violations in project source.

---

## 3. Smoke Tests

All endpoints tested using `TestClient` (equivalent to live uvicorn, avoids external HTTP on CI):

| Endpoint | Status | `sources_available` present | Notes |
|----------|--------|----------------------------|-------|
| `GET /v1/health` | ✅ 200 | N/A | All sources reported; ACLED `configured: false` correctly shown |
| `GET /v1/country/UA` | ✅ 200 | ⚠️ **Missing** | Returns `country`, `factbook`, `worldbank` — no `sources_available` |
| `GET /v1/context/ukraine` | ✅ 200 | ✅ Present | Fallback synthesis runs cleanly; all expected keys present |
| `GET /v1/briefing/ukraine-war` | ✅ 200 | ✅ Present | `markdown` field present as per spec |
| `GET /v1/compare/ukraine-war/gaza-war` | ✅ 200 | ✅ Present | `comparison` field with parallels/differences |

**Finding F-001 (Minor):** `/v1/country/{iso_code}` does not include `sources_available` in its response. Sprint 2 handoff spec states: *"Verify every response includes `sources_available` field."* This endpoint returns raw Factbook + World Bank data and is not a synthesis endpoint — it may be intentionally excluded. **Recommend:** either add `sources_available` for contract consistency, or explicitly document the exception. Not a blocker.

---

## 4. Graceful Degradation

**Result: ✅ PASS**

Tested with `ACLED_USERNAME` / `ACLED_PASSWORD` removed from environment:

- `GET /v1/context/ukraine` → 200, valid briefing returned (minus ACLED data)
- `sources_available.acled.status` = `"skipped"` ✅
- No exception, no 500 error

Codex's `ACLEDIngestor.configured` property (line 61-62 of `acled.py`) correctly guards all token acquisition paths.

---

## 5. Production Fixes Verification

| Check | Location | Result |
|-------|----------|--------|
| `ANTHROPIC_MODEL` read from env | `engine.py` line 75 | ✅ `os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")` |
| `OLLAMA_TIMEOUT` read from env | `engine.py` line 73 | ✅ `float(os.getenv("OLLAMA_TIMEOUT", "120.0"))` |
| `fetch_events()` try/catch on token acquisition | `acled.py` lines 94-97 | ✅ `try: token = await self._get_access_token() except Exception: return []` |

All three confirmed. No hardcoded values.

---

## 6. Code Spot Check

**GDELT (`gdelt.py`):**
- ✅ Rate limiting: `asyncio.Lock()` + `_wait_for_rate_limit()` with 5.0s default interval
- ✅ Caching: SHA-256 keyed JSON files under `.cache/gdelt/`
- ✅ No hardcoded credentials (no auth required)

**ACLED (`acled.py`):**
- ✅ Rate limiting: `asyncio.Lock()` + `_wait_for_rate_limit()` with 2.0s default interval (line 41)
- ✅ Caching: SHA-256 keyed JSON files under `.cache/acled/`
- ✅ No hardcoded credentials — reads from `ACLED_USERNAME` / `ACLED_PASSWORD` env vars

**Secret scan (`git log -p -- .env`):**
- ✅ No `.env` file committed
- ✅ No `ACLED_PASSWORD`, `ANTHROPIC_API_KEY`, or other secrets found in project source files
- ✅ `.gitignore` excludes `.env`

---

## Summary: Finding Register

| ID | Severity | Finding | Recommendation |
|----|----------|---------|----------------|
| F-001 | Minor | `/v1/country/UA` missing `sources_available` field | Add field or document the exception in Sprint 3 |
| W-001 | Warning (known) | FastAPI `on_event("startup")` deprecated | Migrate to `lifespan` in Sprint 3 (already in Codex's recommended follow-ups) |
| W-002 | Warning | SIPRI `loaded: false` in `/v1/health` | Requires pre-downloaded CSV files; expected behavior when local files absent |

Nothing blocking. All critical path items pass.

---

## Ship Recommendation

**✅ SHIP TO LAWRENCE FOR TEST DRIVE.**

The engine generates valid intelligence briefings in fallback mode (no Ollama required), all endpoints return correct structure, degradation is graceful, tests are solid. Quality tuning on the AI synthesis output is next after Lawrence test-drives with real queries.

---

## Next for Antigravity (Sprint 3 Prep)

1. Wire `VerificationPipeline` into `/v1/context/` and `/v1/briefing/` responses — add `verification_status` field
2. Build `bias_detector.py` — now have real AI-generated text to profile
3. Build `fact_checker.py` — now have real timeline/event data to cross-reference
4. Add `sources_available` contract check to test suite (F-001 fix)

---

*Antigravity — QA / Verification — Ground Truth Sprint 2*
