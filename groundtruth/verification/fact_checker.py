"""Fact Checker — Ground Truth Verification Stage 3.

Cross-references factual claims in a synthesised report against known-good data.
Rule-based and deterministic — no LLM calls.

Checks:
  1. Year sanity     — timeline event years must be in a plausible range
  2. ISO validation  — 2-letter country codes cited must be real ISO 3166-1 alpha-2
  3. Citation hygiene — sources_cited must be non-empty for depth != 'brief'
  4. Numeric plausibility — population/GDP figures must be in a sane order of magnitude

Usage::

    checker = FactChecker()
    result = checker.check(report_dict)
    print(result.overall_status)   # 'pass' | 'warn' | 'fail'
    print(result.issues)           # list of human-readable issue messages
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
# Known-good data sets
# ---------------------------------------------------------------------------

#: All valid ISO 3166-1 alpha-2 codes (UN member states + common territories).
_VALID_ISO2: frozenset[str] = frozenset(
    {
        "AF", "AX", "AL", "DZ", "AS", "AD", "AO", "AI", "AQ", "AG", "AR", "AM",
        "AW", "AU", "AT", "AZ", "BS", "BH", "BD", "BB", "BY", "BE", "BZ", "BJ",
        "BM", "BT", "BO", "BQ", "BA", "BW", "BV", "BR", "IO", "BN", "BG", "BF",
        "BI", "CV", "KH", "CM", "CA", "KY", "CF", "TD", "CL", "CN", "CX", "CC",
        "CO", "KM", "CG", "CD", "CK", "CR", "CI", "HR", "CU", "CW", "CY", "CZ",
        "DK", "DJ", "DM", "DO", "EC", "EG", "SV", "GQ", "ER", "EE", "SZ", "ET",
        "FK", "FO", "FJ", "FI", "FR", "GF", "PF", "TF", "GA", "GM", "GE", "DE",
        "GH", "GI", "GR", "GL", "GD", "GP", "GU", "GT", "GG", "GN", "GW", "GY",
        "HT", "HM", "VA", "HN", "HK", "HU", "IS", "IN", "ID", "IR", "IQ", "IE",
        "IM", "IL", "IT", "JM", "JP", "JE", "JO", "KZ", "KE", "KI", "KP", "KR",
        "KW", "KG", "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MO",
        "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MQ", "MR", "MU", "YT", "MX",
        "FM", "MD", "MC", "MN", "ME", "MS", "MA", "MZ", "MM", "NA", "NR", "NP",
        "NL", "NC", "NZ", "NI", "NE", "NG", "NU", "NF", "MK", "MP", "NO", "OM",
        "PK", "PW", "PS", "PA", "PG", "PY", "PE", "PH", "PN", "PL", "PT", "PR",
        "QA", "RE", "RO", "RU", "RW", "BL", "SH", "KN", "LC", "MF", "PM", "VC",
        "WS", "SM", "ST", "SA", "SN", "RS", "SC", "SL", "SG", "SX", "SK", "SI",
        "SB", "SO", "ZA", "GS", "SS", "ES", "LK", "SD", "SR", "SJ", "SE", "CH",
        "SY", "TW", "TJ", "TZ", "TH", "TL", "TG", "TK", "TO", "TT", "TN", "TR",
        "TM", "TC", "TV", "UG", "UA", "AE", "GB", "UM", "US", "UY", "UZ", "VU",
        "VE", "VN", "VG", "VI", "WF", "EH", "YE", "ZM", "ZW",
        # Common non-standard but widely used codes
        "XK",  # Kosovo
    }
)

#: Plausible year range for geopolitical events cited in a briefing.
_MIN_YEAR = 1800
_MAX_YEAR = 2030

#: World population bounds for sanity-checking any figure labelled as population.
_POP_MIN = 800          # smallest inhabited island nation (Nauru ~10k, but allow low)
_POP_MAX = 1_500_000_000  # China ~1.4B

#: GDP (USD) plausible range — Nauru ~130M, US ~27T.
_GDP_MIN = 1_000_000       # $1M — allows very small territories
_GDP_MAX = 50_000_000_000_000  # $50T ceiling

# Abbreviations frequently used in prose that should not be treated as invalid ISO tokens.
NON_COUNTRY_ABBREVIATIONS: frozenset[str] = frozenset(
    {"UN", "EU", "AI", "UK", "US", "FM", "AM", "PM", "TV", "IT", "HR", "PR"}
)

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class FactCheckResult:
    """Result from the fact-checking stage."""

    overall_status: str  # 'pass' | 'warn' | 'fail'
    issues: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "overall_status": self.overall_status,
            "issues": self.issues,
        }


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------


class FactChecker:
    """Cross-reference factual claims in a context report against known-good data."""

    def check(self, report: dict, depth: str = "standard") -> FactCheckResult:
        """Run all fact checks against a context report dict.

        Args:
            report: The ``report`` sub-dict from a context response, OR the full
                    context envelope (both forms accepted).
            depth: The briefing depth used to generate this report.  Used to
                   calibrate the citation-hygiene check.

        Returns:
            :class:`FactCheckResult` with status and list of issues found.
        """
        inner = report.get("report", report)
        issues: list[str] = []

        # --- Check 1: Year sanity ---
        issues.extend(self._check_years(inner))

        # --- Check 2: ISO code validation ---
        issues.extend(self._check_iso_codes(inner))

        # --- Check 3: Citation hygiene ---
        issues.extend(self._check_citations(inner, depth))

        # --- Check 4: Numeric plausibility ---
        issues.extend(self._check_numeric_plausibility(inner))

        # --- Derive status ---
        fail_issues = [i for i in issues if i.startswith("[FAIL]")]
        warn_issues = [i for i in issues if i.startswith("[WARN]")]

        if fail_issues:
            status = "fail"
        elif warn_issues:
            status = "warn"
        else:
            status = "pass"

        # Strip prefixes for cleaner output
        clean_issues = [re.sub(r"^\[(FAIL|WARN)\] ", "", i) for i in issues]

        result = FactCheckResult(overall_status=status, issues=clean_issues)
        log.info(
            "fact_check_complete",
            status=status,
            issue_count=len(issues),
        )
        return result

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_years(self, report: dict) -> list[str]:
        """Validate years in the timeline section."""
        issues: list[str] = []
        for i, event in enumerate(report.get("timeline", [])):
            if not isinstance(event, dict):
                continue
            year = event.get("year")
            if year is None:
                issues.append(f"[WARN] Timeline event #{i+1} is missing a year field")
                continue
            try:
                year_int = int(year)
            except (ValueError, TypeError):
                issues.append(f"[FAIL] Timeline event #{i+1} has non-numeric year: {year!r}")
                continue
            if not (_MIN_YEAR <= year_int <= _MAX_YEAR):
                issues.append(
                    f"[FAIL] Timeline event #{i+1} year {year_int} is outside "
                    f"plausible range [{_MIN_YEAR}–{_MAX_YEAR}]"
                )
        return issues

    def _check_iso_codes(self, report: dict) -> list[str]:
        """Validate any 2-letter country-code-like tokens found in report text."""
        issues: list[str] = []
        text = self._extract_text(report)

        # Match tokens that look like ISO-2 codes: uppercase letter pairs surrounded by
        # word boundaries (but exclude common English words like "IS", "IN", "IT", etc.)
        _COMMON_ENGLISH = {"IS", "IN", "IT", "OR", "AN", "AS", "AT", "BY", "DO",
                           "GO", "HE", "IF", "ME", "MY", "NO", "OF", "OK", "ON",
                           "SO", "TO", "UP", "US", "WE"}

        candidate_tokens: set[str] = set(re.findall(r"\b([A-Z]{2})\b", text))
        candidate_tokens -= _COMMON_ENGLISH  # remove common English words
        candidate_tokens -= NON_COUNTRY_ABBREVIATIONS

        invalid = candidate_tokens - _VALID_ISO2
        if invalid:
            issues.append(
                f"[WARN] Unrecognised 2-letter tokens that may be invalid ISO codes: "
                f"{', '.join(sorted(invalid))}"
            )
        return issues

    @staticmethod
    def _check_citations(report: dict, depth: str) -> list[str]:
        """Ensure sources are cited for non-brief depth reports."""
        issues: list[str] = []
        sources_cited = report.get("sources_cited", [])

        if depth != "brief":
            if not isinstance(sources_cited, list) or len(sources_cited) == 0:
                issues.append(
                    f"[FAIL] Report at depth '{depth}' has no sources_cited — "
                    "synthesis likely did not reference primary sources"
                )
        return issues

    @staticmethod
    def _check_numeric_plausibility(report: dict) -> list[str]:
        """Scan text for numbers that could be population or GDP figures and range-check them."""
        issues: list[str] = []
        text = " ".join(
            [
                report.get("economic_context", ""),
                report.get("military_context", ""),
                report.get("summary", ""),
            ]
        )

        # Look for large numbers preceded by population-related keywords
        pop_pattern = re.compile(
            r"population\s+of\s+[\$\s]*([\d,]+(?:\.\d+)?)\s*(million|billion)?",
            re.IGNORECASE,
        )
        for match in pop_pattern.finditer(text):
            raw = float(match.group(1).replace(",", ""))
            multiplier = {"million": 1_000_000, "billion": 1_000_000_000}.get(
                (match.group(2) or "").lower(), 1
            )
            value = raw * multiplier
            if not (_POP_MIN <= value <= _POP_MAX):
                issues.append(
                    f"[WARN] Possibly implausible population figure: {raw:,.0f}"
                    f"{' ' + match.group(2) if match.group(2) else ''}"
                )

        # GDP plausibility
        gdp_pattern = re.compile(
            r"gdp\s+of\s+\$?([\d,]+(?:\.\d+)?)\s*(trillion|billion|million)?",
            re.IGNORECASE,
        )
        for match in gdp_pattern.finditer(text):
            raw = float(match.group(1).replace(",", ""))
            multiplier = {
                "trillion": 1_000_000_000_000,
                "billion": 1_000_000_000,
                "million": 1_000_000,
            }.get((match.group(2) or "").lower(), 1)
            value = raw * multiplier
            if not (_GDP_MIN <= value <= _GDP_MAX):
                issues.append(
                    f"[WARN] Possibly implausible GDP figure: ${raw:,.0f}"
                    f"{' ' + match.group(2) if match.group(2) else ''}"
                )
        return issues

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(report: dict) -> str:
        """Concatenate all string fields for pattern-matching checks."""
        parts: list[str] = []
        for field_name in ("summary", "background", "economic_context",
                           "military_context", "current_assessment"):
            val = report.get(field_name, "")
            if isinstance(val, str):
                parts.append(val)
        return " ".join(parts)
