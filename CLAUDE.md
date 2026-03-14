# CLAUDE.md — Ground Truth Project Context

## Project
**Ground Truth** — Open-Source Geopolitical Context Engine
**Tagline:** "The intelligence briefing behind the radar blip"
**Repo:** https://github.com/lmagee3/ground-truth
**License:** MIT
**Brand:** Chaos Monk (by MAGE Software / Malleus Prendere LLC)

## What This Is
An API-first engine that generates historical context and intelligence briefings for geopolitical events using ONLY primary authoritative sources. No Wikipedia, no media spin, no editorial narrative. Government archives, institutional databases, declassified intelligence, and verified primary data — synthesized by AI into structured, multi-perspective context reports.

## Owner
Lawrence Magee — CEO, Malleus Prendere LLC. 20-year US Army IT veteran.

## Agent Roster
| Agent | Role | Scope |
|-------|------|-------|
| **Opus** (Claude Cowork) | COO / Product Owner | Architecture, API design, prompt engineering, quality standards, strategy |
| **Sonnet** (Claude Code) | Feature Dev | FastAPI implementation, data pipelines, React frontend |
| **Codex** | Infrastructure | Database, deployment, CI/CD, monitoring |
| **Antigravity** | QA / Verification | Source validation, bias detection, fact-checking. Owns `groundtruth/verification/` |

## Tech Stack
- **Backend:** Python 3.11+ / FastAPI
- **Database:** PostgreSQL + pgvector (embeddings for semantic search)
- **Cache:** Redis
- **AI (dev):** Ollama local (Llama 3 / Mistral / Gemma) — zero cost
- **AI (production paid tiers):** Claude API — Pro/Enterprise/Federal only
- **Frontend:** React 18 + TypeScript (minimal)
- **Hosting:** Vercel (frontend) + Railway (API)
- **CI/CD:** GitHub Actions

## Cost Architecture
- **All data source API keys held by us** — users never register for ACLED, NARA, etc. They only hit the Ground Truth API.
- **Free tier:** Pre-computed cached context reports for top 50+ global hotspots. Batch-generated overnight via server-hosted Ollama. No per-query AI cost. Users get instant responses from cache.
- **Paid tiers (Pro/Enterprise/Federal):** On-demand context generation via Claude API for novel/custom queries. Token costs covered by subscription revenue.
- **Development:** Ollama local — zero cost during build phase.
- **Self-hosted open source users:** They run their own Ollama instance + register their own API keys. That's the tradeoff for free — you host it yourself.
- **Server cost estimate:** ~$7-20/mo for Railway/Fly.io instance running Ollama + FastAPI + PostgreSQL + Redis. Covered by first paying customer.

## Military & Defense Data Layer
Ground Truth includes structured military and weapons capability context:
- **Force structure / order of battle** — CIA Factbook + IISS (where available)
- **Weapons systems profiles** — Federation of American Scientists (fas.org, free)
- **Nuclear arsenals** — SIPRI Nuclear Notebook + FAS Nuclear Notebook
- **Arms transfers** — SIPRI Arms Transfers Database (who sells what to whom)
- **Military spending** — SIPRI Military Expenditure Database
- **Defense agreements** — NATO Article 5, AUKUS, bilateral treaties (from treaty archives)
- **Sanctions & arms embargoes** — UN Security Council + OFAC (treasury.gov)
This layer is critical for the federal/defense revenue tier and differentiates Ground Truth from civilian-focused competitors.

## Data Source Rules
1. **PRIMARY SOURCES ONLY** — Government archives, institutional databases, declassified intelligence
2. **NO WIKIPEDIA** — Editable by anyone, unreliable for contested geopolitical topics
3. **NO NEWS ARTICLES** — Editorial spin, narrative framing
4. **EVERY CLAIM CITED** — Source URL required for all factual assertions
5. **MULTIPLE PERSPECTIVES** — Context reports present competing interpretive frameworks

