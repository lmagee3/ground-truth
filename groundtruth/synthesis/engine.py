"""AI synthesis engine for Ground Truth context reports."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None


PROMPT_TEMPLATE = """You are Ground Truth, a senior intelligence analyst producing a geopolitical
briefing on: "{query}"

YOUR PRIMARY JOB: Explain the GEOPOLITICAL SITUATION described in the query above. The data
below is SUPPORTING EVIDENCE — use it to back up your analysis, but the briefing must be
ABOUT THE QUERY TOPIC, not about the data itself.

WRONG: "The US current account balance has been in deficit..." (this describes data, not the conflict)
RIGHT: "US-Iran tensions trace to the 1953 CIA-backed coup that overthrew Prime Minister Mosaddegh..." (this explains the geopolitical situation)

RULES:
1. TRACE TO DEEPEST HISTORICAL ROOT. For US-Iran: 1953 Operation Ajax. Israel-Palestine: 1917
   Balfour Declaration. Ukraine-Russia: Soviet era. NEVER start at the most recent crisis.
2. You MUST use well-established historical facts to build the narrative. Mark facts not from
   the provided data as "[Historical context]". The data below supplements your analysis —
   it does not replace your knowledge of world history.
3. Present 3+ interpretive frameworks: realist/security, liberal/institutional, regional/local.
4. Cite data sources (World Bank, CIA Factbook, SIPRI, etc.) when using provided data.
5. Military briefing style: clear, direct, authoritative. No hedging, no "it is worth noting."
6. Timeline: minimum 8 entries spanning the full historical arc.
7. For bilateral queries, analyze BOTH sides and how the relationship evolved.

DEPTH: {depth}
- "brief": 5-8 timeline events, 3 paragraphs background, 2+ perspectives
- "standard": 10-18 timeline events, 5+ paragraphs background, 3+ perspectives
- "comprehensive": 18-30 timeline events, 8+ paragraphs, 4+ perspectives, sub-regional dynamics

SUPPORTING DATA (use as evidence, do NOT just describe this data):

CIA FACTBOOK PROFILE:
{factbook_data}

ECONOMIC INDICATORS (World Bank):
{worldbank_data}

RECENT EVENTS (GDELT):
{gdelt_events}

CONFLICT DATA (ACLED):
{acled_events}

MILITARY / ARMS DATA (SIPRI/FAS):
{military_data}

