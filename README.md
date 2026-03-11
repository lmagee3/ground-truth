<p align="center">
  <img src="docs/banner.png" alt="Ground Truth" width="800"/>
</p>

<h1 align="center">GROUND TRUTH</h1>
<p align="center">
  <strong>Open-Source Geopolitical Context Engine</strong><br>
  <em>The intelligence briefing behind the radar blip</em>
</p>

<p align="center">
  <a href="https://github.com/lmagee3/ground-truth/actions"><img src="https://img.shields.io/github/actions/workflow/status/lmagee3/ground-truth/ci.yml?style=flat-square" alt="CI"></a>
  <a href="https://github.com/lmagee3/ground-truth/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://github.com/lmagee3/ground-truth/stargazers"><img src="https://img.shields.io/github/stars/lmagee3/ground-truth?style=flat-square" alt="Stars"></a>
  <a href="https://pypi.org/project/ground-truth/"><img src="https://img.shields.io/pypi/v/ground-truth?style=flat-square" alt="PyPI"></a>
  <a href="https://discord.gg/groundtruth"><img src="https://img.shields.io/badge/discord-join-7289da?style=flat-square" alt="Discord"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#what-it-does">What It Does</a> •
  <a href="#data-sources">Data Sources</a> •
  <a href="#api">API</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## What It Does

**Ground Truth** answers one question: **"How did we get here?"**

