# Sprint 5 Handoff — Ground Truth
**Date:** 2026-03-14
**From:** Opus (COO / Product Owner)
**To:** Codex (Infrastructure / Feature Dev)
**Status:** Executed (Completed 2026-03-14)
**Note:** Originally scoped for Sonnet, reassigned to Codex. Antigravity hit monthly limits — Codex absorbs both feature build AND the minor QA refinements from Antigravity's Sprint 4 recommendations.

---

## Execution Update (2026-03-14)
- Completed in commit `1933144` on `main`.
- SSE streaming endpoint shipped: `GET /v1/context/{query}/stream`.
- Two-pass local synthesis shipped for `standard` and `comprehensive` depth.
- Frontend progress bar + streaming client integration shipped.
- QA refinements shipped:
  - ISO abbreviation false-positive mitigation in fact checker.
  - Expanded bias detector loaded-language term coverage.
- Validation completed:
  - `ruff check .` passed
  - `isort --check .` passed
  - `pytest -p no:cacheprovider` passed (`71 passed`, `28 skipped`)
  - `npm run lint` + `npm run build` passed
- Backbrief: `docs/handoffs/SPRINT_5_BACKBRIEF_2026-03-14.md`

---

## Sprint Objective
Ship production-ready UX polish: streaming progress indicator, two-pass Standard depth generation, and depth tier gating for monetization. This sprint takes GT from "works in dev" to "demo-ready for production."

---

## Task 1: SSE Streaming Progress Indicator

### Problem
The current UX shows a spinner with "ANALYZING" text during query execution. Synthesis takes 30-90+ seconds depending on depth and model. Users think the app is stuck or hanging because there's zero feedback on what's actually happening.

### Solution
Replace the single `GET /v1/context/{query}` call with a Server-Sent Events (SSE) streaming endpoint that pushes stage-by-stage progress updates to the frontend.

### Backend: New SSE Endpoint

**File:** `groundtruth/api/main.py`

Add a new endpoint `GET /v1/context/{query}/stream` that uses `fastapi.responses.StreamingResponse` with `media_type="text/event-stream"`.

```python
from fastapi.responses import StreamingResponse
import asyncio
import json

@app.get("/v1/context/{query}/stream")
async def get_context_stream(
    query: str,
    depth: str = Query("standard", enum=["brief", "standard", "comprehensive"]),
    provider: str | None = Query(None, enum=["ollama", "anthropic"]),
):
    async def event_generator():
        # Stage 1: Parsing query
        yield _sse_event("progress", {"stage": "parsing", "message": "Parsing query...", "percent": 5})

        parsed_query = await parse_query(query)
        all_countries = _extract_countries(query)
        if not all_countries:
            all_countries = parsed_query.get("countries", [])
        iso = _to_iso(query)

        yield _sse_event("progress", {"stage": "parsing_done", "message": f"Identified: {', '.join(all_countries) or query}", "percent": 10})

        # Stage 2: Fetching country profiles
        yield _sse_event("progress", {"stage": "factbook", "message": "Fetching CIA Factbook profiles...", "percent": 15})
        # ... fetch factbook data ...
        yield _sse_event("progress", {"stage": "factbook_done", "message": "Factbook data loaded", "percent": 25})

        # Stage 3: World Bank indicators
        yield _sse_event("progress", {"stage": "worldbank", "message": "Fetching World Bank indicators...", "percent": 30})
        # ... fetch worldbank ...
        yield _sse_event("progress", {"stage": "worldbank_done", "message": f"Loaded {wb_count} economic indicators", "percent": 40})

        # Stage 4: GDELT events
        yield _sse_event("progress", {"stage": "gdelt", "message": "Scanning GDELT event database...", "percent": 45})
        # ... fetch GDELT ...
        yield _sse_event("progress", {"stage": "gdelt_done", "message": f"Found {len(gdelt_events)} recent events", "percent": 55})

        # Stage 5: ACLED conflict data
        yield _sse_event("progress", {"stage": "acled", "message": "Querying ACLED conflict data...", "percent": 60})
        # ... fetch ACLED ...
        yield _sse_event("progress", {"stage": "acled_done", "message": f"Loaded {len(acled_events)} conflict records", "percent": 65})

        # Stage 6: Military data
        yield _sse_event("progress", {"stage": "military", "message": "Loading SIPRI/FAS military data...", "percent": 70})
        # ... fetch SIPRI + FAS ...
        yield _sse_event("progress", {"stage": "military_done", "message": "Military data compiled", "percent": 75})

        # Stage 7: AI Synthesis (the long part)
        yield _sse_event("progress", {"stage": "synthesis", "message": "AI synthesis in progress...", "percent": 80})
        # ... call engine.generate_context() ...
        yield _sse_event("progress", {"stage": "synthesis_done", "message": "Briefing generated", "percent": 95})

        # Stage 8: Complete — send final result
        yield _sse_event("progress", {"stage": "complete", "message": "Briefing ready", "percent": 100})
        yield _sse_event("result", result_payload)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _sse_event(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
```