Return ONLY valid JSON (no markdown, no code fences):
{{
  "title": "Descriptive title about {query}",
  "summary": "2-4 sentence executive summary of the geopolitical situation",
  "background": "Multi-paragraph historical narrative from root cause to present day",
  "timeline": [{{"year": 1953, "event": "key geopolitical event", "source": "Historical context"}}],
  "economic_context": "How economics shaped this conflict/situation, using World Bank data",
  "military_context": "Military balance, arms flows, defense posture relevant to this situation",
  "perspectives": [{{"framework": "Realist/Security", "argument": "...", "evidence": "..."}}],
  "current_assessment": "Current situation and forward-looking analysis",
  "sources_cited": ["World Bank", "CIA Factbook", "SIPRI"],
  "confidence_notes": "Data gaps and reliability caveats"
}}
"""


@dataclass
class ContextEngine:
    provider: str = "ollama"

    def __post_init__(self) -> None:
        self.provider = (os.getenv("SYNTHESIS_PROVIDER") or self.provider or "ollama").lower()
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1")
        self.ollama_fallback_models = [
            model.strip()
            for model in os.getenv(
                "OLLAMA_FALLBACK_MODELS", "gemma3:12b,gemma2:9b,gemma:latest"
            ).split(",")
            if model.strip()
        ]
        self.ollama_timeout = float(os.getenv("OLLAMA_TIMEOUT", "300.0"))
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    async def generate_context(
        self,
        query: str,
        depth: str = "standard",
        country_data: dict[str, Any] | None = None,
        events: dict[str, list[dict[str, Any]]] | None = None,
        military_data: dict[str, Any] | None = None,
        sources_available: dict[str, Any] | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        country_data = country_data or {}
        events = events or {}
        military_data = military_data or {}
        sources_available = sources_available or {}

        prompt = self._build_prompt(query, depth, country_data, events, military_data)
        self._current_depth = depth  # Store for token limit scaling

        selected_provider = (provider or self.provider).lower()
        if "PYTEST_CURRENT_TEST" in os.environ and os.getenv("GT_ALLOW_NETWORK_IN_TESTS") != "1":
            if selected_provider == "anthropic":
                uses_default_impl = (
                    getattr(self._call_anthropic, "__func__", None) is ContextEngine._call_anthropic
                )
            else:
                uses_default_impl = (
                    getattr(self._call_ollama, "__func__", None) is ContextEngine._call_ollama
                )

            if uses_default_impl:
                return self._fallback_report(
                    query=query,
                    depth=depth,
                    country_data=country_data,
                    events=events,
                    military_data=military_data,
                    sources_available=sources_available,
                    llm_error="test_mode: llm call skipped",
                )

        llm_output: str | None = None
        llm_error: str | None = None
        if selected_provider == "anthropic":
            try:
                llm_output = await self._call_anthropic(prompt)
            except Exception as exc:  # noqa: BLE001
                llm_error = f"anthropic_error: {type(exc).__name__}: {exc}"
        else:
            try:
                llm_output = await self._call_ollama(prompt)
            except Exception as exc:  # noqa: BLE001
                llm_error = f"ollama_error: {type(exc).__name__}: {exc}"

        if llm_output:
            parsed = self._parse_llm_json(llm_output)
            if parsed:
                parsed["sources_available"] = sources_available
                parsed.setdefault("confidence_notes", "")
                parsed["confidence_notes"] = self._merge_confidence_notes(
                    parsed["confidence_notes"], sources_available, llm_error
                )
                return parsed

        return self._fallback_report(
            query=query,
            depth=depth,
            country_data=country_data,
            events=events,
            military_data=military_data,
            sources_available=sources_available,
            llm_error=llm_error,
        )

    async def generate_comparison(
        self,
        event_a: str,
        event_b: str,
        context_a: dict[str, Any],
        context_b: dict[str, Any],
        provider: str | None = None,
    ) -> dict[str, Any]:
        prompt = (
            "Compare the two geopolitical contexts below. Return strict JSON with keys "
            "parallels (list), differences (list), assessment (string).\n"
            f"EVENT_A: {event_a}\nCONTEXT_A: {json.dumps(context_a, default=str)}\n"
            f"EVENT_B: {event_b}\nCONTEXT_B: {json.dumps(context_b, default=str)}"
        )

        selected = (provider or self.provider).lower()
        try:
            if selected == "anthropic":
                raw = await self._call_anthropic(prompt)
            else:
                raw = await self._call_ollama(prompt)
            parsed = self._parse_llm_json(raw)
            if parsed:
                return parsed
        except Exception:  # noqa: BLE001
            pass

        return {
            "parallels": [
                "Both contexts show layered geopolitical drivers across economic and security domains."
            ],
            "differences": [
                f"{event_a} and {event_b} differ in tempo, actors, and immediate conflict dynamics."
            ],
            "assessment": "Comparison generated in fallback mode due AI provider unavailability.",
        }

    def _build_prompt(
        self,
        query: str,
        depth: str,
        country_data: dict[str, Any],
        events: dict[str, list[dict[str, Any]]],
        military_data: dict[str, Any],
    ) -> str:
        return PROMPT_TEMPLATE.format(
            query=query,
            depth=depth,
            factbook_data=self._summarize_factbook(country_data.get("factbook", {})),
            worldbank_data=self._summarize_worldbank(country_data.get("worldbank", {})),
            gdelt_events=self._summarize_events(events.get("gdelt", []), "GDELT", max_items=10),
            acled_events=self._summarize_events(events.get("acled", []), "ACLED", max_items=10),
            military_data=self._summarize_military(military_data),
        )

    def _summarize_factbook(self, factbook: dict[str, Any]) -> str:
        """Compress CIA Factbook data into key facts the model can use."""
        if not factbook:
            return "No CIA Factbook data available."

        lines: list[str] = []

        # Government section — most relevant for geopolitical context
        gov = factbook.get("government", {})
        if gov:
            if isinstance(gov, dict):
                for key in (
                    "government_type",
                    "chief_of_state",
                    "capital",
                    "independence",
                    "legal_system",
                    "international_law",
                    "suffrage",
                ):
                    val = gov.get(key)
                    if val:
                        lines.append(f"Government - {key}: {self._truncate(str(val), 200)}")
            else:
                lines.append(f"Government: {self._truncate(str(gov), 300)}")

        # Military section
        mil = factbook.get("military", {})
        if mil:
            if isinstance(mil, dict):
                for key in (
                    "military_branches",
                    "military_service_age",
                    "military_expenditures_percent_gdp",
                ):
                    val = mil.get(key)
                    if val:
                        lines.append(f"Military - {key}: {self._truncate(str(val), 200)}")
            else:
                lines.append(f"Military: {self._truncate(str(mil), 300)}")

        # Transnational issues — often the most relevant for conflict queries
        trans = factbook.get("transnational_issues", {})
        if trans:
            lines.append(f"Transnational issues: {self._truncate(str(trans), 400)}")

        # International orgs
        orgs = factbook.get("international_orgs", [])
        if orgs:
            org_str = ", ".join(str(o) for o in orgs[:20]) if isinstance(orgs, list) else str(orgs)
            lines.append(f"International organizations: {self._truncate(org_str, 300)}")

        # Economy summary (brief)
        econ = factbook.get("economy", {})
        if econ:
            if isinstance(econ, dict):
                for key in ("gdp_purchasing_power_parity", "economic_overview", "inflation_rate"):
                    val = econ.get(key)
                    if val:
                        lines.append(f"Economy - {key}: {self._truncate(str(val), 200)}")
            else:
                lines.append(f"Economy: {self._truncate(str(econ), 300)}")

        # Demographics (brief)
        demo = factbook.get("demographics", {})
        if demo:
            if isinstance(demo, dict):
                for key in ("population", "ethnic_groups", "religions"):
                    val = demo.get(key)
                    if val:
                        lines.append(f"Demographics - {key}: {self._truncate(str(val), 150)}")

        # Check for secondary country data (prefixed with country name)
        for key, val in factbook.items():
            if "_government" in key or "_military" in key or "_transnational" in key:
                country_prefix = key.split("_")[0]
                lines.append(f"[{country_prefix}] {key}: {self._truncate(str(val), 300)}")

        if not lines:
            return "CIA Factbook data present but no key fields extracted."

        return "\n".join(lines)

    def _summarize_worldbank(self, worldbank: dict[str, Any]) -> str:
        """Compress World Bank indicators into trend summaries instead of raw data points."""
        if not worldbank:
            return "No World Bank data available."

        lines: list[str] = []
        for indicator_id, points in worldbank.items():
            if not points:
                continue

            # Get the indicator values — handle both dict and list formats
            values: list[tuple[int, float]] = []
            if isinstance(points, list):
                for p in points:
                    if isinstance(p, dict):
                        year = p.get("year")
                        val = p.get("value")
                        if year and val is not None:
                            values.append((int(year), float(val)))

            if not values:
                continue

            values.sort(key=lambda x: x[0])

            # Extract key trend points: first, last, min, max
            first_year, first_val = values[0]
            last_year, last_val = values[-1]
            min_pair = min(values, key=lambda x: x[1])
            max_pair = max(values, key=lambda x: x[1])

            # Calculate trend direction
            if len(values) >= 2:
                change = last_val - first_val
                pct = (change / abs(first_val) * 100) if first_val != 0 else 0
                direction = "increased" if change > 0 else "decreased"
                line = (
                    f"{indicator_id}: {direction} from {first_val:,.1f} ({first_year}) "
                    f"to {last_val:,.1f} ({last_year}) [{pct:+.1f}%]. "
                    f"Range: {min_pair[1]:,.1f} ({min_pair[0]}) to {max_pair[1]:,.1f} ({max_pair[0]}). "
                    f"({len(values)} data points)"
                )
            else:
                line = f"{indicator_id}: {first_val:,.1f} ({first_year})"

            lines.append(line)

        if not lines:
            return "World Bank indicators present but no values extracted."

        return "\n".join(lines)

    def _summarize_events(
        self, events: list[dict[str, Any]], source: str, max_items: int = 10
    ) -> str:
        """Compress event lists into concise summaries."""
        if not events:
            return f"No {source} events available."

        lines: list[str] = []
        for ev in events[:max_items]:
            date = ev.get("date", "unknown date")
            desc = self._truncate(ev.get("description", "No description"), 150)
            event_type = ev.get("event_type", "")
            actors = ev.get("actors", [])
            actor_str = f" Actors: {', '.join(str(a) for a in actors[:3])}" if actors else ""
            lines.append(f"[{date}] ({event_type}) {desc}{actor_str}")

        total = len(events)
        if total > max_items:
            lines.append(f"... and {total - max_items} more {source} events")

        return "\n".join(lines)

    def _summarize_military(self, military_data: dict[str, Any]) -> str:
        """Compress SIPRI + FAS data into readable summaries."""
        if not military_data:
            return "No military data available."

        lines: list[str] = []

        # SIPRI military expenditure
        sipri = military_data.get("sipri", {})
        mil_exp = sipri.get("military_expenditure", [])
        if mil_exp:
            # Group by country if available
            by_country: dict[str, list[tuple[int, float]]] = {}
            for record in mil_exp:
                if isinstance(record, dict):
                    country = record.get("country", "Unknown")
                    year = record.get("year")
                    val = record.get("value") or record.get("expenditure")
                    if year and val is not None:
                        by_country.setdefault(country, []).append((int(year), float(val)))

            for country, data in by_country.items():
                data.sort(key=lambda x: x[0])
                if len(data) >= 2:
                    first = data[0]
                    last = data[-1]
                    lines.append(
                        f"SIPRI Military Spending ({country}): "
                        f"${first[1]:,.1f}B ({first[0]}) -> ${last[1]:,.1f}B ({last[0]})"
                    )
                elif data:
                    lines.append(
                        f"SIPRI Military Spending ({country}): ${data[0][1]:,.1f}B ({data[0][0]})"
                    )

        # SIPRI arms transfers
        arms = sipri.get("arms_transfers", [])
        if arms:
            lines.append(f"SIPRI Arms Transfers: {len(arms)} records")
            for record in arms[:5]:
                if isinstance(record, dict):
                    year = record.get("year", "?")
                    supplier = record.get("supplier", "?")
                    recipient = record.get("recipient", "?")
                    val = record.get("value") or record.get("tiv", "?")
                    lines.append(f"  [{year}] {supplier} -> {recipient}: TIV {val}")

        # FAS nuclear data
        fas = military_data.get("fas")
        if fas:
            if isinstance(fas, list):
                for entry in fas:
                    if isinstance(entry, dict):
                        country = entry.get("country", "Unknown")
                        warheads = entry.get("total_warheads") or entry.get("warheads", "?")
                        lines.append(f"FAS Nuclear ({country}): {warheads} warheads")
            elif isinstance(fas, dict):
                country = fas.get("country", "Unknown")
                warheads = fas.get("total_warheads") or fas.get("warheads", "?")
                lines.append(f"FAS Nuclear ({country}): {warheads} warheads")

        if not lines:
            return "Military data present but no records extracted."

        return "\n".join(lines)

    @staticmethod
    def _truncate(text: str, max_len: int = 200) -> str:
        """Truncate text to max length."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def _max_tokens_for_depth(self) -> int:
        """Scale output tokens based on requested depth. All depths get generous limits
        because even 'brief' produces historically grounded analysis."""
        depth = getattr(self, "_current_depth", "standard")
        if depth == "brief":
            return 4096
        elif depth == "comprehensive":
            return 16384
        return 8192  # standard — enough for full historical deep dive

    async def _call_ollama(self, prompt: str) -> str:
        max_tokens = self._max_tokens_for_depth()
        model_candidates = [self.ollama_model, *self.ollama_fallback_models]
        tried: set[str] = set()
        errors: list[str] = []
        timeout = httpx.Timeout(10.0, read=self.ollama_timeout)

        async with httpx.AsyncClient(timeout=timeout) as client:
            for model in model_candidates:
                if model in tried:
                    continue
                tried.add(model)

                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": max_tokens},
                }
                try:
                    response = await client.post(
                        f"{self.ollama_base_url}/api/generate", json=payload
                    )
                    response.raise_for_status()
                    body = response.json()

                    if body.get("error"):
                        raise RuntimeError(str(body["error"]))

                    result = str(body.get("response", ""))
                    if not result.strip():
                        raise RuntimeError(f"Ollama returned empty response for model {model}")

                    return result
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{model}: {type(exc).__name__}: {exc}")

        raise RuntimeError(f"Ollama failed for all candidate models: {' | '.join(errors)}")

    async def _call_anthropic(self, prompt: str) -> str:
        if not self.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        if anthropic is None:
            raise RuntimeError("anthropic package is not installed")

        max_tokens = self._max_tokens_for_depth()
        client = anthropic.AsyncAnthropic(api_key=self.anthropic_api_key)
        response = await client.messages.create(
            model=self.anthropic_model,
            max_tokens=max_tokens,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )

        parts = getattr(response, "content", [])
        text_parts: list[str] = []
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)

    def _parse_llm_json(self, raw: str) -> dict[str, Any] | None:
        candidate = raw.strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        try:
            parsed = json.loads(candidate[start : end + 1])
        except json.JSONDecodeError:
            return None

        return parsed if isinstance(parsed, dict) else None

    def _merge_confidence_notes(
        self,
        existing: str,
        sources_available: dict[str, Any],
        llm_error: str | None,
    ) -> str:
        skipped = [
            name for name, details in sources_available.items() if details.get("status") != "used"
        ]
        pieces = [existing.strip()] if existing else []
        if skipped:
            pieces.append(f"Sources skipped/unavailable: {', '.join(skipped)}")
        if llm_error:
            pieces.append(llm_error)
        return " | ".join(piece for piece in pieces if piece)

    def _fallback_report(
        self,
        query: str,
        depth: str,
        country_data: dict[str, Any],
        events: dict[str, list[dict[str, Any]]],
        military_data: dict[str, Any],
        sources_available: dict[str, Any],
        llm_error: str | None,
    ) -> dict[str, Any]:
        country_name = country_data.get("country", {}).get("name") or query
        wb_count = sum(len(v) for v in country_data.get("worldbank", {}).values())
        gdelt_count = len(events.get("gdelt", []))
        acled_count = len(events.get("acled", []))

        timeline: list[dict[str, Any]] = []
        for event in events.get("gdelt", [])[:3]:
            timeline.append(
                {
                    "year": self._year_from_iso(event.get("date")),
                    "event": event.get("description", ""),
                    "source": "GDELT",
                }
            )
        for event in events.get("acled", [])[:2]:
            timeline.append(
                {
                    "year": self._year_from_iso(event.get("date")),
                    "event": event.get("description", ""),
                    "source": "ACLED",
                }
            )

        sources_cited = [
            "World Bank",
            "CIA Factbook",
        ]
        if gdelt_count:
            sources_cited.append("GDELT")
        if acled_count:
            sources_cited.append("ACLED")
        if military_data.get("sipri"):
            sources_cited.append("SIPRI")
        if military_data.get("fas"):
            sources_cited.append("FAS")

        return {
            "title": f"Ground Truth Briefing: {query}",
            "summary": (
                f"{country_name} context generated in fallback mode using available datasets. "
                f"Depth={depth}; economic points={wb_count}; recent events={gdelt_count + acled_count}."
            ),
            "background": f"Background synthesized from CIA Factbook and historical indicators for {country_name}.",
            "timeline": timeline,
            "economic_context": f"World Bank indicators available: {wb_count} records.",
            "military_context": (
                "Military context includes "
                f"SIPRI records={len(military_data.get('sipri', {}).get('military_expenditure', []))} and "
                f"FAS nuclear data={'yes' if military_data.get('fas') else 'no'}."
            ),
            "perspectives": [
                {
                    "framework": "State security",
                    "argument": "Actors prioritize territorial control and deterrence posture.",
                    "evidence": "[CIA Factbook] [GDELT]",
                },
                {
                    "framework": "Political economy",
                    "argument": "Economic constraints and trade exposure shape escalation paths.",
                    "evidence": "[World Bank] [SIPRI]",
                },
            ],
            "current_assessment": "Situation remains fluid; monitor event tempo and economic stress indicators.",
            "sources_cited": sources_cited,
            "confidence_notes": self._merge_confidence_notes(
                "Generated by deterministic fallback synthesis.", sources_available, llm_error
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources_available": sources_available,
        }

    def _year_from_iso(self, value: Any) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and len(value) >= 4 and value[:4].isdigit():
            return int(value[:4])
        return datetime.now(timezone.utc).year
