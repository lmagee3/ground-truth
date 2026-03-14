"""Verification Pipeline — Ground Truth QA Orchestrator.

Runs all verification checks against a context report in sequence:
  1. Source Validator  — authoritative domain + liveness check  [Sprint 1]
  2. Bias Detector     — language + framing analysis             [Sprint 4]
  3. Fact Checker      — date/stat/name cross-reference          [Sprint 4]

Usage::

    pipeline = VerificationPipeline()
    result = await pipeline.run(report_dict)
    print(result.overall_status)  # 'pass' | 'warn' | 'fail'
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from groundtruth.verification.bias_detector import BiasDetector, BiasResult
from groundtruth.verification.fact_checker import FactChecker, FactCheckResult
from groundtruth.verification.source_validator import SourceValidator, ValidationResult

try:
    import structlog

    log = structlog.get_logger(__name__)
except ImportError:  # pragma: no cover
    log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class PipelineResult:
    """Unified result from the full verification pipeline."""

    source_validation: ValidationResult
    bias_analysis: BiasResult
    fact_check: FactCheckResult
    overall_status: str = "pass"  # 'pass' | 'warn' | 'fail'
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Derive overall status from sub-pipeline results."""
        statuses = [
            self.source_validation.overall_status,
            self.bias_analysis.overall_status,
            self.fact_check.overall_status,
        ]

        if "fail" in statuses:
            self.overall_status = "fail"
        elif "warn" in statuses:
            self.overall_status = "warn"
        else:
            self.overall_status = "pass"

    @property
    def verification_summary(self) -> dict:
        """Machine-readable summary for the API ``verification_status`` field."""
        sv = self.source_validation
        return {
            "overall_status": self.overall_status,
            "source_validation": {
                "status": sv.overall_status,
                "total_sources": sv.total_sources,
                "passed": sv.passed,
                "warned": sv.warned,
                "failed": sv.failed,
            },
            "bias_analysis": self.bias_analysis.as_dict(),
            "fact_check": self.fact_check.as_dict(),
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class VerificationPipeline:
    """Orchestrates all verification checks for a Ground Truth context report.

    The pipeline is the single entry point the API uses before returning
    any generated context report.  Reports that fail are still returned but
    include a ``verification_status`` field so consumers know the quality level.
    """

    def __init__(
        self,
        source_validator: SourceValidator | None = None,
        bias_detector: BiasDetector | None = None,
        fact_checker: FactChecker | None = None,
    ) -> None:
        self.source_validator = source_validator or SourceValidator()
        self.bias_detector = bias_detector or BiasDetector()
        self.fact_checker = fact_checker or FactChecker()

    async def run(self, report: dict, depth: str = "standard") -> PipelineResult:
        """Run the full verification pipeline against a context report.

        Args:
            report: The context report dict.  Must contain a ``"sources"`` list.
            depth: The briefing depth used to generate the report (used by the
                   fact-checker citation hygiene check).

        Returns:
            A :class:`PipelineResult` with the outcome of all checks.
        """
        log.info("pipeline_start", query=report.get("query", "<unknown>"))

        # --- Stage 1: Source Validation ---
        source_result = await self.source_validator.validate_report(report)

        # --- Stage 2: Bias Detection ---
        bias_result = self.bias_detector.analyze(report)

        # --- Stage 3: Fact Checking ---
        fact_result = self.fact_checker.check(report, depth=depth)

        result = PipelineResult(
            source_validation=source_result,
            bias_analysis=bias_result,
            fact_check=fact_result,
        )

        log.info(
            "pipeline_complete",
            query=report.get("query", "<unknown>"),
            overall_status=result.overall_status,
        )
        return result
