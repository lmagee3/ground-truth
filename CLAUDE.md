# CLAUDE.md — Ground Truth Project Context

## Project
**Ground Truth** — Open-Source Geopolitical Context Engine → Diplomatic Decision-Support Platform
**Tagline:** "The intelligence briefing behind the radar blip"
**Phase 2 Tagline:** "The Palantir for peace"
**Repo:** https://github.com/lmagee3/ground-truth
**License:** MIT
**Brand:** Malleus Prendere LLC (flagship product). Open-source core distributed under Chaos Monk.
**Strategic Position:** Malleus Prendere's flagship product. Primary revenue vehicle targeting government agencies, UN/multilateral organizations, and institutional buyers via SDVOSB federal contracts and direct sales.

## What This Is
**STRATEGIC PIVOT (2026-05-10):** Phase 2 is now the primary build target. Phase 1 context engine is complete infrastructure — not a standalone product competing with WorldMonitor.

**Core Engine (Sprints 1-6, done/in-progress):** API-first engine that generates historical context and intelligence briefings using ONLY primary authoritative sources. Government archives, declassified intelligence, institutional databases. This is now the *foundation layer* under the recommendation engine, not the product itself.

**Primary Product (Sprint 7+):** A diplomatic decision-support platform — recommendation engine for de-escalation scenarios, aid allocation modeling, diplomatic channel mapping, and intervention feasibility scoring. Targets UN agencies, USAID, State Department, EU External Action Service, think tanks. Uses WorldMonitor MCP/API for real-time event input, GT primary sources for depth, and a new recommendation synthesis layer for actionable diplomatic options.

**Positioning:** "WM tells you what's happening. GT tells you what to DO about it." WorldMonitor = radar. Ground Truth = analyst's recommendation. No competition — complementary layers.

**Federal Go-to-Market:** SDVOSB-eligible. SAM.gov registered. Positioned for IDIQ task orders, BPAs, and GWACs. MAQC 660 (Business Decisions for Contracting) coursework directly informing federal acquisition strategy — source selection, contractor responsibility, subcontracting plans, FAR compliance.

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

## Revenue Model (Revised 2026-05-10)
- **Free (Open Source):** Context API (100 calls/day), primary source citations, basic briefings — community adoption + credibility
- ~~**Pro:** $49/mo~~ — KILLED. Competed with WorldMonitor Pro. Don't fight that fight.
- **Diplomat (PRIMARY TIER):** $500-2K/mo — Recommendation engine, de-escalation scenarios, aid modeling, diplomatic mapping, intervention scoring, PDF export. Target: UN, USAID, State Dept, think tanks
- **Federal:** $500-2K/mo — Same as Diplomat + on-prem option, SDVOSB pricing, IDIQ/BPA eligible
- **Academic:** $99/mo — Full API access for research, university IR departments

## Sprint Status
| Sprint | Status | What Shipped | Tests |
|--------|--------|-------------|-------|
| Sprint 1 | ✅ Complete | World Bank + CIA Factbook ingestion, DB models, API scaffolding, Source Validator | 60 passed |
| Sprint 2 | ✅ Complete — QA PASSED | GDELT + ACLED ingestion, SIPRI + FAS military data, AI synthesis engine, full API wiring, DB persistence | 60 passed |
| Sprint 3 | ✅ Complete | React 18 + TS frontend, GeoJSON endpoint, World Monitor interop, SearchBar, BriefingPanel, CompareView, SourceStatus | — |
| Sprint 4 | ✅ Complete | Ollama fallback model chain, UI reskin to mindmap aesthetic, AI query parser (query_parser.py), data summarization pipeline, prompt rewrite | — |
| Sprint 5 | ✅ Complete | SSE streaming progress, two-pass Standard depth, depth tier gating, frontend polish, QA refinements | 71 passed, 28 skipped |
| Sprint 6 | 🚧 In Progress | Library of Congress + Congress.gov + NARA ingestors (3 new primary sources) | — |
| Sprint 7 | 🔜 PIVOTED | WM MCP integration + Phase 2 data sources (UN Comtrade, WTO, OECD DAC, UNHCR) | — |
| Sprint 8 | 🔜 NEW | Recommendation engine v1 — de-escalation scenarios, intervention scoring | — |
| Sprint 9 | 🔜 NEW | Deploy API (Railway) + Diplomat tier endpoints. API-only, no frontend. | — |

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
| 2026-03-14 | Add LoC + Congress.gov + NARA as data sources | Congressional testimony, treaty texts, declassified intel. 9 sources total. No competitor has this depth. LoC = no key needed, Congress.gov = free key, NARA = email for key. |
| 2026-03-18 | Phase 2: Diplomatic Decision-Support Platform | Flip the Palantir model — same analytical depth pointed at cooperation. GT vertical, not new project. Adds trade flows, aid modeling, diplomatic channel mapping, de-escalation scenarios. Target: UN, USAID, State Dept, think tanks. |
| 2026-05-10 | STRATEGIC PIVOT: Skip Phase 1 deployment, accelerate Phase 2 | WorldMonitor Pro launched with features that commoditize Phase 1 (real-time monitoring, stability scoring, sanctions tracking, 50K GitHub stars). Can't outbuild WM at $2K. Instead: use WM MCP as input layer, keep primary source depth as moat, leapfrog to recommendation engine (Phase 2) that WM doesn't build. "WM tells you what's happening. GT tells you what to DO about it." |
| 2026-05-10 | Kill $49/mo Pro tier | Was competing directly with WM Pro pricing. Go straight to institutional ($500-2K/mo Diplomat tier). Different buyer, different sale. |
| 2026-05-10 | WorldMonitor MCP as input layer | Replace our own GDELT/ACLED real-time crawling with WM's 28-tool MCP server. They do monitoring better. We add depth + recommendations on top. |
| 2026-05-10 | API-first deployment, no frontend | Ship recommendation engine as API endpoints first. Prove value before building globe/dashboard. Frontend deferred to Sprint 10+. |