## Approved Source Domains
See `docs/APPROVED_SOURCES.md` for the full list. Key sources:
- loc.gov, archives.gov, cia.gov, state.gov, congress.gov (US Gov)
- data.worldbank.org, acleddata.com, ucdp.uu.se, gdeltproject.org (International)
- nationalarchives.gov.uk, archives.nato.int (Allied)
- sipri.org, data.humdata.org, transparency.org (Institutional)

## Directory Structure
```
ground-truth/
├── CLAUDE.md               ← You are here
├── README.md               ← GitHub-facing README
├── pyproject.toml          ← Python package config
├── groundtruth/
│   ├── ingestion/          ← Data source integrations
│   ├── synthesis/          ← AI context generation
│   ├── api/                ← FastAPI REST endpoints
│   ├── verification/       ← QA pipeline (Antigravity owns)
│   └── frontend/           ← React web UI
├── tests/                  ← pytest test suite
├── docs/                   ← Architecture docs, handoffs, source list
├── scripts/                ← Utility scripts
└── .github/workflows/      ← CI/CD
```

## Revenue Model
- **Free:** 100 API calls/day (community + GitHub stars)
- **Pro:** $49/mo — unlimited API, real-time alerts, webhooks
- **Enterprise:** $199-499/mo — SLA, bulk queries, custom templates
- **Federal:** $500-2K/mo — on-prem option, SDVOSB pricing

## Sprint Status
| Sprint | Status | What Shipped | Tests |
|--------|--------|-------------|-------|
| Sprint 1 | ✅ Complete | World Bank + CIA Factbook ingestion, DB models, API scaffolding, Source Validator | 60 passed |
| Sprint 2 | ✅ Complete — QA PASSED | GDELT + ACLED ingestion, SIPRI + FAS military data, AI synthesis engine, full API wiring, DB persistence | 60 passed |
| Sprint 3 | ✅ Complete | React 18 + TS frontend, GeoJSON endpoint, World Monitor interop, SearchBar, BriefingPanel, CompareView, SourceStatus | — |
| Sprint 4 | ✅ Complete | Ollama fallback model chain, UI reskin to mindmap aesthetic, AI query parser (query_parser.py), data summarization pipeline, prompt rewrite | — |
| Sprint 5 | 🚧 In Progress | SSE streaming progress, two-pass Standard depth, depth tier gating, frontend polish | — |