### Key Implementation Notes
- The existing `_build_context_response()` function does all the data fetching inline. **Refactor it** into discrete async steps so each step can yield a progress event.
- Don't duplicate business logic — extract the data-fetching steps from `_build_context_response()` into helper functions that both the regular endpoint and the SSE endpoint can call.
- Keep the original `GET /v1/context/{query}` endpoint working unchanged (backward compatibility).
- CORS is already `allow_origins=["*"]` so SSE will work cross-origin.
- **IMPORTANT**: `main.py` has been updated since Sprint 4. Key changes to account for:
  - `AuthMiddleware` is now wired in (`from groundtruth.api.auth import AuthMiddleware`)
  - `VerificationPipeline` runs after synthesis in `_build_context_response()` (lines ~579-584) — add this as its own SSE progress stage ("Verifying sources...", percent: 90)
  - Lifespan migrated from `@app.on_event("startup")` to `@asynccontextmanager async def lifespan()`
  - `/v1/country/{iso_code}` now returns `sources_available` in its payload
  - Response envelope now includes `verification_status` field

### Frontend: Progress Bar Component

**New file:** `groundtruth/frontend/src/components/ProgressBar.tsx`

```tsx
interface ProgressBarProps {
  stage: string;
  message: string;
  percent: number;
}

export function ProgressBar({ stage, message, percent }: ProgressBarProps) {
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gt-muted mb-1">
        <span className="uppercase tracking-[1px]">{message}</span>
        <span className="text-gt-accent">{percent}%</span>
      </div>
      <div className="w-full h-2 bg-gt-surface2 rounded overflow-hidden">
        <div
          className="h-full bg-gt-accent transition-all duration-500 ease-out rounded"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="mt-1 text-[10px] text-gt-muted uppercase tracking-[1px]">
        {stage.replace(/_/g, ' ')}
      </div>
    </div>
  );
}
```

**Update:** `groundtruth/frontend/src/api/client.ts`

Add an SSE-based fetch function:

```typescript
export interface ProgressEvent {
  stage: string;
  message: string;
  percent: number;
}

export async function fetchContextStream(
  query: string,
  depth: Depth = 'standard',
  provider?: string,
  onProgress?: (event: ProgressEvent) => void,
): Promise<ContextResponse> {
  const url = new URL(`${API_BASE}/v1/context/${encodeURIComponent(query)}/stream`);
  url.searchParams.set('depth', depth);
  if (provider) url.searchParams.set('provider', provider);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`GT API error ${res.status}`);

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let result: ContextResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events from buffer
    const events = buffer.split('\n\n');
    buffer = events.pop() || '';

    for (const raw of events) {
      const eventMatch = raw.match(/^event: (\w+)\ndata: (.+)$/ms);
      if (!eventMatch) continue;
      const [, type, data] = eventMatch;
      const parsed = JSON.parse(data);

      if (type === 'progress' && onProgress) {
        onProgress(parsed);
      } else if (type === 'result') {
        result = parsed;
      }
    }
  }

  if (!result) throw new Error('Stream ended without result');
  return result;
}
```

**Update:** `groundtruth/frontend/src/hooks/useContext.ts`

Add progress state and use `fetchContextStream` instead of `fetchContext`:

```typescript
const [progress, setProgress] = useState<ProgressEvent | null>(null);

// In the query function:
setProgress(null);
const result = await fetchContextStream(q, depth, provider, (event) => {
  setProgress(event);
});
setProgress(null); // Clear after completion
```

Return `progress` from the hook so `App.tsx` can render `<ProgressBar>` during loading.

**Update:** `groundtruth/frontend/src/App.tsx`

Replace the current `{loading && <BriefingPanel loading={true} ... />}` with:
- If `loading && progress`: show `<ProgressBar stage={progress.stage} message={progress.message} percent={progress.percent} />`
- If `loading && !progress`: show the existing spinner (fallback for non-SSE)
- If `data && !loading`: show `<BriefingPanel>`

