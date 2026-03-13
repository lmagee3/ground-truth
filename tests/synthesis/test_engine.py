import json

import pytest

from groundtruth.synthesis.engine import ContextEngine


@pytest.mark.asyncio
async def test_prompt_construction():
    engine = ContextEngine(provider="ollama")
    prompt = engine._build_prompt(  # pylint: disable=protected-access
        query="ukraine",
        depth="standard",
        country_data={
            "factbook": {"government": {}},
            "worldbank": {"GDP": [{"year": 2024, "value": 1}]},
        },
        events={"gdelt": [{"description": "event"}], "acled": []},
        military_data={"sipri": {}, "fas": {}},
    )
    assert "QUERY: ukraine" in prompt
    assert "WORLD BANK INDICATORS" in prompt


@pytest.mark.asyncio
async def test_ollama_client_mock(monkeypatch):
    engine = ContextEngine(provider="ollama")

    async def fake_ollama(prompt: str) -> str:
        return json.dumps(
            {
                "title": "Test",
                "summary": "Summary",
                "background": "Background",
                "timeline": [],
                "economic_context": "Eco",
                "military_context": "Mil",
                "perspectives": [],
                "current_assessment": "Assessment",
                "sources_cited": ["World Bank"],
                "confidence_notes": "OK",
            }
        )

    monkeypatch.setattr(engine, "_call_ollama", fake_ollama)
    report = await engine.generate_context(
        "ukraine", sources_available={"worldbank": {"status": "used"}}
    )
    assert report["title"] == "Test"
    assert "sources_available" in report


@pytest.mark.asyncio
async def test_anthropic_mock(monkeypatch):
    engine = ContextEngine(provider="anthropic")

    async def fake_anthropic(prompt: str) -> str:
        return '{"title":"A","summary":"B","background":"C","timeline":[],"economic_context":"D","military_context":"E","perspectives":[],"current_assessment":"F","sources_cited":[],"confidence_notes":"G"}'

    monkeypatch.setattr(engine, "_call_anthropic", fake_anthropic)
    report = await engine.generate_context("query", provider="anthropic", sources_available={})
    assert report["title"] == "A"


@pytest.mark.asyncio
async def test_fallback_when_provider_unavailable(monkeypatch):
    engine = ContextEngine(provider="ollama")

    async def broken(prompt: str) -> str:
        raise RuntimeError("down")

    monkeypatch.setattr(engine, "_call_ollama", broken)
    report = await engine.generate_context(
        "ukraine",
        depth="brief",
        country_data={"country": {"name": "Ukraine"}, "worldbank": {}, "factbook": {}},
        events={"gdelt": [], "acled": []},
        military_data={"sipri": {}, "fas": {}},
        sources_available={"gdelt": {"status": "skipped"}},
    )
    assert report["title"].startswith("Ground Truth Briefing")
    assert "fallback" in report["confidence_notes"].lower()


def test_json_extraction_from_wrapped_llm_output():
    engine = ContextEngine()
    raw = 'Here is your report:\n{"title":"X","summary":"Y"}\nThanks'
    parsed = engine._parse_llm_json(raw)  # pylint: disable=protected-access
    assert parsed is not None
    assert parsed["title"] == "X"