## Key Decisions
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-11 | Project created as "Ground Truth" | Military/ML term for verified reality. Signals credibility. |
| 2026-03-11 | MIT license (not AGPL) | Maximum adoption. World Monitor is AGPL — we complement, not fork. |
| 2026-03-11 | No Wikipedia as source | Editable by anyone, subject to edit wars on geopolitical topics. |
| 2026-03-11 | API-first, not content-first | Tool > publication. Build infrastructure, not a content treadmill. |
| 2026-03-11 | Complementary to World Monitor | WM = radar (what). GT = briefing (why). Partnership > competition. |
| 2026-03-12 | Ollama for free tier, Claude API for paid only | Zero cost to run open source version. Tokens only burned for paying customers. |
| 2026-03-12 | Added military/defense data layer | SIPRI, FAS, OFAC, treaty archives. Differentiator for federal tier. |
| 2026-03-12 | Graceful source degradation is first-class | Any missing credentials or failed source never blocks report generation. |
| 2026-03-12 | AI provider switchable via env var | `SYNTHESIS_PROVIDER=ollama` or `anthropic` — no code change needed. |
| 2026-03-13 | `/v1/country/{iso}` missing `sources_available` | Minor gap — all synthesis endpoints include it; country endpoint is raw data. Fix in Sprint 3. |
| 2026-03-13 | React 18 + TS frontend with WM interop | Embeddable widget + GeoJSON endpoint for World Monitor map layer compatibility. Sonnet builds. |
| 2026-03-13 | No Next.js — pure Vite SPA | Overkill for our needs. Static deploy to Vercel. API stays separate on Railway. |
| 2026-03-13 | Dark theme matching WM aesthetic | Deep navy + emerald green. Military briefing typography. Information density > decoration. |
| 2026-03-14 | qwen3:14b as primary Ollama model | Best balance of quality vs speed from Lawrence's local inventory (9.3GB). Fallback: llama3.1, qwen3:8b, gemma. |
| 2026-03-14 | Data summarization pipeline | Raw JSON (50K+ tokens) compressed to trend summaries (~2-3K tokens) before LLM. Fixed "model describes data instead of geopolitics" bug. |
| 2026-03-14 | Two-pass generation for Standard depth | Local models can't do 8K structured JSON in one shot. Split into historical narrative (4K) + analysis layer (4K), then merge. |
| 2026-03-14 | Comprehensive = Pro tier (cloud API) | Local Ollama can't handle 16K structured output. Comprehensive depth uses Claude API — covered by $49/mo Pro subscription revenue. |
| 2026-03-14 | SSE streaming for progress | Replace spinner with real-time stage-by-stage progress bar. Users see exactly what's happening during 30-90s synthesis. |
| 2026-03-14 | GT is NOT redundant with World Monitor | WM = radar (WHAT is happening). GT = briefing (WHY it's happening). Complementary, not competitive. WM has 2M users with no deep context — GT provides that context. Integration play, not competition. |
| 2026-03-14 | MIT license advantage over WM's AGPL | WM can't embed our engine without going open source. We CAN build embeddable widget they'd want to link to. Leverage. |

## Build Sequence (Agent Assignments)
1. ✅ **Sonnet / Codex** — World Bank + CIA Factbook ingestion, DB models, Source Validator (Sprint 1)
2. ✅ **Codex** — GDELT + ACLED ingestion, SIPRI + FAS military data, AI synthesis engine, full API wiring (Sprint 2)
3. ✅ **Antigravity** — Source Validator built + QA pass on Sprint 2 (Sprint 1–2)
4. ✅ **Sonnet** — React 18 + TS frontend, embeddable widget, GeoJSON endpoint, WM interop (Sprint 3)
5. ✅ **Codex** — Ollama fallback chain, UI reskin, AI query parser (Sprint 4)
6. ✅ **Opus** — Data summarization pipeline, prompt rewrite, multi-country merging (Sprint 4)
7. 🚧 **Sonnet** — SSE streaming progress, two-pass Standard depth, frontend polish (Sprint 5)
8. 🔜 **Antigravity Sprint 3+** — Wire VerificationPipeline into API, build Bias Detector + Fact Checker
9. 🔜 **Sprint 6** — Auth middleware, rate limiting, user accounts, deployment (Vercel + Railway)

## Competitive Positioning
- **World Monitor** = radar screen (WHAT is happening now). Real-time event feed, macro analytics, equity overlays. 2M+ users, AGPL license, Pro tier on waitlist at $0 (no revenue yet). Created by Elie Habib (Anghami CTO).
- **Ground Truth** = analyst's desk (WHY it's happening). Historical context, primary source citations, multi-perspective frameworks. MIT license.
- **Integration play**: WM users click a hotspot → GT provides the deep briefing. WM's 2M users = our distribution channel. No marketing spend needed.
- **Differentiation**: GT's military data layer (SIPRI arms transfers, FAS nuclear notebooks, OFAC sanctions) serves defense/policy audience that WM doesn't touch. That's the federal $500-2K/mo tier.
- **WM's equity/macro features** are financial data overlays for traders. GT's evidence pipeline + historical depth + citation rigor serves a different use case entirely.

# currentDate
Today's date is 2026-03-14.

## Rules
1. Primary sources only — no exceptions
2. Every claim must cite its source
3. Context reports present multiple perspectives — engine doesn't pick sides
4. Antigravity QA pipeline must pass before any report goes public
5. Ship > perfect. Get the MVP working, then refine.
