"""Verification Pipeline — Ground Truth QA Orchestrator.

Runs all verification checks against a context report in sequence:
  1. Source Validator  — authoritative domain + liveness check  [Sprint 1]
  2. Bias Detector     — language + framing analysis             [Sprint 2]
  3. Fact Checker      — date/stat/name cross-reference          [Sprint 2]

Usage::

    pipeline = VerificationPipeline()
    result = await pipeline.run(report_dict)
    print(result.overall_status)  # 'pass' | 'warn' | 'fail'
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

from groundtruth.verification.source_validator import SourceValidator, ValidationResult

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PipelineResult:
    """Unified result from the full verification pipeline."""

    source_validation: ValidationResult
    # bias_analysis: BiasResult | None = None     # Sprint 2
    # fact_check: FactCheckResult | None = None   # Sprint 2
    overall_status: str = "pass"  # 'pass' | 'warn' | 'fail'
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Derive overall status from sub-pipeline results."""
        statuses = [self.source_validation.overall_status]
        # statuses.append(self.bias_analysis.overall_status)  # Sprint 2
        # statuses.append(self.fact_check.overall_status)     # Sprint 2

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
            # "bias_analysis": ...,   # Sprint 2
            # "fact_check": ...,      # Sprint 2
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

    Sprint 1 — Source Validator only.
    Sprint 2 — Bias Detector + Fact Checker will be added here.
    """

    def __init__(self, source_validator: SourceValidator | None = None) -> None:
        self.source_validator = source_validator or SourceValidator()

    async def run(self, report: dict) -> PipelineResult:
        """Run the full verification pipeline against a context report.

        Args:
            report: The context report dict.  Must contain a ``"sources"`` list.

        Returns:
            A :class:`PipelineResult` with the outcome of all checks.
        """
        log.info("pipeline_start", query=report.get("query", "<unknown>"))

        # --- Stage 1: Source Validation ---
        source_result = await self.source_validator.validate_report(report)

        # --- Stage 2: Bias Detection (Sprint 2) ---
        # bias_result = await self.bias_detector.analyze(report)

        # --- Stage 3: Fact Checking (Sprint 2) ---
        # fact_result = await self.fact_checker.check(report)

        result = PipelineResult(
            source_validation=source_result,
        )

        log.info(
            "pipeline_complete",
            query=report.get("query", "<unknown>"),
            overall_status=result.overall_status,
        )
        return result