---

## Task 2: Two-Pass Standard Depth Generation

### Problem
Only Brief depth (4K tokens) produces good output from local Ollama models (qwen3:14b). Standard (8K tokens) and Comprehensive (16K tokens) produce garbage — the model loses coherence when asked for too much structured JSON in one shot.

### Solution
Two-pass generation for Standard depth — split the work into two 4K-token passes, then merge the results. Brief stays single-pass. Comprehensive stays single-pass BUT is gated behind the Pro tier (uses cloud API).

### Implementation

**File:** `groundtruth/synthesis/engine.py`

Add a `_two_pass_generate()` method:

```python
async def _two_pass_generate(
    self,
    query: str,
    depth: str,
    country_data: dict,
    events: dict,
    military_data: dict,
    sources_available: dict,
) -> dict[str, Any]:
    """Two-pass generation: historical context first, then analysis layer."""

    # PASS 1: Historical narrative + timeline (the 'what happened' pass)
    pass1_prompt = PASS1_TEMPLATE.format(
        query=query,
        factbook_data=self._summarize_factbook(country_data.get("factbook", {})),
        worldbank_data=self._summarize_worldbank(country_data.get("worldbank", {})),
        gdelt_events=self._summarize_events(events.get("gdelt", []), "GDELT", max_items=10),
        acled_events=self._summarize_events(events.get("acled", []), "ACLED", max_items=10),
        military_data=self._summarize_military(military_data),
    )

    self._current_depth = "brief"  # Force 4K tokens for pass 1
    pass1_raw = await self._call_ollama(pass1_prompt)
    pass1_result = self._parse_llm_json(pass1_raw) or {}

    # PASS 2: Analysis layer — perspectives, assessment, confidence (the 'so what' pass)
    pass2_prompt = PASS2_TEMPLATE.format(
        query=query,
        title=pass1_result.get("title", query),
        summary=pass1_result.get("summary", ""),
        background=pass1_result.get("background", ""),
        timeline_count=len(pass1_result.get("timeline", [])),
        economic_context=pass1_result.get("economic_context", ""),
        military_context=pass1_result.get("military_context", ""),
    )

    self._current_depth = "brief"  # Force 4K tokens for pass 2
    pass2_raw = await self._call_ollama(pass2_prompt)
    pass2_result = self._parse_llm_json(pass2_raw) or {}

    # MERGE: Pass 1 narrative + Pass 2 analysis
    merged = {
        "title": pass1_result.get("title", f"Ground Truth: {query}"),
        "summary": pass1_result.get("summary", ""),
        "background": pass1_result.get("background", ""),
        "timeline": pass1_result.get("timeline", []),
        "economic_context": pass1_result.get("economic_context", ""),
        "military_context": pass1_result.get("military_context", ""),
        "perspectives": pass2_result.get("perspectives", []),
        "current_assessment": pass2_result.get("current_assessment", ""),
        "sources_cited": list(set(
            pass1_result.get("sources_cited", []) + pass2_result.get("sources_cited", [])
        )),
        "confidence_notes": pass2_result.get("confidence_notes", ""),
        "sources_available": sources_available,
    }

    return merged
```

### Pass 1 Prompt Template (new constant)

```python
PASS1_TEMPLATE = """You are Ground Truth, a senior intelligence analyst.

TASK: Write the HISTORICAL NARRATIVE for a briefing on: "{query}"

Focus on: title, executive summary, deep historical background (trace to ROOT CAUSE),
timeline (10-18 events spanning full arc), economic context, military context.

Do NOT write perspectives or current assessment — those come in pass 2.

[Same data sections as main prompt]

Return ONLY valid JSON:
{{
  "title": "...",
  "summary": "2-4 sentence executive summary",
  "background": "Multi-paragraph historical narrative from root cause to present",
  "timeline": [{{"year": YYYY, "event": "...", "source": "..."}}],
  "economic_context": "...",
  "military_context": "...",
  "sources_cited": [...]
}}
"""
```

### Pass 2 Prompt Template (new constant)