Tools like [World Monitor](https://worldmonitor.app) show you *what* is happening on the globe right now. News outlets tell you *what* with editorial spin. Ground Truth shows you **why** — the chain of events, treaties, economic pressures, and power shifts that led to this exact moment.

**No media narrative. No spin. No feelings spared.**

Just primary sources, verified data, and structured historical context — delivered as an API that anyone can integrate.

### Example

```bash
curl https://api.groundtruth.dev/v1/context \
  -H "Authorization: Bearer $GT_API_KEY" \
  -d '{"query": "South China Sea tensions", "depth": "comprehensive"}'
```

Returns a structured intelligence briefing with:
- Historical timeline (treaty violations, territorial claims since 1947)
- Economic context (trade dependencies, shipping lane volumes)
- Military context (arms transfers, base deployments, exercises)
- Multiple interpretive frameworks (no single narrative)
- Every claim linked to its primary source

## Quick Start

```bash
# Clone
git clone https://github.com/lmagee3/ground-truth.git
cd ground-truth

# Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure (minimal — most sources need no API key)
cp .env.example .env
# Edit .env with your optional API keys (ACLED, NARA, etc.)

# Run
uvicorn groundtruth.api.main:app --reload

# Open API docs
open http://localhost:8000/docs
```

## Data Sources

Ground Truth uses **only primary, authoritative sources**. No Wikipedia. No news articles. Every data point traces to a government archive, institutional database, or verified primary source.

### Tier 1 — Core (Real-Time + Historical)
| Source | Data | Access | Update Frequency |
|--------|------|--------|-----------------|
| [GDELT](https://gdeltproject.org) | 250M+ global events, 300+ categories, 100+ languages | BigQuery + API | Every 15 minutes |
| [ACLED](https://acleddata.com) | 1.3M+ conflict events, 200+ countries | REST API (free acct) | Near real-time |
| [UCDP Uppsala](https://ucdp.uu.se) | 500+ variables, 18 conflict datasets since 1946 | Public API | Updated regularly |
| [World Bank](https://data.worldbank.org) | 16,000+ development indicators, 50+ years | REST API (no key) | Continuous |
| [Library of Congress](https://loc.gov) | Digital collections, congressional records, maps | REST API (no key) | Continuous |
| [CIA World Factbook](https://www.cia.gov/the-world-factbook/) | 260 countries, 200+ fields each | JSON (GitHub mirror) | Weekly |
| [NARA](https://catalog.archives.gov) | 30M+ records, declassified intelligence | REST API (free key) | Continuous |

### Tier 2 — Historical Context
| Source | Data | Access |
|--------|------|--------|
| [State Dept FRUS](https://history.state.gov/historicaldocuments) | 350+ volumes of US diplomatic history since 1861 | HTML/PDF |
| [Congressional Research Service](https://crsreports.congress.gov) | Non-partisan policy analysis reports | API (free key) |
| [UK National Archives](https://nationalarchives.gov.uk) | 32M+ records, declassified MI5/MI6 | API (IP registration) |
| [SIPRI](https://sipri.org) | Arms transfers since 1950, military spending | CSV/Excel download |
| [UN Security Council](https://unscr.com) | 2,802 resolutions since 1946 | Structured corpus |
| [UN HDX](https://data.humdata.org) | 18,110+ humanitarian datasets | API |

### Tier 3 — Enrichment
| Source | Data | Access |
|--------|------|--------|
| [UN Comtrade](https://comtrade.un.org) | Bilateral trade data, 170+ countries | REST API |
| [Transparency International](https://transparency.org) | Corruption Perceptions Index | CSV/JSON |
| [USAID](https://foreignassistance.gov) | US foreign aid flows by country/sector | API |
| [NATO Archives](https://archives.nato.int) | 76 years of alliance documents | Web access |
| [GeoNames](https://geonames.org) | 11M+ placenames, boundaries | REST API |

## API

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/context/{query}` | Generate historical context for an event or region |
| `GET` | `/v1/timeline/{region}` | Get event timeline for a geographic region |
| `GET` | `/v1/briefing/{topic}` | Generate full intelligence briefing |
| `GET` | `/v1/compare/{event_a}/{event_b}` | Compare historical patterns between events |
| `GET` | `/v1/sources/{report_id}` | Get all primary sources for a context report |

### Response Format

Every response includes:
- `context` — Structured historical narrative
- `timeline` — Chronological event chain
- `perspectives` — Multiple interpretive frameworks
- `sources` — Every claim linked to its primary source with URL
- `confidence` — Source reliability assessment
- `metadata` — Query parameters, data freshness, coverage gaps

### Rate Limits

| Tier | Requests/Day | Price |
|------|-------------|-------|
| Free | 100 | $0 |
| Pro | Unlimited | $49/mo |
| Enterprise | Unlimited + SLA | $199-499/mo |

## Architecture

```
┌─────────────────────────────────────────────────┐
│              GROUND TRUTH ENGINE                 │
├──────────────┬──────────────┬───────────────────┤
│  INGESTION   │  SYNTHESIS   │     OUTPUT        │
│              │              │                   │
│ GDELT ──────▶│              │──▶ REST API       │
│ ACLED ──────▶│  AI Context  │──▶ Web Frontend   │
│ UCDP ───────▶│  Engine      │──▶ Integrations   │
│ LOC ────────▶│              │──▶ Embeddable      │
│ NARA ───────▶│  (Claude /   │    Widget         │
│ CIA FB ─────▶│   Ollama)    │                   │
│ World Bank ─▶│              │                   │
│              ├──────────────┤                   │
│              │ VERIFICATION │                   │
│              │ Source check  │                   │
│              │ Bias detect   │                   │
│              │ Fact verify   │                   │
└──────────────┴──────────────┴───────────────────┘

Stack: Python 3.11+ / FastAPI / PostgreSQL + pgvector / Redis / React 18
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Priority Areas
- **Data source integrations** — Adding new authoritative primary sources
- **Verification pipeline** — Improving fact-checking and bias detection
- **API clients** — SDKs for JavaScript, Go, Rust
- **Frontend** — Globe visualization, context panels, search UX
- **Documentation** — API examples, tutorials, use cases

## License

[MIT](LICENSE) — Use it however you want.

## Built By

**[Chaos Monk](https://chaosmonk.netlify.app)** — Open-source tools by [MAGE Software](https://malleusprendere.cloud) (Malleus Prendere LLC)

Created by a 20-year US Army veteran who got tired of media spin and built the tool he wished existed.

---

<p align="center">
  <strong>World Monitor shows you the radar blip.<br>Ground Truth gives you the intelligence briefing.</strong>
</p>
