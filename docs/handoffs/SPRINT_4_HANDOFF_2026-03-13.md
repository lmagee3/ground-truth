# Sprint 4 Handoff — UI Reskin + Ollama Fix + AI Query Intelligence
**From:** Opus (COO / Product Owner)
**To:** Codex (Infrastructure / Implementation)
**Date:** 2026-03-13
**Priority:** HIGH — production blocker

---

## Context
Sprint 3 delivered a working React frontend. Two problems:
1. **Ollama synthesis is failing** — queries return fallback mode (`ollama_error:` empty string). 4/6 data sources light up (World Bank 376 records, CIA Factbook 14, SIPRI 10, FAS 1), but the AI synthesis never generates. This is the #1 blocker.
2. **UI doesn't match our brand** — current frontend is functional but generic. Needs to match the design language from `docs/Ground_Truth_Mindmap.html` (dark terminal aesthetic, monospace, green accent, card-based layout).
3. **Query intelligence** — queries like "US-Iran Tensions background" need AI-powered parsing so the engine understands context, extracts countries, and returns factual deep-dive briefings.

---

## TASK 1: Fix Ollama Connection (CRITICAL — DO THIS FIRST)

### Problem
`/v1/context/iran?depth=standard` returns fallback synthesis with `ollama_error:` (empty error message). The engine hits Ollama but gets nothing back — likely a timeout, connection refused, or empty response.

### Investigation Steps
1. Verify Ollama is running: `curl http://localhost:11434/api/tags`
2. Test Ollama directly: `curl -X POST http://localhost:11434/api/generate -d '{"model":"llama3.1","prompt":"Hello","stream":false}' | head -100`
3. Check `.env` has `SYNTHESIS_PROVIDER=ollama` and `OLLAMA_MODEL=llama3.1`
4. Check the `engine.py` error path — the `ollama_error:` is empty, which means the exception has no message. Add better error logging.

### Fix Required in `groundtruth/synthesis/engine.py`
The `_call_ollama()` method catches exceptions but the error message is empty. Two likely causes:

**A. Timeout** — `OLLAMA_TIMEOUT` defaults to 120s but llama3.1 with an 8K token `num_predict` on a MacBook may need more time. The prompt is now much larger (includes merged data from multiple countries).
- Fix: Increase default `OLLAMA_TIMEOUT` to `300.0` (5 minutes)
- Also: the `httpx.AsyncClient(timeout=self.ollama_timeout)` uses a single float which sets ALL timeouts (connect + read + write). For Ollama, the connect should be fast but the read (waiting for generation) needs to be long.
- Better fix:
```python
timeout = httpx.Timeout(10.0, read=self.ollama_timeout)  # 10s connect, long read
async with httpx.AsyncClient(timeout=timeout) as client:
```

**B. Empty response** — Ollama sometimes returns `{"response": ""}` if the model can't handle the prompt size.
- Fix: Add a check after the response:
```python
result = str(body.get("response", ""))
if not result.strip():
    raise RuntimeError(f"Ollama returned empty response for model {self.ollama_model}")
```

**C. Better error capture** — change the exception handler to capture the full error:
```python
except Exception as exc:  # noqa: BLE001
    llm_error = f"ollama_error: {type(exc).__name__}: {exc}"
```
Do this for BOTH the ollama and anthropic error handlers in `generate_context()`.

### Verification
After fix, restart uvicorn and run:
```bash
curl -s 'http://localhost:8000/v1/context/iran?depth=brief' | python3 -m json.tool | head -50
```
Should see actual synthesized content in `background`, `timeline`, `summary` fields — NOT the fallback template text.

---

## TASK 2: UI Reskin to Match Mindmap Aesthetic

### Design Reference
File: `docs/Ground_Truth_Mindmap.html` — open in browser to see the exact aesthetic.

### Design System (extract from mindmap HTML)

**Colors:**
| Token | Hex | Use |
|-------|-----|-----|
| `gt-bg` | `#0a0a0f` | Body background (CHANGE from current `#0a0f1a`) |
| `gt-surface` | `#0d0d14` | Card/panel backgrounds |
| `gt-border` | `#1a1a2e` | Borders |
| `gt-text` | `#e0e0e0` | Primary text |
| `gt-muted` | `#999` / `#888` / `#666` | Secondary/tertiary text |
| `gt-accent` | `#00ff88` | Primary accent (CHANGE from current `#10b981`) |
| `gt-warn` | `#ff6b35` | Warning/orange accent (tagline, highlights) |
| `gt-danger` | `#ff5588` | Error/critical |
| `gt-blue` | `#3388ff` | Info/secondary accent |
| `gt-purple` | `#aa55ff` | Tertiary accent |

