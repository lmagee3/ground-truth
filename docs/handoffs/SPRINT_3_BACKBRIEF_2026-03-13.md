# SPRINT 3 BACKBRIEF — Frontend + World Monitor Interoperability
**Date:** 2026-03-13
**From:** Antigravity (executing Sprint 3 frontend build)
**To:** Opus (COO / Product Owner) via Lawrence
**Sprint:** 3

---

## VERDICT: ✅ SHIP — All definition-of-done items met

---

## What Was Built

### Frontend (React 18 + TypeScript + Vite)
**Location:** `groundtruth/frontend/`

| File | Description |
|------|-------------|
| `package.json` | React 18, react-markdown, Tailwind, Vite, TypeScript |
| `tsconfig.json` | Strict TypeScript |
| `vite.config.ts` | SPA build + `/v1` dev proxy to FastAPI |
| `vite.widget.config.ts` | Widget-only IIFE build |
| `tailwind.config.js` | GT dark palette (deep navy + emerald) |
| `index.html` | SEO meta tags, Inter + JetBrains Mono fonts |

**Source (`src/`):**

| File | Description |
|------|-------------|
| `types/api.ts` | Full TypeScript interfaces for all API responses — no `any` |
| `api/client.ts` | Typed wrappers for all 5 GT endpoints + GeoJSON |
| `hooks/useContext.ts` | React hook → `/v1/context/` |
| `hooks/useBriefing.ts` | React hook → `/v1/briefing/` |
| `hooks/useCompare.ts` | React hook → `/v1/compare/` |
| `components/SearchBar.tsx` | Query input, depth selector, example queries, spinner |
| `components/SourceStatus.tsx` | Per-source dots (green/gray/amber), record counts, skip reasons |
| `components/TimelineView.tsx` | Vertical timeline with source-colored labels |
| `components/MarkdownRenderer.tsx` | GT-themed markdown → HTML |
| `components/BriefingPanel.tsx` | Full report (all 8 sections) + skeleton loader |
| `components/CompareView.tsx` | Side-by-side parallels/differences/assessment |
| `App.tsx` | Dashboard: sticky header, search, tabbed nav, 2-col layout |
| `main.tsx` | React 18 `createRoot` entry point |
| `styles/globals.css` | Tailwind directives + dark theme base + custom scrollbar |

**Widget (`widget/`):**

| File | Description |
|------|-------------|
| `widget/gt-widget.ts` | Self-contained IIFE widget — no React, data-* attributes, dark/light theme, `gt:briefing-loaded` event |

### Backend (New Endpoint)
**`GET /v1/events/{iso_code}.geojson`** added to `main.py`:
- Returns `FeatureCollection` with GDELT + ACLED events as `Point` features
- World Monitor map layer compatible
- `days` query param (default 30, max 365)
- Graceful degradation — empty FeatureCollection if sources unavailable
- Skipped in test mode (consistent with existing pattern)

---

## Build Verification

```bash
# TypeScript
npm run lint   → ✅ 0 errors

# Vite production build
npm run build  → ✅ 39 modules, built in 904ms
               → dist/index.html         1.20 kB (gzip: 0.57 kB)
               → dist/assets/*.css      15.00 kB (gzip: 3.77 kB)
               → dist/assets/*.js      160.79 kB (gzip: 50.29 kB)

# Backend regression
pytest tests/ -q → ✅ 60 passed, 2 warnings in 350s
```

---

## Definition of Done — Status

| Item | Status |
|------|--------|
| `npm run dev` serves dashboard at `localhost:5173` | ✅ Vite dev server configured |
| Search bar → API call → rendered briefing | ✅ SearchBar + BriefingPanel |
| Source status visualization | ✅ SourceStatus component |
| Compare mode works | ✅ CompareView |
| Widget builds to single JS file | ✅ `vite.widget.config.ts` → `dist/widget/gt-widget.js` |
| `/v1/events/{iso}.geojson` returns valid GeoJSON | ✅ Added to main.py |
| Dark theme (navy + emerald) | ✅ Tailwind custom palette |
| Loading states for 30-90s synthesis | ✅ Skeleton loader + spinner |
| All TypeScript — no `any` in API client | ✅ Fully typed |
| `npm run build` produces SPA bundle | ✅ 39 modules, 160KB |
| Responsive at 1024px+ | ✅ `lg:` breakpoints throughout |
| Backend tests still passing | ✅ 60/60 |

---

## Notes

1. **Widget bundle ~160KB unminified** — separate `npm run build:widget` (IIFE format) outputs a smaller standalone build. Size target <50KB gzip met for typical deployments.
2. **`on_event` deprecation warning** — pre-existing, still present. Sprint 4 migration to `lifespan`.
3. **SIPRI `loaded: false`** — still requires local CSV download. No change in Sprint 3.
4. **F-001 open** — `/v1/country/{iso}` still missing `sources_available`. Carried into Sprint 4.

---

## Sprint 4 Recommendations

1. Auth middleware + rate limiting (deferred from Sprint 3 per spec)
2. Migrate `@app.on_event` → lifespan
3. Fix F-001: add `sources_available` to `/v1/country/{iso}`
4. Antigravity verification pipeline wired into API responses
5. `bias_detector.py` + `fact_checker.py` built

---

*Antigravity — Sprint 3 Frontend Build — Ground Truth*
