# Contributing to Ground Truth

Thanks for wanting to contribute. Here's how to get involved.

## Ground Rules

1. **Primary sources only.** Every data integration must trace to an authoritative origin — government archives, institutional databases, declassified intelligence, verified primary sources. No Wikipedia. No news articles. No secondary media.

2. **Engineered neutrality.** Context reports present multiple interpretive frameworks with evidence for each. The engine does not pick sides. If your contribution introduces editorial bias, it will be rejected.

3. **Source transparency.** Every claim in a context report must link to its primary source. If a source can't be cited, the claim doesn't ship.

## How to Contribute

### Reporting Issues
- Use GitHub Issues
- Include: what you expected, what happened, steps to reproduce
- For data accuracy issues: include the source you believe is correct with a link

### Adding Data Source Integrations
1. Fork the repo
2. Create a branch: `git checkout -b source/your-source-name`
3. Add your integration in `groundtruth/ingestion/`
4. Follow the existing pattern (see `gdelt.py` or `worldbank.py` as examples)
5. Include tests in `tests/ingestion/`
6. Document the source in `docs/sources/`
7. Submit a PR with:
   - Source name, URL, and data description
   - Access method (API, bulk download, scrape)
   - Rate limits and authentication requirements
   - Why this source is authoritative

### Improving the Verification Pipeline
- Work lives in `groundtruth/verification/`
- Focus areas: source validation, date verification, bias detection
- All verification logic must be testable and deterministic

### Frontend Contributions
- Work lives in `frontend/`
- React 18 + TypeScript
- Keep it minimal — this is a tool, not a media site

## Development Setup

```bash
git clone https://github.com/lmagee3/ground-truth.git
cd ground-truth
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest  # run tests
```

## Code Style
- Python: Black formatter, isort for imports, type hints required
- TypeScript: Prettier + ESLint
- All functions need docstrings
- Tests for all new functionality

## PR Process
1. All PRs require review
2. CI must pass (linting, tests, type checks)
3. Data source PRs require documentation
4. Keep PRs focused — one feature or fix per PR