**Tag Colors (for source status badges):**
| Tag | Background | Text | Border |
|-----|-----------|------|--------|
| API | `#00ff8820` | `#00ff88` | `#00ff8840` |
| CSV | `#3388ff20` | `#3388ff` | `#3388ff40` |
| Free | `#ffaa0020` | `#ffaa00` | `#ffaa0040` |
| Key Required | `#ff558820` | `#ff5588` | `#ff558840` |
| Real-time | `#00ccff20` | `#00ccff` | `#00ccff40` |
| Historical | `#cc88ff20` | `#cc88ff` | `#cc88ff40` |

**Typography:**
- Primary font: `'SF Mono', 'Fira Code', 'Consolas', monospace` — ALL text is monospace
- NO sans-serif fonts. The current Inter font must be removed.
- Headers: `letter-spacing: 4px`, `text-transform: uppercase`
- Section titles: `font-size: 1.3em`, `color: #00ff88`, with bottom border `1px solid #1a2a1f`
- Body text: `font-size: 0.82em`, `line-height: 1.6`, `color: #999`

**Layout:**
- Max width: `1400px` centered
- Cards: `background: #0d0d14`, `border: 1px solid #1a1a2e`, `border-radius: 8px`, `padding: 20px`
- Card hover: `border-color: #00ff8855`, `transform: translateY(-2px)`
- Section spacing: `margin-bottom: 40px`

### Files to Modify

#### `tailwind.config.js`
Update the color palette to match the mindmap:
```js
colors: {
  gt: {
    bg: '#0a0a0f',        // was #0a0f1a
    surface: '#0d0d14',    // was #111827
    surface2: '#111',      // dark card variant
    border: '#1a1a2e',     // was #1f2937
    text: '#e0e0e0',       // was #e5e7eb
    muted: '#888',         // was #9ca3af
    accent: '#00ff88',     // was #10b981 — THIS IS THE BIG ONE
    'accent-dim': '#00ff8855',
    warn: '#ff6b35',       // orange accent
    danger: '#ff5588',     // was #ef4444
    blue: '#3388ff',       // new — info accent
    purple: '#aa55ff',     // new — tertiary
    skipped: '#666',
  },
},
fontFamily: {
  mono: ['"SF Mono"', '"Fira Code"', '"Consolas"', 'monospace'],
  // REMOVE sans entirely — everything is monospace
},
```

#### `globals.css`
- Change Google Fonts import to Fira Code only (drop Inter):
  ```css
  @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&display=swap');
  ```
- Update `html` styles:
  ```css
  html {
    background-color: #0a0a0f;
    color: #e0e0e0;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  }
  ```

#### `App.tsx` — Header Reskin
Current header is minimal. Match the mindmap header:
```tsx
<header className="text-center py-10 px-5 border-b border-gt-border">
  <h1 className="text-4xl font-bold text-gt-accent tracking-[4px] uppercase mb-2">
    GROUND TRUTH
  </h1>
  <div className="text-gt-muted text-sm tracking-[2px] uppercase">
    Geopolitical Context Engine — By Chaos Monk
  </div>
  <div className="text-gt-warn text-base mt-3 italic">
    "The intelligence briefing behind the radar blip"
  </div>
</header>
```

#### `App.tsx` — Tab Navigation Reskin
Match the mindmap tab style:
```tsx
<div className="flex gap-1 flex-wrap mb-8">
  {tabs.map(t => (
    <button
      key={t.id}
      onClick={() => setTab(t.id)}
      className={`
        bg-gt-surface2 border border-gt-border text-gt-muted
        px-5 py-2.5 font-mono text-xs tracking-[1px] rounded
        transition-all cursor-pointer
        ${tab === t.id
          ? 'bg-[#00ff8815] border-gt-accent text-gt-accent'
          : 'hover:border-gt-accent hover:text-gt-accent'
        }
      `}
    >
      {t.label}
    </button>
  ))}
</div>
```