```python
PASS2_TEMPLATE = """You are Ground Truth, a senior intelligence analyst.

TASK: Write the ANALYSIS LAYER for a briefing on: "{query}"

You already have the historical narrative (title: "{title}", {timeline_count} timeline events).
Now provide interpretive frameworks, current assessment, and confidence analysis.

Context from Pass 1:
- Summary: {summary}
- Economic: {economic_context}
- Military: {military_context}

Return ONLY valid JSON:
{{
  "perspectives": [{{"framework": "...", "argument": "...", "evidence": "..."}}],
  "current_assessment": "Forward-looking analysis of current situation",
  "sources_cited": [...],
  "confidence_notes": "Data gaps and reliability caveats"
}}
"""
```

### Routing Logic

In `generate_context()`, add routing before the LLM call:

```python
if depth == "standard" and selected_provider != "anthropic":
    return await self._two_pass_generate(
        query, depth, country_data, events, military_data, sources_available
    )
```

Brief stays single-pass (already works). Comprehensive with `provider=anthropic` stays single-pass (cloud model handles it). Comprehensive with `provider=ollama` should also use two-pass (or three-pass if needed — start with two).

---

## Task 3: Depth Tier Gating (Monetization Prep)

### Problem
Open source users get all three depth tiers for free, but Standard/Comprehensive produce poor results with local models. Need a clean strategy that doesn't break the MIT license promise.

### Tier Strategy
| Tier | Depth | Model | Cost to Run | Target |
|------|-------|-------|-------------|--------|
| Free (open source) | Brief | Local Ollama | $0 | Community / GitHub stars |
| Free (open source) | Standard | Local Ollama (two-pass) | $0 | Community / power users |
| Pro ($49/mo) | Comprehensive | Claude API | ~$0.02-0.10/query | Analysts / researchers |
| Enterprise ($199-499/mo) | All + batch + webhooks | Claude API | Variable | Institutions |
| Federal ($500-2K/mo) | All + on-prem | Customer's choice | Variable | Defense / gov |

### Implementation

**NO tier gating in the open source code.** The MIT repo stays fully functional with all depths available via local Ollama. The two-pass fix makes Standard actually usable with local models.

**For the hosted API (separate deployment):**
- Add `X-GT-Tier` header or API key validation middleware
- Comprehensive depth without a Pro API key returns a 402 response:
  ```json
  {"error": "comprehensive_depth_requires_pro", "message": "Comprehensive briefings use Claude AI for deep analysis. Upgrade to Pro ($49/mo) at groundtruth.dev/pricing", "fallback_depth": "standard"}
  ```
- This middleware lives in a SEPARATE file (`groundtruth/api/middleware/tier_gate.py`) that is NOT included in the open source repo. It's deployed only on the hosted version.

### Frontend Hint (open source)

In the SearchBar depth selector, add a subtle indicator for Comprehensive:

```tsx
// In DEPTHS array:
{ value: 'comprehensive', label: 'Comprehensive', desc: '~90s · Cloud AI' },
```

And when Comprehensive is selected while running against local Ollama:
```tsx
{depth === 'comprehensive' && (
  <div className="text-[10px] text-gt-warn">
    ⚡ Best results with Claude API. Set SYNTHESIS_PROVIDER=anthropic in .env
  </div>
)}
```

---

## Task 4: Frontend Polish

### 4a. Source count in progress bar
When data sources finish loading, show counts in the progress messages:
- "Loaded 978 economic indicators across 2 countries"
- "Found 47 GDELT events in the last 30 days"
- "SIPRI: 42 military expenditure records, 12 arms transfers"

### 4b. Error state improvement
Current error display is a raw string in a red box. Improve:
- If Ollama is unreachable: "Local AI (Ollama) is not running. Start it with: `ollama serve`"
- If model not found: "Model 'qwen3:14b' not found. Pull it with: `ollama pull qwen3:14b`"
- If synthesis times out: "Synthesis timed out after 5 minutes. Try Brief depth for faster results."

### 4c. Briefing panel loading skeleton
Replace the empty/loading state with skeleton placeholders that match the briefing layout — gray blocks where title, summary, background will appear. This signals "content is coming" better than a spinner.

---

## Task 5: QA Refinements (from Antigravity Sprint 4 Backbrief)

Antigravity flagged these in their Sprint 4 backbrief. Low-effort, high-value fixes.

### 5a. Fact Checker ISO False-Positives
**File:** `groundtruth/verification/fact_checker.py`

Common abbreviations like "UN", "EU", "UK" are 2-letter tokens that could trip the ISO 3166-1 validation. Add an allowlist of non-country 2-letter abbreviations:

