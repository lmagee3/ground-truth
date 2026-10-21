# Measuring Ground Truth's primary-source rule

The numbers below come from the [measurement script](../../scripts/measure_source_validator.py)
run against the current source-domain validator. The findings are limited to this small test set.

## Why this matters

Ground Truth's first stated principle is *"primary sources only, no Wikipedia, no news articles, no
editorial content."* That is the whole point of the tool. If it lets a news article or a blog in, the
briefing it produces is harder to trust. So the useful question is not just "does it run?" It is
how well the code actually enforces that rule. The measurement focuses on the component that makes the call:
`SourceValidator.check_domain_approved()`.

## Method

The check is pure domain logic. It needs no API keys, no network, and no database, so anyone can
reproduce it. The test uses **39 labeled URLs**. Each was assigned an expected result using the
project's own policy: accept = primary authoritative government, institutional, or recognized academic
source; reject = news, encyclopedia, social media, or general commercial content. The set deliberately
includes subdomains (`api.congress.gov`, `home.treasury.gov`) and five legitimate
primary sources not on the approved list. The script runs each URL through the validator
(which loads the 33-domain list from `docs/APPROVED_SOURCES.md`) and compares its decision to
the label.

## Results

| Metric | Value |
|---|---|
| Dataset | 39 labeled URLs (23 accept / 16 reject) |
| Accuracy | **87.2%** |
| Precision | **100.0%** |
| Recall | **78.3%** |
| F1 | **87.8%** |

Confusion matrix: 18 true-accept, 16 true-reject, **0 false-accept**, 5 missed.

**In this set, the validator accepted no non-primary sources.** It rejected all 16 news, encyclopedia,
social-media, and general commercial URLs we tested. That matters because accepting one of those URLs
as primary evidence would weaken the tool's results. This small test does not prove it will reject every
non-primary source on the web.

## Two findings worth acting on

**1. Recall is held back by list coverage (the 5 misses).** The validator rejected five legitimate
primary sources (`un.org`, `census.gov`, `nasa.gov`, `bls.gov`, `whitehouse.gov`) because
they are not on the 33-domain approved list. The validator is cautious, but it can reject useful primary
sources it has not been told about. That list needs regular review, and the limitation should be clear
to users.

**2. A domain-parsing bug, found while testing `whitehouse.gov`.** That URL did not just fail the check.
The validator reported the domain as **`hitehouse.gov`**. It was eating the leading letter. Tracing it:

```python
# groundtruth/verification/source_validator.py, _extract_domain()
return parsed.netloc.lower().lstrip("www.")
```

`str.lstrip("www.")` treats `"www."` as a set of characters to strip, not as a prefix. So it removes any
leading `w` or `.`, and every `www.`-prefixed host whose name then starts with `w` loses letters:

| Input | Extracted (buggy) |
|---|---|
| `www.whitehouse.gov` | `hitehouse.gov` |
| `www.worldbank.org` | `orldbank.org` |
| `www.who.int` | `ho.int` |
| `www.wto.org` | `to.org` |
| `www3.weforum.org` | `3.weforum.org` |

In this project the approved list carries no `w`-initial domains and cites World Bank as
`data.worldbank.org`, so the current test examples avoid the problem. In practice, a `www.worldbank.org`,
`www.who.int`, or `www.wto.org` citation would be mis-read and then wrongly rejected.

**A fix is proposed in [PR #1](https://github.com/lmagee3/ground-truth/pull/1).** Replacing
`lstrip("www.")` with `removeprefix("www.")` (Python 3.9+) removes only the exact prefix. Four new tests
cover the affected URLs. The table shows the results after applying the patch locally:

| Input | Before (`lstrip`) | After (`removeprefix`) |
|---|---|---|
| `www.whitehouse.gov` | `hitehouse.gov` | `whitehouse.gov` |
| `www.worldbank.org` | `orldbank.org` | `worldbank.org` |
| `www.who.int` | `ho.int` | `who.int` |
| `www3.weforum.org` | `3.weforum.org` | `www3.weforum.org` (unchanged, correct) |
| `www.cia.gov` | `cia.gov` | `cia.gov` (still works) |

The rerun left the headline metrics unchanged (87.2% / 100% / 78.3%). That makes sense: the
bug affected domain parsing, not the approved list, so
the five misses remain. What changed is the reason the tool gives: the `whitehouse.gov` miss now reports
correctly as a coverage gap (`'whitehouse.gov' is not on the approved sources list`) instead of the
mangled `'hitehouse.gov'`. Before the fix the tool rejected `whitehouse.gov` for the wrong reason. After
the fix it rejects it for the right reason, which is simply that the domain is not on the list yet.

## Test status (verified vs claimed)

The README cites "71 tests passing." Local runs found **62 passed** in `tests/verification` and
`tests/synthesis` before the fix and **66 passed** after adding four new tests. The 66-test result was
rechecked on October 21, 2026. These runs used Python 3.10. The project targets Python 3.11 or later,
and the full suite was not run with its database and Redis services. The README's 71-test claim remains
unverified here.

## Limitations (so the number is not oversold)

- The 39 hand-labeled URLs form a small, selected set, not a standard benchmark. The labels reflect this
  project's source policy, not a universal definition of "primary."
- This is a domain check only. It does not verify a page's content, whether the page still exists, or
  whether it has changed over time.
- Results are specific to the 33-domain list in `docs/APPROVED_SOURCES.md` at the tested commit.

## Reproduce it

```bash
git clone https://github.com/lmagee3/ground-truth.git
cd ground-truth
python3 -m venv .venv && . .venv/bin/activate
python -m pip install httpx pydantic pydantic-settings sqlalchemy structlog python-dotenv
PYTHONPATH=. python scripts/measure_source_validator.py
```

## Authorship and review

Ground Truth and this report were developed with AI assistance. Lawrence Magee reviewed the findings
and approved this report for publication. The linked script, test cases, and pull request show the
method and proposed fix so readers can inspect the work directly.