#### `BriefingPanel.tsx` — Card-Based Sections
Each section (Background, Timeline, Economic, Military, Perspectives) should be a separate card matching the mindmap `.card` style:
```tsx
<div className="bg-gt-surface border border-gt-border rounded-lg p-5 mb-4
     hover:border-[#00ff8855] transition-all">
  <h3 className="text-gt-accent text-lg mb-4 pb-2 border-b border-[#1a2a1f]
       flex items-center gap-2.5 tracking-[1px] uppercase">
    <span className="text-base">◉</span> BACKGROUND
  </h3>
  <div className="text-gt-muted text-sm leading-relaxed">
    {report.background}
  </div>
</div>
```

#### `TimelineView.tsx` — Vertical Timeline
Match the mindmap `.timeline` style with the gradient left border and dot markers:
```css
/* Timeline container */
.timeline {
  position: relative;
  padding-left: 30px;
}
.timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, #00ff88, #ff6b35, #3388ff);
}
/* Timeline items */
.timeline-item {
  position: relative;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: #0d0d14;
  border: 1px solid #1a1a2e;
  border-radius: 6px;
}
.timeline-item::before {
  content: '';
  position: absolute;
  left: -26px;
  top: 20px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #00ff88;
  border: 2px solid #0a0a0f;
}
```

#### `SourceStatus.tsx` — Tag-Based Source Badges
Replace the current plain text with colored tag badges matching the mindmap `.tag` classes:
- Used sources: green tag (`#00ff8820` bg, `#00ff88` text)
- Skipped sources: gray tag
- Error sources: red/pink tag (`#ff558820` bg)
- Each tag shows record count

#### Confidence/Warning Box
When showing fallback mode or confidence notes, use the mindmap `.note-box` style:
```css
background: #1a1a0a;
border: 1px solid #333300;
border-left: 3px solid #ffaa00;
padding: 16px 20px;
color: #ccaa44;
```

### Key Principle
**Everything is monospace. Everything is dark. Green (`#00ff88`) is the hero color. Orange (`#ff6b35`) is the secondary accent. Cards have subtle hover animations. Military briefing aesthetic — information density over decoration.**

---

## TASK 3: AI-Powered Query Intelligence

### Problem
When a user types "US-Iran Tensions background" or "What's happening in Gaza", the engine needs to:
1. **Understand the intent** — is this about a specific country, a bilateral relationship, a region, or a topic?
2. **Extract entities** — countries, organizations (NATO, EU), conflicts, time periods
3. **Route to the right data** — fetch from appropriate sources based on query type

### What Opus Already Built (in `main.py`)
- `QUERY_COUNTRY_MAP` — 30+ country name → ISO mappings
- `_extract_countries()` — parses complex queries for country references
- `_to_iso()` — smart primary country resolution (prioritizes non-US for bilateral queries)
- `_build_context_response()` — merges data from multiple countries for bilateral queries

### What Codex Needs to Add

#### 3A. AI Query Parser Endpoint (NEW)
Create `groundtruth/api/query_parser.py`:

```python
"""AI-powered query understanding using local Ollama/Gemma."""

import json
import os
import httpx
from typing import Any

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
- "US-Iran Tensions" → {{"query_type": "bilateral", "countries": ["US", "IR"], "topic": "US-Iran geopolitical tensions", "time_period": {{"start_year": 1953, "end_year": 2026}}}}
- "Ukraine war" → {{"query_type": "country", "countries": ["UA", "RU"], "topic": "Russia-Ukraine conflict", "time_period": {{"start_year": 2014, "end_year": 2026}}}}
- "South China Sea tensions" → {{"query_type": "regional", "countries": ["CN", "PH", "VN", "TW"], "region": "asia", "topic": "South China Sea territorial disputes"}}
- "NATO expansion history" → {{"query_type": "topical", "countries": ["US", "DE", "FR", "GB"], "topic": "NATO expansion since 1949", "key_entities": ["NATO", "Warsaw Pact"]}}

Query: {query}
"""

async def parse_query(query: str) -> dict[str, Any]:
    """Use local LLM to parse a geopolitical query into structured data."""
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
            raw = response.json().get("response", "")

            # Parse JSON from response
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end > start:
                return json.loads(raw[start:end+1])
    except Exception:
        pass

    # Fallback: use the existing regex-based parser
    return {
        "query_type": "country",
        "countries": [],
        "topic": query,
        "time_period": {"start_year": 2000, "end_year": 2026},
    }
```

