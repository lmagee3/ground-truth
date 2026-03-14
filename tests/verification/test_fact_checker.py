"""Tests for FactChecker — groundtruth.verification.fact_checker."""

from __future__ import annotations

import pytest

from groundtruth.verification.fact_checker import FactChecker, FactCheckResult


@pytest.fixture()
def checker() -> FactChecker:
    return FactChecker()


def _make_report(**kwargs) -> dict:
    defaults = {
        "summary": "The nation has a population of 10 million people.",
        "background": "Historical context spanning decades.",
        "economic_context": "GDP growth has been moderate.",
        "military_context": "Defence spending increased slightly.",
        "current_assessment": "The situation remains stable.",
        "confidence_notes": "Based on available primary sources.",
        "perspectives": [
            {"framework": "Realist", "argument": "Balance of power matters.", "evidence": "Troop data"},
        ],
        "timeline": [
            {"year": 1990, "event": "Cold War ended", "source": "UN"},
            {"year": 2014, "event": "Conflict escalated", "source": "ACLED"},
        ],
        "sources_cited": ["World Bank", "CIA Factbook", "GDELT"],
    }
    defaults.update(kwargs)
    return defaults


class TestFactCheckerPass:
    def test_clean_report_passes(self, checker):
        result = checker.check(_make_report())
        assert isinstance(result, FactCheckResult)
        assert result.overall_status == "pass"
        assert result.issues == []

    def test_result_shape(self, checker):
        result = checker.check(_make_report())
        assert "overall_status" in result.as_dict()
        assert "issues" in result.as_dict()


class TestFactCheckerYears:
    def test_bad_year_too_low_fails(self, checker):
        report = _make_report(
            timeline=[{"year": 1600, "event": "Ancient event", "source": "historian"}]
        )
        result = checker.check(report)
        assert result.overall_status == "fail"
        assert any("year" in i.lower() for i in result.issues)

    def test_bad_year_too_high_fails(self, checker):
        report = _make_report(
            timeline=[{"year": 2099, "event": "Future event", "source": "oracle"}]
        )
        result = checker.check(report)
        assert result.overall_status == "fail"

    def test_missing_year_warns(self, checker):
        report = _make_report(
            timeline=[{"event": "Something happened", "source": "unknown"}]
        )
        result = checker.check(report)
        assert result.overall_status in ("warn", "fail")

    def test_nonnumeric_year_fails(self, checker):
        report = _make_report(
            timeline=[{"year": "circa 19th century", "event": "Some event", "source": "history"}]
        )
        result = checker.check(report)
        assert result.overall_status == "fail"

    def test_valid_years_pass(self, checker):
        report = _make_report(
            timeline=[
                {"year": 1945, "event": "WW2 ended", "source": "UN"},
                {"year": 2023, "event": "Recent event", "source": "ACLED"},
            ]
        )
        result = checker.check(report)
        assert result.overall_status == "pass"


class TestFactCheckerCitations:
    def test_empty_citations_standard_depth_fails(self, checker):
        report = _make_report(sources_cited=[])
        result = checker.check(report, depth="standard")
        assert result.overall_status == "fail"
        assert any("sources_cited" in i.lower() for i in result.issues)

    def test_empty_citations_brief_depth_passes(self, checker):
        report = _make_report(sources_cited=[])
        result = checker.check(report, depth="brief")
        assert result.overall_status == "pass"

    def test_present_citations_pass(self, checker):
        report = _make_report(sources_cited=["World Bank", "GDELT"])
        result = checker.check(report, depth="comprehensive")
        assert result.overall_status == "pass"


class TestFactCheckerEdgeCases:
    def test_empty_report_does_not_crash(self, checker):
        result = checker.check({})
        assert isinstance(result, FactCheckResult)

    def test_accepts_full_context_envelope(self, checker):
        envelope = {"query": "ukraine", "report": _make_report()}
        result = checker.check(envelope)
        assert isinstance(result, FactCheckResult)

    def test_empty_timeline_passes(self, checker):
        report = _make_report(timeline=[])
        result = checker.check(report)
        assert result.overall_status == "pass"

    def test_non_country_abbreviations_not_flagged(self, checker):
        report = _make_report(
            summary="UN observers met EU diplomats and UK officials on peacekeeping terms."
        )
        result = checker.check(report)
        assert not any("invalid iso" in issue.lower() for issue in result.issues)
