"""Tests for groundtruth.verification.source_validator."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from groundtruth.verification.source_validator import (
    SourceValidation,
    SourceValidator,
    ValidationResult,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def validator() -> SourceValidator:
    """SourceValidator with default approved domains (loaded from APPROVED_SOURCES.md)."""
    return SourceValidator()


@pytest.fixture()
def good_report() -> dict:
    return json.loads((FIXTURES_DIR / "good_report.json").read_text())


@pytest.fixture()
def bad_report() -> dict:
    return json.loads((FIXTURES_DIR / "bad_report.json").read_text())


# ---------------------------------------------------------------------------
# Domain approval checks (synchronous — no I/O)
# ---------------------------------------------------------------------------


class TestCheckDomainApproved:
    """Unit tests for check_domain_approved — no network required."""

    def test_approved_us_gov_domain(self, validator):
        approved, note = validator.check_domain_approved("https://loc.gov/collections/foo")
        assert approved is True
        assert "approved" in note.lower()

    def test_approved_worldbank(self, validator):
        approved, _ = validator.check_domain_approved(
            "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD"
        )
        assert approved is True

    def test_approved_cia_factbook(self, validator):
        approved, _ = validator.check_domain_approved(
            "https://www.cia.gov/the-world-factbook/countries/china/"
        )
        assert approved is True

    def test_approved_nato_archives(self, validator):
        approved, _ = validator.check_domain_approved("https://archives.nato.int/foo")
        assert approved is True

    def test_approved_acled(self, validator):
        approved, _ = validator.check_domain_approved("https://acleddata.com/data/")
        assert approved is True

    def test_explicitly_blocked_wikipedia(self, validator):
        approved, note = validator.check_domain_approved(
            "https://en.wikipedia.org/wiki/South_China_Sea"
        )
        assert approved is False
        assert "blocked" in note.lower()

    def test_explicitly_blocked_nytimes(self, validator):
        approved, note = validator.check_domain_approved(
            "https://www.nytimes.com/2024/01/01/world/story.html"
        )
        assert approved is False

    def test_explicitly_blocked_twitter(self, validator):
        approved, _ = validator.check_domain_approved("https://twitter.com/someuser/status/123")
        assert approved is False

    def test_unapproved_unknown_domain(self, validator):
        approved, note = validator.check_domain_approved("https://randomnewssite.com/article")
        assert approved is False
        assert "not on the approved" in note.lower()

    def test_subdomain_of_approved(self, validator):
        """Subdomains of approved domains (e.g., api.archives.gov) should pass."""
        approved, _ = validator.check_domain_approved("https://api.archives.gov/v1/records")
        assert approved is True

    def test_malformed_url(self, validator):
        approved, note = validator.check_domain_approved("not-a-url")
        assert approved is False


# ---------------------------------------------------------------------------
# Date freshness checks (synchronous — no I/O)
# ---------------------------------------------------------------------------


class TestCheckDateFreshness:
    def test_current_same_year(self, validator):
        assert validator.check_date_freshness("2024-03-01", "2024-06-15") == "current"

    def test_current_within_2_years(self, validator):
        assert validator.check_date_freshness("2022-08-01", "2024-06-15") == "current"

    def test_dated_3_years(self, validator):
        assert validator.check_date_freshness("2021-01-01", "2024-06-15") == "dated"

    def test_dated_10_years(self, validator):
        assert validator.check_date_freshness("2014-06-01", "2024-06-15") == "dated"

    def test_stale_more_than_10_years(self, validator):
        assert validator.check_date_freshness("1989-03-10", "2024-06-15") == "stale"

    def test_source_newer_than_context(self, validator):
        """Source published after context date is treated as current."""
        assert validator.check_date_freshness("2025-01-01", "2024-06-15") == "current"

    def test_year_only_strings(self, validator):
        assert validator.check_date_freshness("2010", "2024") == "stale"

    def test_unparseable_date(self, validator):
        assert validator.check_date_freshness("unknown", "2024-06-15") == "unknown"


# ---------------------------------------------------------------------------
# URL liveness check (async — HTTP mocked)
# ---------------------------------------------------------------------------


class TestCheckUrlLive:
    @pytest.mark.asyncio
    async def test_live_url_returns_true(self, validator):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.head = AsyncMock(return_value=mock_resp)

        v = SourceValidator(http_client=mock_client)
        result = await v.check_url_live("https://data.worldbank.org/")
        assert result is True

    @pytest.mark.asyncio
    async def test_404_returns_false(self, validator):
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.head = AsyncMock(return_value=mock_resp)

        v = SourceValidator(http_client=mock_client)
        result = await v.check_url_live("https://data.worldbank.org/gone")
        assert result is False

    @pytest.mark.asyncio
    async def test_connection_error_returns_false(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.head = AsyncMock(side_effect=httpx.ConnectError("refused"))

        v = SourceValidator(http_client=mock_client)
        result = await v.check_url_live("https://unreachable.example.com/")
        assert result is False

    @pytest.mark.asyncio
    async def test_timeout_returns_false(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.head = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        v = SourceValidator(http_client=mock_client)
        result = await v.check_url_live("https://slow.example.com/")
        assert result is False


# ---------------------------------------------------------------------------
# Wayback Machine fallback (async — HTTP mocked)
# ---------------------------------------------------------------------------


class TestCheckWaybackFallback:
    @pytest.mark.asyncio
    async def test_snapshot_found(self):
        wayback_response = {
            "archived_snapshots": {
                "closest": {
                    "available": True,
                    "url": "https://web.archive.org/web/20230601120000/https://example.gov/page",
                    "timestamp": "20230601120000",
                    "status": "200",
                }
            }
        }
        mock_resp = MagicMock()
        mock_resp.json = MagicMock(return_value=wayback_response)
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_resp)

        v = SourceValidator(http_client=mock_client)
        result = await v.check_wayback_fallback("https://example.gov/page")
        assert result == "https://web.archive.org/web/20230601120000/https://example.gov/page"

    @pytest.mark.asyncio
    async def test_no_snapshot_returns_none(self):
        wayback_response = {"archived_snapshots": {}}

        mock_resp = MagicMock()
        mock_resp.json = MagicMock(return_value=wayback_response)
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=mock_resp)

        v = SourceValidator(http_client=mock_client)
        result = await v.check_wayback_fallback("https://deadlink.gov/page")
        assert result is None

    @pytest.mark.asyncio
    async def test_wayback_request_error_returns_none(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        v = SourceValidator(http_client=mock_client)
        result = await v.check_wayback_fallback("https://example.gov/page")
        assert result is None


# ---------------------------------------------------------------------------
# Full report validation (async — HTTP mocked)
# ---------------------------------------------------------------------------


class TestValidateReport:
    @pytest.mark.asyncio
    async def test_good_report_passes(self, good_report):
        """All approved-domain, live sources → overall_status = 'pass'."""
        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.head = AsyncMock(return_value=mock_resp_ok)
        # Wayback should NOT be called for live URLs
        mock_client.get = AsyncMock(return_value=MagicMock())

        v = SourceValidator(http_client=mock_client)
        result = await v.validate_report(good_report)

        assert isinstance(result, ValidationResult)
        assert result.total_sources == 4
        assert result.failed == 0
        assert result.overall_status in ("pass", "warn")  # dated sources may warn

    @pytest.mark.asyncio
    async def test_bad_report_fails(self, bad_report):
        """Wikipedia + news outlet → at least 2 failures → overall_status = 'fail'."""
        mock_resp_ok = MagicMock()
        mock_resp_ok.status_code = 200
        mock_resp_dead = MagicMock()
        mock_resp_dead.status_code = 404

        # 3rd source (archives.gov dead link) returns 404; others 200
        call_count = {"n": 0}

        async def head_side_effect(url, **kwargs):
            call_count["n"] += 1
            if "thisurldoesnotexistatall" in url:
                return mock_resp_dead
            return mock_resp_ok

        no_snapshot = {"archived_snapshots": {}}
        mock_wayback_resp = MagicMock()
        mock_wayback_resp.json = MagicMock(return_value=no_snapshot)
        mock_wayback_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.head = AsyncMock(side_effect=head_side_effect)
        mock_client.get = AsyncMock(return_value=mock_wayback_resp)

        v = SourceValidator(http_client=mock_client)
        result = await v.validate_report(bad_report)

        assert result.overall_status == "fail"
        # wikipedia + nytimes should both fail domain check
        assert result.failed >= 2

    @pytest.mark.asyncio
    async def test_stale_source_is_warned(self):
        """Approved domain + stale date → status = 'warn'."""
        report = {
            "query": "test",
            "date": "2024-01-01",
            "sources": [
                {
                    "url": "https://archives.gov/research/foo",
                    "date": "1990-06-01",
                    "claim": "Old declassified cable",
                }
            ],
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.head = AsyncMock(return_value=mock_resp)

        v = SourceValidator(http_client=mock_client)
        result = await v.validate_report(report)

        assert result.total_sources == 1
        detail = result.details[0]
        assert detail.is_approved is True
        assert detail.freshness == "stale"
        assert detail.status == "warn"

    @pytest.mark.asyncio
    async def test_empty_sources_list(self, validator):
        """Report with no sources produces an empty pass result."""
        result = await validator.validate_report({"query": "test", "sources": []})
        assert result.total_sources == 0
        assert result.overall_status == "pass"

    @pytest.mark.asyncio
    async def test_string_source_urls(self):
        """Sources as plain URL strings (no dict) are handled."""
        report = {
            "query": "test",
            "date": "2024-01-01",
            "sources": ["https://data.worldbank.org/indicator/NY.GDP.MKTP.CD"],
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.head = AsyncMock(return_value=mock_resp)

        v = SourceValidator(http_client=mock_client)
        result = await v.validate_report(report)
        assert result.total_sources == 1
        assert result.details[0].is_approved is True
