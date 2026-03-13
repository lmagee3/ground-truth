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


PROMPT_TEMPLATE = """You are Ground Truth, a geopolitical context engine that produces intelligence
briefings explaining HOW and WHY geopolitical situations developed. You write like a senior
intelligence analyst producing a briefing for a policy maker — clear, deep, authoritative.

CRITICAL RULES:
1. TRACE HISTORICAL ROOTS TO THEIR DEEPEST ORIGIN. Do NOT start at the most recent crisis.
   - For US-Iran: begin with the 1953 CIA/MI6-backed coup (Operation Ajax) that overthrew Mosaddegh,
     then cover the Shah era, 1979 revolution, hostage crisis, Iran-Iraq war, nuclear program, JCPOA.
   - For Israel-Palestine: begin with the Balfour Declaration (1917), British Mandate, 1948 war.
   - For Ukraine-Russia: begin with Crimean history, Soviet era, 1991 independence, Orange Revolution.
   - For ANY topic: identify the earliest causal event and build forward chronologically.
2. Use the provided data as your PRIMARY evidence, but you may reference well-established
   historical facts (pre-2000) that provide essential context even if not in the dataset.
   Clearly mark any historical context not from the provided data as "[Historical context]".
3. Present MULTIPLE interpretive frameworks — do not pick sides. Include at minimum:
   realist/security, liberal/institutional, and regional/local perspectives.
4. Every claim from the provided data must cite its source (World Bank, CIA Factbook, GDELT, etc.).
5. Military briefing style: clear, direct, no editorial language, no hedging.
6. The timeline MUST span the full historical arc — include pre-2000 events that are essential
   to understanding the current situation. Aim for 8-15 timeline entries for "standard" depth.
7. For bilateral queries (e.g., "US-Iran", "India-Pakistan"), analyze BOTH countries' data
   and how their relationship evolved over time.

DEPTH GUIDANCE (ALL depths produce substantive analysis — there is no "shallow" mode):
- "brief": Concise but STILL historically grounded. 5-8 timeline events going back to the
  root cause. 3-5 paragraphs of background. 2+ perspectives. Never skip historical origins.
- "standard": Full deep-dive analysis. 10-18 timeline events spanning the ENTIRE historical arc.
  Detailed economic/military context. 3+ perspectives with evidence. 4-8 paragraphs of background
  covering every major turning point from origin to present day.
- "comprehensive": Maximum depth. 18-30 timeline events. Granular economic trends year-by-year.
  4+ perspectives with detailed evidence. Sub-regional dynamics, treaty/agreement history,
  leadership transitions, covert operations, proxy conflicts. 6-10 paragraphs of background.

IMPORTANT: Regardless of depth level, ALWAYS trace the full historical arc. A "brief" on Iran
still starts at 1953, it just covers fewer details. NEVER produce a timeline with fewer than
5 entries. NEVER start a background section later than the root cause event.

QUERY: {query}
DEPTH: {depth}

AVAILABLE DATA:
--- CIA FACTBOOK ---
{factbook_data}

--- WORLD BANK INDICATORS ---
{worldbank_data}

--- GDELT EVENTS (Recent) ---
{gdelt_events}

--- ACLED CONFLICT DATA ---
{acled_events}

--- MILITARY DATA (SIPRI/FAS) ---
{military_data}

Generate a JSON object with this exact schema (no markdown, no code fences, ONLY valid JSON):
{{
  "title": "descriptive title for the briefing",
  "summary": "2-4 sentence executive summary",
  "background": "3-6 paragraphs tracing the FULL historical arc from earliest relevant event to present",
  "timeline": [{{"year": 1953, "event": "description of key event", "source": "CIA Factbook or Historical context"}}],
  "economic_context": "economic analysis using World Bank data and historical trends",
  "military_context": "military balance, arms flows, defense posture using SIPRI/FAS data",
  "perspectives": [{{"framework": "Realist/Security", "argument": "the argument", "evidence": "supporting evidence"}}],
  "current_assessment": "current situation assessment with forward-looking analysis",
  "sources_cited": ["World Bank", "CIA Factbook", "SIPRI", "etc."],
  "confidence_notes": "data gaps, caveats, reliability assessment"
}}
"""


@dataclass
class ContextEngine:
    provider: str = "ollama"

    def __post_init__(self) -> None:
        self.provider = (os.getenv("SYNTHESIS_PROVIDER") or self.provider or "ollama").lower()
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1")
        self.ollama_timeout = float(os.getenv("OLLAMA_TIMEOUT", "120.0"))
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
        llm_output: str | None = None
        llm_error: str | None = None
        if selected_provider == "anthropic":
            try:
                llm_output = await self._call_anthropic(prompt)
            except Exception as exc:  # noqa: BLE001
                llm_error = f"anthropic_error: {exc}"
        else:
            try:
                llm_output = await self._call_ollama(prompt)
            except Exception as exc:  # noqa: BLE001
                llm_error = f"ollama_error: {exc}"

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
            factbook_data=json.dumps(country_data.get("factbook", {}), default=str),
            worldbank_data=json.dumps(country_data.get("worldbank", {}), default=str),
            gdelt_events=json.dumps(events.get("gdelt", []), default=str),
            acled_events=json.dumps(events.get("acled", []), default=str),
            military_data=json.dumps(military_data, default=str),
        )

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
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=self.ollama_timeout) as client:
            response = await client.post(f"{self.ollama_base_url}/api/generate", json=payload)
            response.raise_for_status()
            body = response.json()
        return str(body.get("response", ""))

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
