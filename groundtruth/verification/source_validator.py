"""Source Validator — Ground Truth Verification Pipeline.

Validates that all sources cited in a context report are:
  - From an approved authoritative domain
  - Resolvable (live URL or Wayback Machine fallback)
  - Appropriately recent for the context period

This is Deliverable 1 of the Antigravity verification pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
import structlog

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Path to approved sources doc — relative to repo root
# ---------------------------------------------------------------------------
_APPROVED_SOURCES_DOC = (
    Path(__file__).parent.parent.parent / "docs" / "APPROVED_SOURCES.md"
)

# Hardcoded fallback in case the doc can't be read
_FALLBACK_APPROVED_DOMAINS: frozenset[str] = frozenset(
    {
        # US Government
        "loc.gov",
        "archives.gov",
        "cia.gov",
        "state.gov",
        "congress.gov",
        "foreignassistance.gov",
        "usitc.gov",
        "fbi.gov",
        "treasury.gov",
        "defense.gov",
        "fas.org",
        "dni.gov",
        "cbo.gov",
        # International Institutions
        "data.worldbank.org",
        "gdeltproject.org",
        "acleddata.com",
        "ucdp.uu.se",
        "data.humdata.org",
        "unscr.com",
        "comtrade.un.org",
        "sipri.org",
        "transparency.org",
        "icj-cij.org",
        "icc-cpi.int",
        # Allied Government Archives
        "nationalarchives.gov.uk",
        "archives.nato.int",
        "naa.gov.au",
        "aspi.org.au",
        # Academic / Research
        "doi.org",
        "jstor.org",
        "zenodo.org",
        # Geographic Data
        "geonames.org",
        "naturalearthdata.com",
    }
)

# Domains that are explicitly blocked (for fast rejection + clear messaging)
_BLOCKED_DOMAINS: frozenset[str] = frozenset(
    {
        "wikipedia.org",
        "en.wikipedia.org",
        "twitter.com",
        "x.com",
        "reddit.com",
        "facebook.com",
        "instagram.com",
        "telegram.org",
        "nytimes.com",
        "bbc.com",
        "bbc.co.uk",
        "reuters.com",
        "aljazeera.com",
        "theguardian.com",
        "washingtonpost.com",
        "cnn.com",
        "foxnews.com",
        "medium.com",
        "substack.com",
    }
)

# Freshness thresholds in years
_DATED_THRESHOLD_YEARS = 2
_STALE_THRESHOLD_YEARS = 10

# HTTP request config
_HTTP_TIMEOUT = 10.0  # seconds
_WAYBACK_CDX_URL = "https://archive.org/wayback/available?url={url}"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SourceValidation:
    """Validation result for a single cited source."""

    url: str
    domain: str
    is_approved: bool
    is_live: bool | None  # None = not checked (e.g., domain already failed)
    wayback_url: str | None
    freshness: str  # 'current' | 'dated' | 'stale' | 'unknown'
    status: str  # 'pass' | 'warn' | 'fail'
    notes: str


@dataclass
class ValidationResult:
    """Aggregate validation result for a full context report."""

    total_sources: int
    passed: int
    warned: int
    failed: int
    details: list[SourceValidation] = field(default_factory=list)
    overall_status: str = "pass"  # 'pass' | 'warn' | 'fail'

    def __post_init__(self) -> None:
        if self.failed > 0:
            self.overall_status = "fail"
        elif self.warned > 0:
            self.overall_status = "warn"
        else:
            self.overall_status = "pass"


# ---------------------------------------------------------------------------
# Approved domain loading
# ---------------------------------------------------------------------------


def _parse_approved_domains(markdown_path: Path) -> frozenset[str]:
    """Parse domain column from APPROVED_SOURCES.md markdown tables.

    Looks for table rows in the format:  | domain.tld | ... |
    Skips header rows and separator rows.
    """
    domains: set[str] = set()
    try:
        text = markdown_path.read_text(encoding="utf-8")
    except OSError:
        log.warning("approved_sources.md not readable — using fallback domain list")
        return _FALLBACK_APPROVED_DOMAINS

    # Match table data rows: | something.tld | ... |
    # Domain column is the first column (after leading |)
    pattern = re.compile(r"^\|\s*([a-z0-9][\w.\-]*\.[a-z]{2,})\s*\|", re.MULTILINE)
    for match in pattern.finditer(text):
        candidate = match.group(1).strip().lower()
        # Skip obvious header/separator artifacts
        if candidate in {"domain", "---", ""}:
            continue
        domains.add(candidate)

    if not domains:
        log.warning("No domains parsed from APPROVED_SOURCES.md — using fallback")
        return _FALLBACK_APPROVED_DOMAINS

    log.info("approved_domains_loaded", count=len(domains))
    return frozenset(domains)


# ---------------------------------------------------------------------------
# SourceValidator
# ---------------------------------------------------------------------------


class SourceValidator:
    """Validates source citations in a Ground Truth context report.

    Usage::

        validator = SourceValidator()
        result = await validator.validate_report(report_dict)
        print(result.overall_status)   # 'pass' | 'warn' | 'fail'
    """

    def __init__(
        self,
        approved_sources_path: Path | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        path = approved_sources_path or _APPROVED_SOURCES_DOC
        self._approved_domains = _parse_approved_domains(path)
        self._http_client = http_client  # injected in tests; created lazily in prod

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def validate_report(self, report: dict) -> ValidationResult:
        """Run all validation checks on a context report.

        Expects ``report`` to contain a ``"sources"`` list, where each item
        is either a URL string or a dict with a ``"url"`` key and an optional
        ``"date"`` key.

        Returns a :class:`ValidationResult` with per-source details.
        """
        raw_sources: list = report.get("sources", [])
        context_date: str = report.get(
            "date", datetime.utcnow().strftime("%Y-%m-%d")
        )

        details: list[SourceValidation] = []

        async with self._get_client() as client:
            for item in raw_sources:
                if isinstance(item, str):
                    url, source_date = item, None
                elif isinstance(item, dict):
                    url = item.get("url", "")
                    source_date = item.get("date")
                else:
                    continue

                if not url:
                    continue

                sv = await self._validate_source(client, url, source_date, context_date)
                details.append(sv)

        passed = sum(1 for d in details if d.status == "pass")
        warned = sum(1 for d in details if d.status == "warn")
        failed = sum(1 for d in details if d.status == "fail")

        result = ValidationResult(
            total_sources=len(details),
            passed=passed,
            warned=warned,
            failed=failed,
            details=details,
        )
        log.info(
            "report_validated",
            total=result.total_sources,
            passed=passed,
            warned=warned,
            failed=failed,
            overall=result.overall_status,
        )
        return result

    def check_domain_approved(self, url: str) -> tuple[bool, str]:
        """Check if a URL's domain is on the approved authoritative source list.

        Returns:
            (is_approved, note) — note explains the result.
        """
        domain = self._extract_domain(url)
        if not domain:
            return False, "Could not parse domain from URL"

        if domain in _BLOCKED_DOMAINS:
            return False, f"Domain '{domain}' is explicitly blocked (not a primary source)"

        # Check exact match or subdomain match
        if domain in self._approved_domains:
            return True, f"Domain '{domain}' is approved"

        # Check if it's a subdomain of an approved domain
        # e.g., "api.worldbank.org" should match "data.worldbank.org" sibling → worldbank.org root
        for approved in self._approved_domains:
            if domain.endswith("." + approved) or domain == approved:
                return True, f"Domain '{domain}' matches approved domain '{approved}'"

        # Check parent domain match (e.g., api.archives.gov → archives.gov)
        parts = domain.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[i:])
            if parent in self._approved_domains:
                return True, f"Domain '{domain}' is subdomain of approved '{parent}'"

        return False, f"Domain '{domain}' is not on the approved sources list"

    async def check_url_live(self, url: str) -> bool:
        """Verify a URL is reachable via HEAD request (follows redirects).

        Returns True if the server responds with a non-error status code.
        """
        async with self._get_client() as client:
            return await self._head_request(client, url)

    async def check_wayback_fallback(self, url: str) -> str | None:
        """Check Internet Archive Wayback Machine for a cached snapshot.

        Returns the snapshot URL if one exists, otherwise None.
        """
        async with self._get_client() as client:
            return await self._query_wayback(client, url)

    def check_date_freshness(
        self, source_date: str, report_context_date: str
    ) -> str:
        """Assess how fresh a source is relative to the context period.

        Args:
            source_date: ISO 8601 date string for the source (YYYY-MM-DD or YYYY).
            report_context_date: ISO 8601 date string for the context event.

        Returns:
            'current'  — within 2 years of context date
            'dated'    — 2–10 years older than context date
            'stale'    — more than 10 years older
            'unknown'  — could not parse dates
        """
        try:
            src_year = self._parse_year(source_date)
            ctx_year = self._parse_year(report_context_date)
        except (ValueError, TypeError):
            return "unknown"

        gap = ctx_year - src_year
        if gap < 0:
            # Source is newer than context date — treat as current
            return "current"
        if gap <= _DATED_THRESHOLD_YEARS:
            return "current"
        if gap <= _STALE_THRESHOLD_YEARS:
            return "dated"
        return "stale"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _validate_source(
        self,
        client: httpx.AsyncClient,
        url: str,
        source_date: str | None,
        context_date: str,
    ) -> SourceValidation:
        """Run all checks on a single source URL and return a SourceValidation."""
        domain = self._extract_domain(url)
        is_approved, approval_note = self.check_domain_approved(url)
        notes_parts = [approval_note]

        # Domain not approved → immediate fail, skip liveness check
        if not is_approved:
            freshness = (
                self.check_date_freshness(source_date, context_date)
                if source_date
                else "unknown"
            )
            return SourceValidation(
                url=url,
                domain=domain,
                is_approved=False,
                is_live=None,
                wayback_url=None,
                freshness=freshness,
                status="fail",
                notes="; ".join(notes_parts),
            )

        # Check liveness
        is_live = await self._head_request(client, url)
        wayback_url: str | None = None

        if not is_live:
            wayback_url = await self._query_wayback(client, url)
            if wayback_url:
                notes_parts.append(f"URL dead — Wayback snapshot found: {wayback_url}")
            else:
                notes_parts.append("URL dead — no Wayback snapshot available")

        # Date freshness
        freshness = (
            self.check_date_freshness(source_date, context_date)
            if source_date
            else "unknown"
        )
        if freshness == "stale":
            notes_parts.append(
                f"Source date '{source_date}' is stale relative to context '{context_date}'"
            )
        elif freshness == "dated":
            notes_parts.append(
                f"Source date '{source_date}' is dated relative to context '{context_date}'"
            )

        # Determine status
        if not is_live and not wayback_url:
            status = "warn"  # approved domain but completely unreachable
        elif freshness == "stale" or (not is_live and wayback_url):
            status = "warn"
        else:
            status = "pass"

        return SourceValidation(
            url=url,
            domain=domain,
            is_approved=True,
            is_live=is_live,
            wayback_url=wayback_url,
            freshness=freshness,
            status=status,
            notes="; ".join(notes_parts),
        )

    async def _head_request(self, client: httpx.AsyncClient, url: str) -> bool:
        """Send HEAD request. Returns True on 2xx/3xx, False otherwise."""
        try:
            resp = await client.head(url, follow_redirects=True, timeout=_HTTP_TIMEOUT)
            return resp.status_code < 400
        except Exception as exc:
            log.debug("url_check_failed", url=url, error=str(exc))
            return False

    async def _query_wayback(self, client: httpx.AsyncClient, url: str) -> str | None:
        """Query Wayback Machine CDX API for a snapshot of the given URL."""
        cdx_url = _WAYBACK_CDX_URL.format(url=url)
        try:
            resp = await client.get(cdx_url, timeout=_HTTP_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            snapshot = data.get("archived_snapshots", {}).get("closest", {})
            if snapshot.get("available"):
                return snapshot.get("url")
        except Exception as exc:
            log.debug("wayback_check_failed", url=url, error=str(exc))
        return None

    def _get_client(self) -> httpx.AsyncClient:
        """Return the injected HTTP client, or create a default one."""
        if self._http_client is not None:
            # Return a context manager wrapper that doesn't close injected client
            return _NoCloseClient(self._http_client)
        return httpx.AsyncClient()

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract the netloc/domain from a URL string."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().lstrip("www.")
        except Exception:
            return ""

    @staticmethod
    def _parse_year(date_str: str) -> int:
        """Parse a year from an ISO date string (YYYY-MM-DD or YYYY)."""
        return int(str(date_str).strip()[:4])


# ---------------------------------------------------------------------------
# Thin wrapper so injected test clients aren't closed by `async with`
# ---------------------------------------------------------------------------


class _NoCloseClient:
    """Wraps an existing AsyncClient so `async with` doesn't close it."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def __aenter__(self) -> httpx.AsyncClient:
        return self._client

    async def __aexit__(self, *_: object) -> None:
        pass  # Don't close — caller owns the lifecycle

    # Proxy attribute access for direct usage (e.g. await validator.check_url_live)
    def __getattr__(self, name: str):  # noqa: ANN204
        return getattr(self._client, name)
