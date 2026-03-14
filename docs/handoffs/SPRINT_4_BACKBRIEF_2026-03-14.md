# SPRINT 4 BACKBRIEF — Ollama Reliability + UI Reskin + Query Intelligence

**Date:** 2026-03-14  
**From:** Codex  
**To:** Opus via Lawrence  
**Sprint:** 4

---

## Scope Delivered (per Sprint 4 handoff)

### Task 1 — Fix Ollama Connection / Error Handling
**File:** `groundtruth/synthesis/engine.py`

Implemented:
- Increased default `OLLAMA_TIMEOUT` from `120.0` to `300.0`
- Switched timeout config to split connect/read:
  - `httpx.Timeout(10.0, read=self.ollama_timeout)`
- Added empty-response hard fail:
  - raises if Ollama returns blank `response`
- Improved LLM error capture format:
  - `ollama_error: <ExceptionType>: <message>`
  - `anthropic_error: <ExceptionType>: <message>`
- Added model failover chain for Ollama:
  - primary `OLLAMA_MODEL`
  - fallback list from `OLLAMA_FALLBACK_MODELS`
  - default fallback sequence: `gemma3:12b,gemma2:9b,gemma:latest`

Result:
- Engine now surfaces actionable LLM failures instead of silent/empty errors.
- If primary model fails or returns empty output, fallback models are attempted automatically.

### Task 2 — UI Reskin to Mindmap Aesthetic
**Files:**
- `groundtruth/frontend/tailwind.config.js`
- `groundtruth/frontend/src/styles/globals.css`
- `groundtruth/frontend/src/App.tsx`
- `groundtruth/frontend/src/components/BriefingPanel.tsx`
- `groundtruth/frontend/src/components/TimelineView.tsx`
- `groundtruth/frontend/src/components/SourceStatus.tsx`

Implemented:
- Palette and tokens aligned to Sprint 4 handoff:
  - `#0a0a0f` background, `#0d0d14` cards, `#00ff88` primary accent, `#ff6b35` warning accent
- Monospace-first typography (`SF Mono / Fira Code / Consolas`)
- Card-based briefing sections with subtle hover transitions
- Vertical timeline with gradient spine + marker dots
- Source contribution tags (used/skipped/error styles)
- Warning/confidence note box style (`note-box` treatment)
- Header/tab treatment updated to match military briefing aesthetic

### Task 3 — AI Query Intelligence
**Files:**
- `groundtruth/api/query_parser.py` (new)
- `groundtruth/api/main.py`
- `groundtruth/frontend/src/api/client.ts`
- `groundtruth/frontend/src/types/api.ts`
- `groundtruth/frontend/src/components/SearchBar.tsx`

Implemented:
- New backend parser endpoint:
  - `GET /v1/parse/{query}`
- Added `parse_query()` pre-pass using local Ollama with JSON extraction + deterministic fallback parser
- Wired parser into context routing:
  - uses parsed countries when regex extractor misses
  - uses parsed time-period defaults when request uses default year range
  - supports parser-suggested depth when depth not explicitly provided
- Search bar enhancement:
  - debounced query-understanding preview (`Detected: <type> | <countries> | <time span> | <depth>`)

---

## Additional Stability Fixes

- Widget TypeScript lint fix:
  - removed unused variable in `groundtruth/frontend/widget/gt-widget.ts`

---

## Verification Results

### Backend (Sprint 4 scoped)
- Python lint/tests (Sprint 4-scoped files):
  - `ruff check` ✅
  - `black --check` ✅
  - `isort --check` ✅
  - `pytest tests/synthesis/test_engine.py tests/test_api.py` ✅ (`12 passed`)

### Frontend
- `npm run lint` ✅
- `npm run build` ✅
  - build output generated successfully

---

## Known Gaps / Notes

1. **Live Ollama runtime verification is environment-dependent**
   During execution, `localhost:11434` was not reachable in this environment, so live generation validation requires an active local Ollama process.

2. **Repository contains in-progress Sprint 5 files**
   Sprint 5 handoff/backbrief drafts and auth/verification additions exist in working tree. Sprint 4 deliverables are kept scoped by file-level changes above.

---

## Env Guidance for Production-Like Local Testing

Recommended synthesis env:

```bash
SYNTHESIS_PROVIDER=ollama
OLLAMA_MODEL=llama3.1
OLLAMA_TIMEOUT=300.0
OLLAMA_FALLBACK_MODELS=gemma3:12b,gemma2:9b,gemma:latest
```

---

## Sprint 5 Handoff Readiness

Sprint 4 tasks are implemented and validated at code/test/build level. Repo is ready to branch or continue directly into Sprint 5 task execution.
