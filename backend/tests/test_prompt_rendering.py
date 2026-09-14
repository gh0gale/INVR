"""Prompt interpolation guard.

Both system prompts once wrote every placeholder with doubled braces, so the
models received the literal text `{state['ticker']}` and no analysis context at
all. The tutor then answered about whichever company it invented. Nothing in the
suite would have caught that, and nothing would have caught it coming back.

These tests stub the model, capture the exact system message that would have
been sent, and assert the data is really in it. No Ollama required.
"""
import asyncio

import pytest
from langchain_core.messages import HumanMessage

import app.orchestrator as orchestrator
import app.pipeline.tutor_graph as tutor_graph


class _Captured:
    """Stands in for the chat model and records the prompt it was handed."""

    prompt: str = ""

    def __init__(self, *args, **kwargs):
        pass

    async def ainvoke(self, messages, *args, **kwargs):
        _Captured.prompt = messages[0].content
        return _Reply()


class _Reply:
    content = (
        '{"personalized_reasoning": ["thesis"], "what_to_watch": ["condition"], '
        '"risk_warning": "risk", "tutor_triggers": ["RSI", "ATR"]}'
    )


GOLD = {
    "verdict": "STRONG BUY",
    "primary_reason": "Cleared all gates.",
    "gate_results": {"trend": "PASS", "rsi": "PASS"},
    "what_to_watch": ["hold above the 20 SMA"],
    "confidence_score": 78.0,
    "timeframe": "swing",
}
SILVER = {"rsi_14": 58.2, "atr_14": 41.3, "current_price": 2847.5}


@pytest.fixture
def synthesizer_prompt(monkeypatch) -> str:
    monkeypatch.setattr(orchestrator, "get_chat_model", lambda *a, **k: _Captured())
    state = {
        "ticker": "RELIANCE.NS",
        "timeframe": "swing",
        "user_profile": {"goal": "wealth_growth", "risk_tolerance": "moderate"},
        "silver": SILVER,
        "gold": GOLD,
        "errors": [],
    }
    asyncio.run(orchestrator.llm_synthesizer_node(state))
    return _Captured.prompt


@pytest.fixture
def tutor_prompt(monkeypatch) -> str:
    monkeypatch.setattr(tutor_graph, "get_chat_model", lambda *a, **k: _Captured())
    state = {
        "messages": [HumanMessage(content="what is ATR?")],
        "analysis_state": {
            "ticker": "RELIANCE.NS",
            "timeframe": "swing",
            "verdict": "STRONG BUY",
            "metrics": SILVER,
        },
        "user_profile": {"experience_level": "beginner", "goal": "wealth_growth"},
        "routed_mode": "definition",
        "tool_data": "",
    }
    asyncio.run(tutor_graph.generation_node(state, None))
    return _Captured.prompt


# ------------------------------------------------------------- the actual guard

def test_synthesizer_prompt_has_no_literal_placeholders(synthesizer_prompt):
    """The exact regression: doubled braces leaving `{state[...]}` in the text."""
    assert "{state[" not in synthesizer_prompt
    assert "{safe_silver}" not in synthesizer_prompt
    assert "{_safe_get" not in synthesizer_prompt


def test_synthesizer_prompt_carries_the_real_analysis(synthesizer_prompt):
    assert "RELIANCE.NS" in synthesizer_prompt
    assert "swing" in synthesizer_prompt
    assert "STRONG BUY" in synthesizer_prompt
    assert "58.2" in synthesizer_prompt          # a Silver metric really arrived


def test_synthesizer_prompt_keeps_its_json_schema_braces(synthesizer_prompt):
    """Those braces are meant to be literal. Fixing one bug must not cause another."""
    assert '"personalized_reasoning"' in synthesizer_prompt
    assert '"tutor_triggers"' in synthesizer_prompt


def test_tutor_prompt_has_no_literal_placeholders(tutor_prompt):
    assert "{ticker}" not in tutor_prompt
    assert "{analysis_state_str}" not in tutor_prompt
    assert "{experience}" not in tutor_prompt


def test_tutor_prompt_pins_the_displayed_ticker(tutor_prompt):
    """The stock on screen must be named, or the model picks its own."""
    assert "RELIANCE.NS" in tutor_prompt
    assert "58.2" in tutor_prompt
    assert "experience beginner" in tutor_prompt


def test_tutor_prompt_does_not_leak_another_company(tutor_prompt):
    for other in ("HDFC", "TCS", "INFY"):
        assert other not in tutor_prompt


def test_news_tool_does_not_fall_back_to_another_ticker():
    """It used to default to RELIANCE.NS when no ticker was loaded."""
    result = asyncio.run(
        tutor_graph.news_tool_node({"analysis_state": {}, "messages": []})
    )
    assert "RELIANCE" not in result["tool_data"]
    assert "no ticker" in result["tool_data"].lower()
