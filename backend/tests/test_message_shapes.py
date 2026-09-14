"""Model replies are read the same way whatever shape they arrive in.

Found 2026-09-13 on the first run against hosted models: newer Gemini models
return `content` as a list of parts, not a string. The guardrail
(`.content.upper()`), the scope classifier (`.strip()`) and the synthesiser
(`re.search` on it) all raised, and through the failover chain a Gemini answer
turned into the deterministic "AI Synthesizer is currently offline" narrative.
"""
import asyncio
import inspect

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk

import app.guardrails.scope as scope
import app.orchestrator as orchestrator
import app.services.guardrail_service as guardrail
from app.llm import message_text


def parts(text):
    """How Gemini 3.x shapes a reply."""
    return AIMessage(content=[{"type": "text", "text": text}])


class _Replies:
    def __init__(self, message):
        self.message = message

    async def ainvoke(self, *args, **kwargs):
        return self.message


class TestMessageText:
    def test_list_of_parts(self):
        msg = AIMessage(content=[{"type": "text", "text": "Hello "}, {"type": "text", "text": "world"}])
        assert message_text(msg) == "Hello world"

    def test_plain_string(self):
        assert message_text(AIMessage(content="plain")) == "plain"

    def test_streamed_chunk_of_parts(self):
        assert message_text(AIMessageChunk(content=[{"type": "text", "text": "tok", "index": 0}])) == "tok"

    def test_nothing(self):
        assert message_text(None) == ""


class TestEveryReaderAcceptsParts:
    def test_guardrail_reads_a_yes_in_parts(self, monkeypatch):
        monkeypatch.setattr(guardrail, "get_chat_model", lambda *a, **k: _Replies(parts("YES")))
        safe, _ = asyncio.run(guardrail.check_input_safety("tell me a joke"))
        assert safe is False, "a YES must still block when it arrives as a list of parts"

    def test_scope_classifier_reads_out_in_parts(self, monkeypatch):
        monkeypatch.setattr(scope, "get_chat_model", lambda *a, **k: _Replies(parts("OUT")))
        assert asyncio.run(scope.classify_with_model("write a poem", "TCS.NS")) == "out"

    def test_synthesiser_does_not_fall_back_on_parts(self, monkeypatch):
        body = ('<thinking>ok</thinking>{"personalized_reasoning": ["x"], "what_to_watch": ["y"], '
                '"risk_warning": "r", "tutor_triggers": ["RSI", "ATR"]}')
        monkeypatch.setattr(orchestrator, "get_chat_model", lambda *a, **k: _Replies(parts(body)))
        state = {"ticker": "TEST.NS", "timeframe": "swing", "user_profile": {},
                 "silver": {"rsi_14": 50.0}, "gold": {"verdict": "MONITOR"}, "errors": []}
        out = asyncio.run(orchestrator.llm_synthesizer_node(state))["llm_output"]
        assert "raw_json_string" in out, "a parts-shaped reply must be parsed, not replaced by the fallback"
        assert out["raw_json_string"].startswith('{"personalized_reasoning"')

    def test_synthesiser_request_has_a_user_turn(self, monkeypatch):
        """Gemini rejects a system-only request ("contents are required") and
        Qwen's template will not render one; both surfaced as the fallback."""
        seen = {}

        class _Records:
            async def ainvoke(self, messages, *a, **k):
                seen["types"] = [type(m).__name__ for m in messages]
                return AIMessage(content='{"personalized_reasoning": ["x"], "what_to_watch": ["y"], '
                                         '"risk_warning": "r", "tutor_triggers": ["RSI", "ATR"]}')

        monkeypatch.setattr(orchestrator, "get_chat_model", lambda *a, **k: _Records())
        state = {"ticker": "TEST.NS", "timeframe": "swing", "user_profile": {},
                 "silver": {"rsi_14": 50.0}, "gold": {"verdict": "MONITOR"}, "errors": []}
        asyncio.run(orchestrator.llm_synthesizer_node(state))
        assert seen["types"] == ["SystemMessage", "HumanMessage"]

    def test_tutor_stream_sends_text_not_an_array(self):
        import app.api.routes.tutor as route

        source = inspect.getsource(route.chat_stream)
        assert "message_text(chunk)" in source
        assert "chunk.content" not in source