## Build Sequence (Agent Assignments)
1. ✅ **Sonnet / Codex** — World Bank + CIA Factbook ingestion, DB models, Source Validator (Sprint 1)
2. ✅ **Codex** — GDELT + ACLED ingestion, SIPRI + FAS military data, AI synthesis engine, full API wiring (Sprint 2)
3. ✅ **Antigravity** — Source Validator built + QA pass on Sprint 2 (Sprint 1–2)
4. ✅ **Sonnet** — React 18 + TS frontend, embeddable widget, GeoJSON endpoint, WM interop (Sprint 3)
5. ✅ **Codex** — Ollama fallback chain, UI reskin, AI query parser (Sprint 4)
6. ✅ **Opus** — Data summarization pipeline, prompt rewrite, multi-country merging (Sprint 4)
7. ✅ **Sonnet** — SSE streaming progress, two-pass Standard depth, frontend polish (Sprint 5)
8. ✅ **Antigravity Sprint 4** — VerificationPipeline fully wired (Source Validator + Bias Detector + Fact Checker), Auth middleware, 96 tests passing
9. 🚧 **Codex Sprint 6** — Library of Congress + Congress.gov + NARA ingestors (3 new primary sources, 9 total)
10. 🔜 **Sprint 7 (PIVOTED)** — WorldMonitor MCP integration as input layer + Phase 2 data sources (UN Comtrade, WTO, OECD DAC, UNHCR, FAO, UN Treaty Collection)
11. 🔜 **Sprint 8** — Recommendation engine v1: de-escalation scenario generation, intervention feasibility scoring, scenario comparison
12. 🔜 **Sprint 9** — Deploy API to Railway. Diplomat tier endpoints live. No frontend — API-only.
13. 🔜 **Sprint 10** — Frontend (globe, dashboard, scenario cards) — only after API proves value with first institutional buyer

## Phase 2 — Diplomatic Decision-Support Platform (Post-Sprint 7)

### Vision
Flip the Palantir model. Palantir builds intelligence tools for threat identification and force projection (CIA, DoD, ICE). Ground Truth Phase 2 builds the counterweight: a decision-support platform for **diplomatic outcomes** — peace, trade, aid allocation, conflict de-escalation. Same analytical depth, pointed at cooperation instead of coercion.

### Tagline
*"The Palantir for peace"*

### Why GT Is 70% There Already
The current engine (9 primary sources, AI synthesis, verification pipeline, bias detection) provides the analytical foundation. Phase 2 adds a **recommendation layer** on top of existing context briefings.

### New Data Sources Required
| Source | What It Gives Us | API | Cost |
|--------|-----------------|-----|------|
| **UN Comtrade** | Bilateral trade flows, import/export volumes | comtrade.un.org/data/dev/portal | Free (API key) |
| **WTO** | Trade disputes, tariff data, trade agreements | apiportal.wto.org | Free |
| **OECD DAC** | Aid effectiveness data, donor flows, development outcomes | stats.oecd.org API | Free |
| **UNHCR** | Refugee/displacement data, humanitarian corridors | api.unhcr.org | Free |
| **FAO** | Food price indices, agricultural trade, food security | fao.org/faostat/api | Free |
| **UN General Assembly Voting** | Diplomatic alignment mapping, voting blocs | digitallibrary.un.org | Free |
| **World Bank WGI** | Governance indicators (corruption, rule of law, stability) | Already partially integrated via World Bank API | Free |
| **UN Treaty Collection** | Active treaties, bilateral agreements, treaty status | treaties.un.org | Free (scrape) |

