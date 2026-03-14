"""Tests for BiasDetector — groundtruth.verification.bias_detector."""

from __future__ import annotations

import pytest

from groundtruth.verification.bias_detector import BiasDetector, BiasResult


@pytest.fixture()
def detector() -> BiasDetector:
    return BiasDetector()


def _make_report(**kwargs) -> dict:
    """Build a minimal report dict for testing."""
    defaults = {
        "summary": "The country has a stable government.",
        "background": "Historical context of the region.",
        "economic_context": "Economic growth has been moderate.",
        "military_context": "Defence spending is average.",
        "current_assessment": "The situation reportedly remains stable according to some analysts.",
        "confidence_notes": "Sources may be incomplete.",
        "perspectives": [
            {"framework": "Realist", "argument": "Power dynamics drive policy.", "evidence": "Troop movements"},
            {"framework": "Liberal", "argument": "Institutions matter.", "evidence": "Treaty participation"},
        ],
        "timeline": [
            {"year": 1990, "event": "End of Cold War", "source": "historian"},
            {"year": 2003, "event": "Major conflict began", "source": "ACLED"},
        ],
        "sources_cited": ["World Bank", "CIA Factbook"],
    }
    defaults.update(kwargs)
    return defaults


class TestBiasDetectorPass:
    def test_clean_report_passes(self, detector):
        report = _make_report()
        result = detector.analyze(report)
        assert isinstance(result, BiasResult)
        assert result.overall_status == "pass"
        assert result.score < 0.20

    def test_result_has_expected_fields(self, detector):
        result = detector.analyze(_make_report())
        assert hasattr(result, "overall_status")
        assert hasattr(result, "flags")
        assert hasattr(result, "score")
        assert 0.0 <= result.score <= 1.0

    def test_as_dict_shape(self, detector):
        d = detector.analyze(_make_report()).as_dict()
        assert "overall_status" in d
        assert "flags" in d
        assert "score" in d


class TestBiasDetectorHighBias:
    def test_high_bias_term_fails(self, detector):
        report = _make_report(summary="The terrorist state regime is an axis of evil.")
        result = detector.analyze(report)
        assert result.overall_status in ("warn", "fail")
        assert result.score >= 0.35
        assert any("loaded language" in f.lower() for f in result.flags)

    def test_freedom_fighters_flagged(self, detector):
        report = _make_report(background="The freedom fighters liberated the city.")
        result = detector.analyze(report)
        assert result.overall_status in ("warn", "fail")

    def test_expanded_geopolitical_terms_flagged(self, detector):
        report = _make_report(
            summary="The so-called expansionist strongman leads a rogue nation."
        )
        result = detector.analyze(report)
        assert result.overall_status in ("warn", "fail")
        assert result.score >= 0.35


class TestBiasDetectorSourceImbalance:
    def test_single_perspective_warns(self, detector):
        report = _make_report(perspectives=[
            {"framework": "Realist", "argument": "Power rules.", "evidence": "Data."}
        ])
        result = detector.analyze(report)
        assert result.overall_status in ("warn", "fail")
        assert any("perspective" in f.lower() for f in result.flags)

    def test_no_perspectives_warns(self, detector):
        report = _make_report(perspectives=[])
        result = detector.analyze(report)
        assert result.overall_status in ("warn", "fail")


class TestBiasDetectorHedgeRatio:
    def test_low_hedge_ratio_warns_on_long_report(self, detector):
        # Long report with absolutely no hedging language anywhere
        long_text = "The government controls all resources. " * 60
        report = _make_report(
            summary=long_text,
            background=long_text,
            economic_context="Growth is strong.",
            military_context="Spending is high.",
            current_assessment="The situation is exactly as described.",
            confidence_notes="",  # override fixture default which has "may be"
            perspectives=[
                {"framework": "A", "argument": "A", "evidence": "A"},
                {"framework": "B", "argument": "B", "evidence": "B"},
            ],
        )
        result = detector.analyze(report)
        assert any("hedg" in f.lower() for f in result.flags)

    def test_short_report_not_penalised(self, detector):
        report = _make_report(summary="Short.", background="Brief background.")
        result = detector.analyze(report)
        # Short reports should not fail hedge check
        assert not any("hedg" in f.lower() for f in result.flags)


class TestBiasDetectorEnvelope:
    def test_accepts_full_context_envelope(self, detector):
        """Detector should unwrap report from a full API response envelope."""
        envelope = {"query": "ukraine", "report": _make_report()}
        result = detector.analyze(envelope)
        assert isinstance(result, BiasResult)

    def test_empty_report_does_not_crash(self, detector):
        result = detector.analyze({})
        assert isinstance(result, BiasResult)
