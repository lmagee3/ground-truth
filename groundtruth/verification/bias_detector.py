"""Bias Detector — Ground Truth Verification Stage 2.

Rule-based (no LLM) language and framing analysis for synthesised context reports.
Fast, deterministic, and fully testable without network access.

Three checks:
  1. Loaded Language  — flags politically charged / one-sided vocabulary
  2. Source Imbalance — warns when only one perspective appears in citations
  3. Hedge Ratio      — warns on over-confident prose (no hedging language)

Usage::

    detector = BiasDetector()
    result = detector.analyze(report_dict)
    print(result.overall_status)   # 'pass' | 'warn' | 'fail'
    print(result.flags)            # list of human-readable flag messages
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

try:
    import structlog

    log = structlog.get_logger(__name__)
except ImportError:  # pragma: no cover
    log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Word lists
# ---------------------------------------------------------------------------

# Terms that signal one-sided framing when used without counterbalancing context.
# Split into "high" (fail-level) and "medium" (warn-level) buckets.
_HIGH_BIAS_TERMS: frozenset[str] = frozenset(
    {
        # Dehumanising / absolute enemy framing
        "terrorist state",
        "axis of evil",
        "rogue state",
        "rogue nation",
        "puppet regime",
        "illegal occupation",
        "genocide",  # only flagged; not necessarily wrong — context matters
        "ethnic cleansing",
        # Uncritical heroising
        "freedom fighters",
        "liberation army",
        "democratic saviors",
    }
)

_MEDIUM_BIAS_TERMS: frozenset[str] = frozenset(
    {
        "regime",
        "terrorist",
        "terrorists",
        "juntas",
        "junta",
        "dictator",
        "tyrant",
        "oppressor",
        "puppet",
        "propaganda",
        "indoctrination",
        "warlord",
        "extremist",
        "radical",
        "fanatic",
        "invader",
        "occupier",
        "strongman",
        "so-called",
        "illegitimate",
        "expansionist",
    }
)

# Hedging patterns — presence of these reduces the over-confidence flag.
_HEDGE_PATTERNS: list[str] = [
    r"\ballegedly?\b",
    r"\breportedly?\b",
    r"\baccording to\b",
    r"\bsuggests?\b",
    r"\bappears? to\b",
    r"\bmay\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\bunclear\b",
    r"\buncertain\b",
    r"\bdisputed?\b",
    r"\bcontested?\b",
    r"\bsome analysts?\b",
    r"\bsome sources?\b",
    r"\bit is (possible|likely|believed)\b",
]

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class BiasResult:
    """Result from the bias detection stage."""

    overall_status: str  # 'pass' | 'warn' | 'fail'
    flags: list[str] = field(default_factory=list)
    score: float = 0.0  # 0.0–1.0, higher = more biased

    def as_dict(self) -> dict:
        return {
            "overall_status": self.overall_status,
            "flags": self.flags,
            "score": round(self.score, 3),
        }


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class BiasDetector:
    """Analyse a synthesised context report for language and framing bias."""

    # Proportion of words that must match medium-bias terms before it warns
    _MEDIUM_DENSITY_WARN_THRESHOLD = 0.008   # ~0.8% of all words
    _MEDIUM_DENSITY_FAIL_THRESHOLD = 0.020   # ~2.0% of all words

    # Minimum hedge-pattern hits per 1000 words before flagging over-confidence
    _HEDGE_RATIO_WARN_THRESHOLD = 0.5   # hits per 1000 words

    def analyze(self, report: dict) -> BiasResult:
        """Run all bias checks against a context report dict.

        Args:
            report: The ``report`` sub-dict from a context response (or the
                    full context response — both are handled).

        Returns:
            :class:`BiasResult` with status, flags, and bias score.
        """
        # Accept either the full context envelope or just the inner report dict
        inner = report.get("report", report)

        full_text = self._extract_text(inner)
        flags: list[str] = []
        score = 0.0

        # --- Check 1: Loaded language ---
        high_hits = self._find_terms(full_text, _HIGH_BIAS_TERMS)
        medium_hits = self._find_terms(full_text, _MEDIUM_BIAS_TERMS)

        if high_hits:
            flags.append(
                f"High-bias loaded language detected: {', '.join(sorted(high_hits))}"
            )
            score = max(score, 0.75)

        word_count = max(len(full_text.split()), 1)
        medium_density = len(medium_hits) / word_count
        if medium_density >= self._MEDIUM_DENSITY_FAIL_THRESHOLD:
            flags.append(
                f"Excessive loaded language density ({medium_density:.1%}): "
                f"{', '.join(sorted(medium_hits))}"
            )
            score = max(score, 0.65)
        elif medium_density >= self._MEDIUM_DENSITY_WARN_THRESHOLD and medium_hits:
            flags.append(
                f"Elevated loaded language: {', '.join(sorted(medium_hits))}"
            )
            score = max(score, 0.35)

        # --- Check 2: Source imbalance ---
        perspectives = inner.get("perspectives", [])
        if isinstance(perspectives, list) and len(perspectives) == 1:
            flags.append(
                "Only one analytical perspective present — consider adding counter-narratives"
            )
            score = max(score, 0.30)
        elif isinstance(perspectives, list) and len(perspectives) == 0:
            flags.append("No analytical perspectives section found in report")
            score = max(score, 0.20)

        # --- Check 3: Hedge ratio (over-confidence) ---
        hedge_hits = self._count_hedge_patterns(full_text)
        hedge_ratio = (hedge_hits / word_count) * 1000  # per 1000 words
        if word_count > 200 and hedge_ratio < self._HEDGE_RATIO_WARN_THRESHOLD:
            flags.append(
                f"Low hedging language ratio ({hedge_ratio:.2f} per 1000 words) — "
                "report may overstate certainty"
            )
            score = max(score, 0.25)

        # --- Derive status ---
        if score >= 0.65 or (high_hits and score >= 0.50):
            status = "fail"
        elif score >= 0.20 or flags:
            status = "warn"
        else:
            status = "pass"

        result = BiasResult(overall_status=status, flags=flags, score=score)
        log.info(
            "bias_detection_complete",
            status=status,
            score=round(score, 3),
            flag_count=len(flags),
        )
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(report: dict) -> str:
        """Concatenate all string fields in the report into a single corpus."""
        text_parts: list[str] = []
        text_fields = (
            "summary",
            "background",
            "economic_context",
            "military_context",
            "current_assessment",
            "confidence_notes",
        )
        for field_name in text_fields:
            val = report.get(field_name, "")
            if isinstance(val, str):
                text_parts.append(val)

        for event in report.get("timeline", []):
            if isinstance(event, dict):
                text_parts.append(str(event.get("event", "")))

        for perspective in report.get("perspectives", []):
            if isinstance(perspective, dict):
                text_parts.append(str(perspective.get("argument", "")))
                text_parts.append(str(perspective.get("evidence", "")))

        return " ".join(text_parts).lower()

    @staticmethod
    def _find_terms(text: str, terms: frozenset[str]) -> set[str]:
        """Return which terms from the set appear in the text."""
        return {term for term in terms if term in text}

    @staticmethod
    def _count_hedge_patterns(text: str) -> int:
        """Count total hedge-pattern occurrences in the text."""
        return sum(
            len(re.findall(pattern, text, re.IGNORECASE))
            for pattern in _HEDGE_PATTERNS
        )