### New Capabilities (Phase 2 Features)
1. **Economic Interdependency Mapping** — Trade flow analysis showing where countries are already economically linked and where trade bridges could be built
2. **Aid Allocation Modeling** — Historical aid effectiveness data + current conditions → recommended aid strategies ranked by likelihood of sustained impact
3. **Diplomatic Channel Mapping** — Treaty networks, voting alignment, embassy presence, bilateral agreements → who talks to whom and where channels exist
4. **Conflict De-escalation Scenarios** — Based on conflict trajectory + economic interdependencies + historical precedents → ranked intervention options
5. **Early Warning Dashboard** — Food prices (FAO) + displacement (UNHCR) + governance decline (WGI) + conflict events (ACLED) as leading indicators
6. **Regional Temperature Index** — Composite score per country/region factoring:
   - **Religious landscape** — dominant faiths, sectarian divisions, religious freedom indices (Pew Research Center religious restrictions data — free)
   - **Political ideology spectrum** — conservative/progressive score derived from governance indicators (WGI), Freedom House ratings (free API), and V-Dem democracy indices (free)
   - **Spoiler actor mapping** — Known rebel groups, opposition movements, separatist factions, radical organizations sourced from ACLED actor data + UCDP (Uppsala Conflict Data Program — free). Each actor tagged with: capability level, territorial control, foreign backers, willingness to negotiate
   - **Diplomatic friction score** — AI-computed likelihood of smooth negotiations based on: historical negotiation outcomes, current leader tenure/stability, presence of spoiler actors, religious/ethnic fault lines, active sanctions, and whether the parties have existing diplomatic channels
   - Displayed as a "temperature gauge" on the country dashboard — green (conducive to diplomacy) through red (high friction, spoiler risk). Clicking the gauge expands to show all contributing factors with source citations

### Additional Data Sources for Regional Temperature
| Source | What It Gives Us | API | Cost |
|--------|-----------------|-----|------|
| **Pew Research Center** | Religious demographics, restrictions indices by country | pewresearch.org datasets (downloadable) | Free |
| **Freedom House** | Freedom ratings, political rights, civil liberties scores | freedomhouse.org/report/freedom-world (API + CSV) | Free |
| **V-Dem Institute** | Democracy indices, 450+ indicators per country | v-dem.net API | Free |
| **UCDP** | Armed conflict data, actor profiles, peace agreements | ucdp.uu.se/apidocs | Free |
| **ETH Zurich ALED** | Armed group profiles, alliances, political wings | Already partially covered by ACLED | Free |

### Product Architecture
- **Ground Truth Free** — Current: context briefings for researchers/analysts (Sprints 1-7)
- **Ground Truth Diplomat** — Phase 2 premium tier: aid modeling, trade analysis, de-escalation scenarios, diplomatic channel mapping
- Same codebase, same API, same verification pipeline — different synthesis prompts + additional data sources

### Target Buyers
| Buyer | Why | Price Tier |
|-------|-----|-----------|
| **UN agencies** (UNDP, UNHCR, OCHA) | Aid allocation decisions | $500-2K/mo |
| **USAID / State Department** | Foreign aid strategy, diplomatic planning | $500-2K/mo (SDVOSB) |
| **EU External Action Service** | Neighborhood policy, trade agreements | $500-2K/mo |
| **US Institute of Peace (USIP)** | Conflict resolution research | $200-500/mo |
| **Think tanks** (Brookings, RAND, CFR, Chatham House) | Policy research | $199-499/mo |
| **University IR departments** | Teaching + research | $49/mo (academic tier) |

### Why This Wins
- **No competitor exists** in this space. Palantir serves the coercive side. Crisis Group writes reports manually. World Monitor shows real-time events. Nobody synthesizes primary sources into actionable diplomatic recommendations.
- **SDVOSB + military background** = credibility with federal/institutional buyers
- **Open-source core** = trust + transparency, critical for multilateral organizations that can't use proprietary black boxes
- **MIT license** = embeddable in UN/NGO systems without legal friction
- **Data sources are all free public APIs** — zero marginal cost for data, same as Phase 1

### Visualization Architecture (Opus Owns — Full Product Authority)

**Layer 1 — Interactive Globe (Entry Point)**
WebGL globe (deck.gl or Three.js) as landing view. Not flat Mercator — 3D globe signals global-scale tool.
- Red pulse: Active conflict (ACLED real-time) + high diplomatic friction score
- Amber: Elevated tension (GDELT spikes + governance decline + spoiler actor activity)
- Green: Stable / positive trajectory + low friction score
- Blue lines: Trade corridors (UN Comtrade, thickness = volume)
- Gold lines: Diplomatic channels (treaties + bilateral agreements)
- White dots: Aid allocation (OECD DAC, size = volume)
Click country → zooms to dashboard.