```python
# Add near top of file
NON_COUNTRY_ABBREVIATIONS = {"UN", "EU", "AI", "UK", "US", "FM", "AM", "PM", "TV", "IT", "HR", "PR"}
# UK and US ARE country codes but commonly appear as abbreviations — allow them in non-ISO contexts
```

In the ISO validation check, skip tokens that are in `NON_COUNTRY_ABBREVIATIONS` when they appear in prose context (not in the `countries` field of the report).

### 5b. Bias Detector Word List Expansion
**File:** `groundtruth/verification/bias_detector.py`

Add geopolitical-domain loaded terms that the current list likely misses:

```python
# Suggested additions to high-tier (fail) list:
"terrorist state", "axis of evil", "rogue nation", "puppet regime"

# Suggested additions to medium-tier (warn) list:
"regime", "strongman", "so-called", "illegitimate", "expansionist"
```

These are common in news coverage but inappropriate for an intelligence-grade briefing engine that claims neutrality.

### 5c. Skip Redis for now
Antigravity recommended migrating rate limiter to Redis. **DO NOT build this yet.** In-memory rate limiting works fine for single-instance Railway deployment. Redis adds a dependency and cost. Defer to Sprint 7+ when we need multi-instance scaling.

---

## Files to Modify

| File | Changes |
|------|---------|
| `groundtruth/api/main.py` | Add `/v1/context/{query}/stream` SSE endpoint, refactor `_build_context_response()` into discrete steps. NOTE: AuthMiddleware + VerificationPipeline already wired — SSE endpoint must respect both. |
| `groundtruth/synthesis/engine.py` | Add `_two_pass_generate()`, `PASS1_TEMPLATE`, `PASS2_TEMPLATE`, routing logic in `generate_context()` |
| `groundtruth/frontend/src/components/ProgressBar.tsx` | NEW — progress bar component |
| `groundtruth/frontend/src/api/client.ts` | Add `fetchContextStream()` function |
| `groundtruth/frontend/src/hooks/useContext.ts` | Add progress state, use SSE stream |
| `groundtruth/frontend/src/App.tsx` | Integrate ProgressBar, add Comprehensive depth hint |
| `groundtruth/frontend/src/components/SearchBar.tsx` | Add cloud AI hint for Comprehensive depth |
| `groundtruth/frontend/src/components/BriefingPanel.tsx` | Add skeleton loading state |
| `groundtruth/verification/fact_checker.py` | Add NON_COUNTRY_ABBREVIATIONS allowlist for ISO false-positive fix |
| `groundtruth/verification/bias_detector.py` | Expand loaded language word lists with geopolitical terms |

---

## Testing

1. **SSE endpoint**: `curl -N "http://localhost:8000/v1/context/US-Iran%20tensions/stream?depth=brief"` — should see progressive `event: progress` lines followed by `event: result`
2. **Two-pass Standard**: Run "US-Iran tensions" at Standard depth — should produce coherent output comparable to Brief but with more detail
3. **Brief regression**: Ensure Brief depth still works single-pass with same quality
4. **Fallback**: If SSE endpoint fails, frontend should gracefully fall back to the regular endpoint
5. **Comprehensive hint**: Select Comprehensive → see cloud AI notice in SearchBar
6. **ISO false-positive**: Run fact checker on a report containing "UN peacekeepers" — should NOT flag "UN" as invalid ISO code
7. **Bias detector**: Run bias detector on text containing "terrorist state" — should flag as high-tier loaded language
8. **Full test suite**: `pytest` — all 96+ tests pass, 0 failures

---

## Priority Order
1. Two-pass Standard (Task 2) — highest impact, fixes broken depth tier
2. SSE Progress (Task 1) — best UX improvement
3. QA Refinements (Task 5) — quick wins, fixes Antigravity's flagged issues
4. Frontend Polish (Task 4) — quick wins
5. Tier Gating prep (Task 3) — lowest priority, just the frontend hint for now

---

## Definition of Done
- [ ] Standard depth produces coherent, historically-grounded briefings via two-pass local generation
- [ ] Progress bar shows real-time stage updates during query execution
- [ ] Comprehensive depth shows "Cloud AI" hint in the UI
- [ ] Error messages are human-readable with actionable fix instructions
- [ ] Brief depth regression: still works exactly as before
- [ ] Fact checker no longer false-flags "UN", "EU" etc. in prose
- [ ] Bias detector catches "terrorist state", "axis of evil", "puppet regime"
- [ ] All existing 96 tests still pass + new tests for QA refinements