#### 3B. Wire Query Parser into Context Endpoint
In `main.py`, update `_build_context_response()` to optionally use the AI parser:

```python
from groundtruth.api.query_parser import parse_query

# At the top of _build_context_response():
parsed = await parse_query(query)
# Use parsed.countries if _extract_countries returns nothing
# Use parsed.time_period for start_year/end_year if not explicitly set
# Use parsed.suggested_depth if depth not specified
```

The AI parser is a **fast pre-pass** (512 tokens, 0.1 temp) that runs BEFORE the main synthesis. It helps route the query to the right data. The main synthesis still does the heavy lifting.

#### 3C. New API Endpoint for Query Understanding
```python
@app.get("/v1/parse/{query}")
async def parse_query_endpoint(query: str):
    """Parse a query into structured geopolitical entities. Useful for frontends."""
    parsed = await parse_query(query)
    return parsed
```

This lets the frontend show query understanding in real-time (e.g., "Detected: bilateral query, US + Iran, 1953-present").

---

## TASK 4: Frontend Query Intelligence Integration

### SearchBar Enhancement
When the user types a query, show a small "understanding" preview below the search bar:
```
🔍 US-Iran Tensions background
   Detected: bilateral | US 🇺🇸 + Iran 🇮🇷 | 1953-present | comprehensive depth recommended
```

Call `/v1/parse/{query}` with a debounce (300ms after typing stops) to get the structured preview. This is optional/nice-to-have — the backend fixes are the priority.

---

## File Summary

| File | Action | Priority |
|------|--------|----------|
| `groundtruth/synthesis/engine.py` | Fix Ollama timeout + empty response + error logging | P0 |
| `groundtruth/frontend/tailwind.config.js` | Update colors to match mindmap | P1 |
| `groundtruth/frontend/src/styles/globals.css` | Monospace font, new bg color | P1 |
| `groundtruth/frontend/src/App.tsx` | Header reskin, tab reskin | P1 |
| `groundtruth/frontend/src/components/BriefingPanel.tsx` | Card-based sections | P1 |
| `groundtruth/frontend/src/components/TimelineView.tsx` | Vertical timeline with gradient | P1 |
| `groundtruth/frontend/src/components/SourceStatus.tsx` | Tag-based colored badges | P1 |
| `groundtruth/frontend/src/components/SearchBar.tsx` | Query preview (optional) | P2 |
| `groundtruth/api/query_parser.py` | NEW — AI query parser | P2 |
| `groundtruth/api/main.py` | Wire query parser into context endpoint | P2 |

---

## What Opus Already Changed (this session)

### `groundtruth/api/main.py`
- Added `QUERY_COUNTRY_MAP` (30+ country→ISO mappings)
- Added `_extract_countries()` for multi-country query parsing
- Rewrote `_to_iso()` to use `_extract_countries()` with smart prioritization
- Updated `_build_context_response()` to fetch+merge data from ALL extracted countries (bilateral support)
- Merges SIPRI/FAS data across multiple countries

### `groundtruth/synthesis/engine.py`
- Completely rewrote `PROMPT_TEMPLATE` — now demands deep historical roots (1953 for Iran, not 1979)
- Added depth-scaled token limits: brief=4K, standard=8K, comprehensive=16K
- Added `_max_tokens_for_depth()` method
- Stored `self._current_depth` for token scaling

### These changes are committed but NOT YET TESTED because Ollama is failing.
Fix the Ollama connection first (Task 1), then the reskin, then query intelligence.

---

## Definition of Done
- [ ] `curl 'http://localhost:8000/v1/context/iran?depth=standard'` returns AI-synthesized content (NOT fallback)
- [ ] Timeline goes back to 1953 (Operation Ajax), not just 1979
- [ ] UI matches `docs/Ground_Truth_Mindmap.html` aesthetic (monospace, `#00ff88`, dark cards)
- [ ] Source status shows colored tag badges
- [ ] Timeline renders as vertical timeline with gradient left border
- [ ] All 60 existing tests still pass
- [ ] Linters clean (ruff, black, isort)

---

## Backbrief
Write completion report to `docs/handoffs/SPRINT_4_BACKBRIEF_2026-03-13.md` with:
- Tasks completed (checklist)
- Any issues encountered
- Test results
- Screenshots or curl output showing working synthesis + new UI