**Layer 2 — Country Dashboard (Analyst's Desk)**
- Left: GT context briefing (existing — historical narrative + analysis)
- Center: Relationship graph (D3.js force-directed) — trade, treaties, alliances, voting blocs. Click connection → bilateral detail.
- Right: Recommendation engine output (scenario cards)

**Layer 3 — Decision Matrix (Scenario Cards)**
AI-generated ranked intervention scenarios. Each card includes:
- Intervention type (trade bridge, aid package, diplomatic channel, security guarantee, multilateral framework)
- Feasibility score (computed from current conditions)
- Regional temperature reading (diplomatic friction score + contributing factors)
- Spoiler actors identified (rebel groups, opposition, radical factions — with capability and negotiation willingness ratings)
- Religious/ideological landscape summary (sectarian fault lines, political spectrum position)
- Historical precedents (from same primary sources)
- Dependency chain (what must be true for this to work)
- Risk factors (including spoiler disruption probability)
- Timeline estimate
- Data confidence rating
- Source citations for every claim

**Design principle:** System NEVER picks sides. Presents 3-5 scenarios with transparent reasoning. Human always decides. Every score shows its inputs. This is what makes it trustworthy for institutional buyers.

**Layer 4 — Comparison View**
Side-by-side scenario comparison (2-3 columns). Matching categories: feasibility, timeline, risk, cost, precedent. Export to PDF for briefing documents.

**Layer 5 — Early Warning Dashboard**
Time-series convergence detection:
- Food prices (FAO) → food insecurity
- Displacement (UNHCR) → humanitarian crisis
- Governance decline (WGI) → state fragility
- Arms imports (SIPRI) → militarization
- Conflict events (ACLED) → escalation
When multiple indicators converge → automated alert with historical pattern match and recommended review window.

**Visualization Tech Stack:**
- Globe: deck.gl (WebGL geospatial) or Three.js
- Relationship graphs: D3.js force-directed
- Charts/time-series: Recharts
- Maps (2D fallback): MapLibre GL JS (open source, no Mapbox license)
- GeoJSON: existing endpoint from Sprint 3

### Build Sequence (Estimated)
1. Sprint 7 — Deploy Phase 1 (Vercel + Railway), production hardening
2. Sprint 8 — UN Comtrade + WTO trade flow ingestors
3. Sprint 9 — OECD DAC + UNHCR + FAO ingestors
4. Sprint 10 — Diplomatic relationship graph (UN voting + treaty data)
5. Sprint 11 — Recommendation engine (intervention scenarios, aid modeling, scenario scoring algorithm)
6. Sprint 12 — Diplomat tier frontend (globe, dashboard, scenario cards, comparison view, early warning, PDF export)

### Key Decision
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-18 | Phase 2 = GT vertical, not new project | Same infra, same verification pipeline, same codebase. Avoids splitting engineering effort. |
| 2026-03-18 | "Palantir for peace" positioning | No competitor occupies this space. Different buyer, different mission, different market than Palantir. |
| 2026-03-18 | All new data sources are free public APIs | Zero marginal data cost. Same economic model as Phase 1. |
| 2026-03-18 | Opus has full product authority on Phase 2 UX/visualization | Decision matrix design, scenario scoring, globe visualization, all frontend architecture decisions flow through Opus. Lawrence executes + approves spend. |
| 2026-03-18 | Interactive 3D globe as entry point | Signals global-scale institutional tool. Color-coded layers (conflict/trade/diplomatic/aid) make complex data immediately visual. deck.gl or Three.js, not flat maps. |
| 2026-03-18 | System never picks sides | Presents ranked scenarios with transparent reasoning + source citations. Human always decides. Critical for institutional trust (UN, USAID won't use a tool that makes decisions for them). |

## Competitive Positioning
- **World Monitor** = radar screen (WHAT is happening now). Real-time event feed, macro analytics, equity overlays. 2M+ users, AGPL license, Pro tier on waitlist at $0 (no revenue yet). Created by Elie Habib (Anghami CTO).
- **Ground Truth** = analyst's desk (WHY it's happening). Historical context, primary source citations, multi-perspective frameworks. MIT license.
- **Integration play**: WM users click a hotspot → GT provides the deep briefing. WM's 2M users = our distribution channel. No marketing spend needed.
- **Differentiation**: GT's military data layer (SIPRI arms transfers, FAS nuclear notebooks, OFAC sanctions) serves defense/policy audience that WM doesn't touch. That's the federal $500-2K/mo tier.
- **WM's equity/macro features** are financial data overlays for traders. GT's evidence pipeline + historical depth + citation rigor serves a different use case entirely.

# currentDate
Today's date is 2026-03-18.

## Rules
1. Primary sources only — no exceptions
2. Every claim must cite its source
3. Context reports present multiple perspectives — engine doesn't pick sides
4. Antigravity QA pipeline must pass before any report goes public
5. Ship > perfect. Get the MVP working, then refine.
