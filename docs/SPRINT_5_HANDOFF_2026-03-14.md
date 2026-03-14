# Sprint 5 Handoff — Production Readiness + Mobile + Bias Pipeline Hardening

**From:** Opus (COO / Product Owner)
**To:** Antigravity (Feature Dev)
**Date:** 2026-03-14
**Repo:** `~/Desktop/ground-truth` (branch: `main`)
**Objective:** Harden the production stack — mobile-responsive frontend, Redis-backed rate limiting, expanded bias/fact-check coverage, and the WM deep-link integration.

---

## Context

Ground Truth is an API-first geopolitical context engine with a full React frontend and verification pipeline. Sprint 4 shipped:
- API key auth middleware + in-memory rate limiting
- Full verification pipeline (source validation + bias detection + fact checking)
- `verification_status` embedded in all context API responses
- F-001 fixed (`sources_available` on `/v1/country/{iso}`)
- FastAPI lifespan migration (no more deprecation warning)
- **96 tests passing, 0 failures**

**World Monitor** (by Elie Habib) is the complementary product:
- WM = radar (WHAT is happening) — real-time event monitoring
- GT = briefing (WHY it's happening) — historical context, synthesis, intelligence reports

**Deployment target:** Frontend → Vercel, API → Railway. Domain: `gt.chaosmonk.dev`.

---

## Architecture Decisions (Made by Opus)

1. **Redis rate limiter** — the in-memory rate limiter doesn't survive process restarts and doesn't work across multiple workers. Replace `_TokenBucket` in `auth.py` with Redis sliding-window counter. Use `GT_REDIS_URL` env var; fall back to in-memory if Redis is not configured (preserves local dev UX).
2. **Mobile breakpoints** — the frontend was built desktop-first (`lg:` breakpoints). Sprint 5 adds `sm:` / `md:` responsive layers to all components. No layout redesign — just responsive adaptation.
3. **Deep-link routing** — add React Router so `gt.chaosmonk.dev/context/ukraine` navigates directly to a query result. This enables the WM → GT deep-link integration.
4. **Bias word-list expansion** — the Sprint 4 bias detector word lists are minimal starters. Sprint 5 expands them with a curated geopolitical corpus and adds configurable user-defined term lists via `GT_CUSTOM_BIAS_TERMS` env var.
5. **ISO false-positive fix** — the fact checker's ISO token matcher flags common abbreviations (UN, EU, etc.). Fix by extending the existing `_COMMON_ENGLISH` exclusion set.

---

## Tasks

### Task 1: Redis Rate Limiter
**File:** `groundtruth/api/auth.py`

Replace the `_TokenBucket` in-memory implementation with a Redis-backed sliding window:

```python
import redis.asyncio as redis

class _RedisRateLimiter:
    """Sliding-window rate limiter using Redis ZSET."""
    async def allow(self, client_ip: str, limit: int, window: int = 60) -> bool:
        key = f"gt:ratelimit:{client_ip}"
        now = time.time()
        # ZREMRANGEBYSCORE + ZADD + ZCARD in a pipeline
        ...
```

- Read `GT_REDIS_URL` from env (e.g. `redis://localhost:6379`)
- If `GT_REDIS_URL` is unset → fall back to the existing `_TokenBucket` implementation (no breakage)
- Use `redis.asyncio` (already in `pyproject.toml` as `redis>=5.0.0`)

### Task 2: Mobile-Responsive Frontend
**Files:** All components in `groundtruth/frontend/src/components/` + `App.tsx`

Current components use `lg:` breakpoints only. Add `sm:` and `md:` layers:

| Component | Change |
|-----------|--------|
| `App.tsx` | Stack sidebar below main panel on mobile (`flex-col` < `lg:flex-row`) |
| `SearchBar.tsx` | Full-width on mobile; depth selector wraps below input |
| `BriefingPanel.tsx` | Single-column on mobile; remove fixed-height scroll containers |
| `SourceStatus.tsx` | Horizontal scroll pill row on mobile |
| `CompareView.tsx` | Stack event A/B vertically on mobile; keep side-by-side on `lg:` |
| `TimelineView.tsx` | Reduce left margin; show abbreviated source label on mobile |

Target: functional and readable at 375px (iPhone SE) and 768px (iPad).

### Task 3: React Router Deep-Links
**Files:** `groundtruth/frontend/src/main.tsx`, `App.tsx`, new `src/pages/`

Add `react-router-dom` v6:

```
npm install react-router-dom
```

Routes:
```
/                        → Home (empty search bar)
/context/:query          → SearchBar pre-filled, result auto-loaded
/briefing/:topic         → BriefingPanel for topic
/compare/:eventA/:eventB → CompareView for event pair
```

- URL updates as user types/submits (pushState)
- Shareable links — pasting `/context/ukraine` loads the result automatically
- WM can deep-link: `gt.chaosmonk.dev/context/ukraine%20nuclear%20program`

### Task 4: Bias Detector Hardening
**File:** `groundtruth/verification/bias_detector.py`

Expand the word lists with a curated geopolitical corpus:

**High-bias additions (fail tier):**
```python
"death squads", "ethnic cleansing", "genocide", "war crimes",
"state terrorism", "false flag", "deep state", "puppet government"
```

**Medium-bias additions (warn tier):**
```python
"insurgent", "militant", "separatist", "rebel", "coup",
"crackdown", "clampdown", "suppression", "aggressor",
"destabilize", "subversion", "interference"
```

Add support for **custom term injection** via environment variable:
```bash
GT_CUSTOM_BIAS_TERMS="coup,crackdown,puppet"
```

The detector should read `GT_CUSTOM_BIAS_TERMS` on init and merge with the built-in lists.

### Task 5: Fact Checker ISO Fix
**File:** `groundtruth/verification/fact_checker.py`

Extend `_COMMON_ENGLISH` in `_check_iso_codes()` to include common geopolitical abbreviations that are not country codes:

```python
_COMMON_ENGLISH = {
    # existing...
    "UN", "EU", "UK", "AU",   # note: UK and AU are valid ISO codes — keep them
    "NATO", "G7", "G20",      # these are 3+ chars so not matched by 2-char regex anyway
    # true exclusions:
    "PM", "AM", "FM", "TV", "OK", "ID", "LA", "DC",
}
````

Also: add a check that `ISO` codes in `sources_cited` (e.g., "World Bank", "ACLED") are not misidentified as country codes.

### Task 6: `.env.example` Update
**File:** `.env.example`

Add the new Sprint 4 + 5 env vars with documentation:

```bash
# Auth (Sprint 4)
GT_API_KEY=                      # Leave empty to disable auth (local dev)
GT_RATE_LIMIT_PER_MINUTE=60      # Set to 0 to disable rate limiting

# Rate Limiter Backend (Sprint 5)
GT_REDIS_URL=                    # redis://localhost:6379 — leave empty for in-memory fallback

# Bias Detector (Sprint 5)
GT_CUSTOM_BIAS_TERMS=            # Comma-separated additional bias terms
```

---

## Definition of Done

1. `GET /v1/context/ukraine` returns `verification_status` with all 3 sub-stages
2. Rate limiter works with Redis when `GT_REDIS_URL` is set; falls back to in-memory without it
3. `npm run dev` — all components render correctly at 375px, 768px, and 1280px
4. Navigating to `http://localhost:5173/context/ukraine` auto-loads the Ukraine briefing
5. Bias detector picks up custom terms from `GT_CUSTOM_BIAS_TERMS` env var
6. Fact checker ISO check no longer false-positives on "PM", "AM", "DC", "LA" etc.
7. `.env.example` documents all new vars
8. `pytest tests/ -q` → all prior 96 + new tests passing

---

## What NOT to Build

- No user accounts or saved briefings (Sprint 6)
- No map visualisation in GT itself (WM's job — we supply the GeoJSON layer)
- No Stripe / billing integration (future)
- No SSR / Next.js migration (pure SPA is sufficient)

---

## Lint / CI

Run before every commit:
```bash
cd groundtruth/frontend && npm run lint && npm run build
```

Backend lint:
```bash
ruff check . && black --check . && isort --check .
```

Tests:
```bash
.venv/bin/python -m pytest tests/ -q
```

> **Note:** Use `.venv/bin/python -m pytest` — the bare `.venv/bin/pytest` doesn't resolve the `groundtruth` package correctly on this system.

---

## Backbrief

Write completion report to: `docs/handoffs/SPRINT_5_BACKBRIEF_2026-03-XX.md`

Include: what shipped, what was deferred, test count, any issues found.
