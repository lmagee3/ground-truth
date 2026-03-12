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

## Build Sequence (Agent Assignments)
1. **Sonnet** — Wire World Bank + CIA Factbook ingestion (zero cost, proves pipeline)
2. **Codex** — PostgreSQL models + Alembic migrations
3. **Sonnet** — Add GDELT + ACLED ingestion
4. **Sonnet** — Synthesis layer (Ollama local dev, Claude API production hook)
5. **Antigravity** — Verification pipeline (parallel once reports flow)
6. **Sonnet** — Auth middleware + rate limiting
7. **Sonnet** — Minimal React frontend (last)

# currentDate
Today's date is 2026-03-12.

## Rules
1. Primary sources only — no exceptions
2. Every claim must cite its source
3. Context reports present multiple perspectives — engine doesn't pick sides
4. Antigravity QA pipeline must pass before any report goes public
5. Ship > perfect. Get the MVP working, then refine.
