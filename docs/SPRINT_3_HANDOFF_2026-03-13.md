# Sprint 3 Handoff — Frontend + World Monitor Interoperability

**From:** Opus (COO / Product Owner)
**To:** Sonnet (Feature Dev)
**Date:** 2026-03-13
**Repo:** `~/Desktop/ground-truth` (branch: `main`)
**Objective:** Build a production-ready React frontend and interoperability layer so Ground Truth can ship as a standalone product AND integrate with World Monitor's ecosystem.

---

## Context

Ground Truth is an API-first geopolitical context engine. Sprint 1-2 delivered the full backend: 6 data sources (World Bank, CIA Factbook, GDELT, ACLED, SIPRI, FAS), AI synthesis engine (Ollama local + Claude API), and a working FastAPI with 7 endpoints. 60 tests passing, CI green.

**World Monitor** (by Elie Habib) is the complementary product:
- WM = radar (WHAT is happening) — real-time event monitoring, 435+ RSS feeds, military tracking
- GT = briefing (WHY it's happening) — historical context, multi-source synthesis, intelligence reports

WM stack: Vanilla TypeScript, Vite, Vercel Edge Functions, proto-first API (`POST /api/{domain}/v1/{rpc-name}`), GeoJSON layers, globe.gl/deck.gl maps, Ollama/Groq AI. No formal plugin system, but programmatic API access exists.

**Design goal:** GT frontend works standalone AND can be embedded/consumed by World Monitor or any third party.

---

## Architecture Decisions (Made by Opus)

1. **React 18 + TypeScript + Vite** — Matches our pyproject.toml spec. React for component reuse and widget export. TypeScript for WM compatibility.
2. **Tailwind CSS** — Fast styling, utility-first, no CSS framework lock-in.
3. **No Next.js** — Overkill. Pure SPA served by Vercel or any static host. API is separate (FastAPI on Railway).
4. **Embeddable widget build** — Vite outputs both a full SPA and a standalone `gt-widget.js` that any page can embed.
5. **GeoJSON API endpoint** — New backend endpoint for map layer compatibility with WM.
6. **CORS already configured** — `allow_origins=["*"]` in main.py. Ready for cross-origin consumption.

---

## Tasks

### Task 1: Project Scaffolding
**File:** `groundtruth/frontend/`

```
groundtruth/frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── public/
│   └── favicon.ico
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   └── client.ts          # GT API client (typed)
│   ├── components/
│   │   ├── SearchBar.tsx       # Query input + depth selector
│   │   ├── BriefingPanel.tsx   # Main briefing display
│   │   ├── SourceStatus.tsx    # sources_available visualization
│   │   ├── TimelineView.tsx    # Timeline events display
│   │   ├── CompareView.tsx     # Side-by-side comparison
│   │   ├── MarkdownRenderer.tsx # Briefing markdown display
│   │   └── Widget.tsx          # Embeddable standalone widget
│   ├── hooks/
│   │   ├── useContext.ts       # /v1/context/ query hook
│   │   ├── useBriefing.ts     # /v1/briefing/ query hook
│   │   └── useCompare.ts      # /v1/compare/ query hook
│   ├── types/
│   │   └── api.ts             # TypeScript interfaces matching API responses
│   └── styles/
│       └── globals.css
└── widget/
    └── gt-widget.ts           # Standalone embeddable widget entry point
```

Dependencies:
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-markdown": "^9.0.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

### Task 2: API Client (Typed)
**File:** `src/api/client.ts`

Typed client wrapping all GT API endpoints:

```typescript
const API_BASE = import.meta.env.VITE_GT_API_URL || 'http://localhost:8000';

export interface ContextResponse {
  query: string;
  depth: string;
  region: string | null;
  country: { iso_code: string; name: string };
  report: BriefingReport;
  sources: string[];
  sources_available: Record<string, SourceStatus>;
}

export interface BriefingReport {
  title: string;
  summary: string;
  background: string;
  timeline: TimelineEvent[];
  economic_context: string;
  military_context: string;
  perspectives: Perspective[];
  current_assessment: string;
  sources_cited: string[];
  confidence_notes: string;
  sources_available: Record<string, SourceStatus>;
}

export interface SourceStatus {
  status: 'used' | 'skipped';
  records: number;
  reason: string | null;
}

export interface TimelineEvent {
  year: number;
  event: string;
  source: string;
}

export interface Perspective {
  framework: string;
  argument: string;
  evidence: string;
}

export async function fetchContext(query: string, depth?: string, provider?: string): Promise<ContextResponse>;
export async function fetchBriefing(topic: string, format?: string, provider?: string): Promise<any>;
export async function fetchComparison(eventA: string, eventB: string, provider?: string): Promise<any>;
export async function fetchHealth(): Promise<any>;
export async function fetchCountry(iso: string): Promise<any>;
```

### Task 3: Main Dashboard (SPA)
**File:** `src/App.tsx`

Layout:
```
┌─────────────────────────────────────────────────────┐
│  GROUND TRUTH — Geopolitical Context Engine    [?]  │
├─────────────────────────────────────────────────────┤
│  [Search: Enter country, conflict, or topic...]     │
│  Depth: [Brief] [Standard] [Comprehensive]          │
├──────────────────────────────┬──────────────────────┤
│                              │  SOURCE STATUS       │
│  BRIEFING PANEL              │  ■ World Bank ✓      │
│                              │  ■ CIA Factbook ✓    │
│  # Title                     │  ■ GDELT ✓           │
│  ## Summary                  │  ■ ACLED ✓           │
│  ## Background               │  ■ SIPRI ✓           │
│  ## Timeline                 │  ■ FAS ✓             │
│  ## Economic Context         │                      │
│  ## Military Context         ├──────────────────────┤
│  ## Perspectives             │  CONFIDENCE          │
│  ## Current Assessment       │  Sources: 5/6        │
│                              │  Provider: ollama    │
│                              │  Depth: standard     │
├──────────────────────────────┴──────────────────────┤
│  [Compare Mode] Enter two events to compare...      │
└─────────────────────────────────────────────────────┘
```

**Design principles:**
- Dark theme (matches WM aesthetic — dark navy/charcoal, green accents)
- Military briefing typography — monospace headers, clean sans-serif body
- No clutter. Information density > decoration.
- Responsive — works on desktop and tablet
- Loading state: pulsing skeleton while Ollama synthesizes (can take 30-90s)

**Color palette:**
- Background: `#0a0f1a` (deep navy)
- Surface: `#111827` (card backgrounds)
- Primary text: `#e5e7eb` (light gray)
- Accent: `#10b981` (emerald green — matches GT brand)
- Warning: `#f59e0b` (amber for skipped sources)
- Border: `#1f2937`
- Source "used": `#10b981` (green dot)
- Source "skipped": `#6b7280` (gray dot)

### Task 4: Source Status Component
**File:** `src/components/SourceStatus.tsx`

Visual display of `sources_available` from API response. Each source shows:
- Colored dot (green = used, gray = skipped, amber = error)
- Source name
- Record count
- Reason if skipped

This is a key differentiator — users can see exactly which primary sources contributed to their briefing.

### Task 5: Compare View
**File:** `src/components/CompareView.tsx`

Side-by-side comparison mode. User enters two events/topics, hits the `/v1/compare/` endpoint, sees:
- Left panel: Event A briefing summary
- Right panel: Event B briefing summary
- Center: Parallels, differences, assessment

### Task 6: Embeddable Widget
**File:** `widget/gt-widget.ts`

A standalone JavaScript widget that any website can embed:

```html
<!-- Drop this on any page -->
<div id="groundtruth-widget" data-query="ukraine" data-depth="brief"></div>
<script src="https://gt.chaosmonk.dev/widget/gt-widget.js"></script>
```

The widget:
- Self-contained (no React dependency in the bundle — use Preact or vanilla DOM)
- Renders a compact briefing card with source attribution
- Configurable via `data-*` attributes (query, depth, theme, api-url)
- Emits custom events (`gt:briefing-loaded`, `gt:source-click`) for host page integration
- CORS-compatible — works on any domain
- Light theme option for sites that aren't dark-mode

**Vite config** outputs two builds:
1. `dist/` — Full SPA
2. `dist/widget/gt-widget.js` — Standalone widget (single file, <50KB gzipped)

### Task 7: GeoJSON API Endpoint (Backend)
**File:** `groundtruth/api/main.py`

Add endpoint for map layer compatibility:

```python
@app.get("/v1/events/{iso_code}.geojson")
async def get_events_geojson(iso_code: str, days: int = 30):
    """Return GDELT + ACLED events as GeoJSON FeatureCollection.

    Compatible with World Monitor's map layer format.
    Each feature includes: geometry (point), properties (event_type,
    date, description, source, actors).
    """
```

This lets World Monitor (or any map tool) overlay GT's conflict data as a toggleable layer.

### Task 8: OpenAPI Schema Polish
**File:** `groundtruth/api/main.py`

Add proper Pydantic response models so `/docs` generates a clean, typed OpenAPI spec. This makes it easy for WM or any third party to auto-generate a client from our schema.

---

## World Monitor Integration Points

| Integration | How | Priority |
|-------------|-----|----------|
| **Briefing embed** | `gt-widget.js` dropped into WM page or iframe | HIGH |
| **Map layer** | `/v1/events/{iso}.geojson` consumed by WM's layer system | HIGH |
| **API consumption** | WM fetches GT context via typed client | MEDIUM |
| **Shared GDELT data** | Both use GDELT; GT adds synthesis layer on top | ALREADY DONE |
| **Deep link** | WM event click → `gt.chaosmonk.dev/context/{query}` | LOW (URL routing) |
| **AI provider chain** | Both support Ollama; GT adds Anthropic as premium tier | ALREADY DONE |

---

## Deployment Target

- **Frontend:** Vercel (free tier) — static SPA + widget CDN
- **API:** Already running on localhost, deploy to Railway (free tier → paid when traffic justifies)
- **Domain:** `gt.chaosmonk.dev` or `groundtruth.chaosmonk.dev` (Lawrence to configure DNS)

---

## Definition of Done

1. `npm run dev` serves the dashboard at `localhost:5173`
2. Search bar → API call → rendered briefing with source status
3. Compare mode works for any two topics
4. Widget builds to single JS file, embeddable on external pages
5. `/v1/events/{iso}.geojson` returns valid GeoJSON FeatureCollection
6. Dark theme matches Ground Truth / World Monitor aesthetic
7. Loading states handle 30-90s Ollama synthesis times
8. All TypeScript — no `any` types in the API client
9. `npm run build` produces both SPA and widget bundles
10. Responsive layout works on 1024px+ screens

---

## What NOT to Build

- No authentication (Sprint 4)
- No rate limiting UI (Sprint 4)
- No user accounts or saved briefings (Sprint 4)
- No map visualization in GT itself (that's WM's job — we provide the data layer)
- No server-side rendering (pure SPA is fine)
- No mobile-first design (desktop/tablet priority — mobile is Sprint 4)

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

---

## Backbrief

Write completion report to: `docs/handoffs/SONNET_SPRINT3_BACKBRIEF_2026-03-XX.md`

Include: what shipped, what was deferred, test coverage, screenshots, any issues found.
