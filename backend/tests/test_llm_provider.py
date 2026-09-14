"""Provider selection, failover, and the router's degradation paths.

deployment_plan.md §1. The migration off local Ollama moved five hard-coded
`ChatOllama(...)` calls behind `app/llm.py`. These tests pin down what that
seam promises:

  * with no configuration, behaviour is exactly the pre-migration behaviour
  * a hosted primary gets a failover provider behind it, and a primary failure
    actually reaches the secondary - including mid-graph, while streaming
  * when every provider fails, the verdict still ships (deterministic path)
  * a change of model invalidates cached narratives
  * the router degrades to `fallback` instead of failing the chat, and uses
    committed centroids instead of re-embedding them on every cold start

No network: hosted clients are constructed with dummy keys (construction makes
no call) and every generation goes through a fake model.
"""
import asyncio
import json

import numpy as np
import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables.fallbacks import RunnableWithFallbacks
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from pydantic import ValidationError

import app.orchestrator as orchestrator
import app.pipeline.tutor_graph as tutor_graph
from app import llm
from app.config import Settings, settings
from app.llm import (
    GEMINI_THINKING_HEADROOM,
    GROQ_REASONING_HEADROOM,
    LLMConfigError,
    Task,
    get_chat_model,
    get_structured_model,
    model_identity,
)


class _Down(GenericFakeChatModel):
    """A provider that is out of quota: every call raises, streamed or not."""

    def _generate(self, *args, **kwargs):
        raise RuntimeError("429 rate limit exceeded")

    def _stream(self, *args, **kwargs):
        raise RuntimeError("429 rate limit exceeded")


def _down():
    return _Down(messages=iter([]))


def _up(text):
    return GenericFakeChatModel(messages=iter([AIMessage(content=text)]))


@pytest.fixture
def hosted(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "LLM_FALLBACK_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk-test")
    monkeypatch.setattr(settings, "GOOGLE_API_KEY", "google-test")


# --------------------------------------------------------------- no config

class TestDefaultIsThePreMigrationBehaviour:
    @pytest.mark.parametrize(
        "task, model, temperature, ceiling",
        [
            (Task.SYNTHESIS, "llama3.1", 0.0, 1200),
            (Task.TUTOR, "llama3.1", 0.3, 900),
            (Task.MEMORY, "llama3.1", 0.0, 400),
            (Task.GUARDRAIL, "llama3.1", 0.0, 8),   # was phi3:mini, never installed (OBS-03)
        ],
    )
    def test_each_task_keeps_its_original_model_and_limits(self, task, model, temperature, ceiling):
        chat = get_chat_model(task)
        assert isinstance(chat, ChatOllama)
        assert chat.model == model
        assert chat.temperature == temperature
        assert chat.num_predict == ceiling

    def test_no_failover_unless_configured(self):
        assert not isinstance(get_chat_model(Task.SYNTHESIS), RunnableWithFallbacks)


# --------------------------------------------------------- hosted selection

class TestHostedSelection:
    def test_groq_primary_with_gemini_behind_it(self, hosted):
        chain = get_chat_model(Task.SYNTHESIS)
        assert isinstance(chain, RunnableWithFallbacks)
        assert isinstance(chain.runnable, ChatGroq)
        assert chain.runnable.model_name == "openai/gpt-oss-120b"
        assert isinstance(chain.fallbacks[0], ChatGoogleGenerativeAI)
        assert chain.fallbacks[0].model == "gemini-3.6-flash"

    def test_small_tasks_use_the_small_model(self, hosted):
        chain = get_chat_model(Task.GUARDRAIL)
        assert chain.runnable.model_name == "openai/gpt-oss-20b"

    def test_groq_gets_headroom_for_its_reasoning(self, hosted):
        """gpt-oss at an 8-token ceiling returned '' after 6 reasoning tokens (measured)."""
        assert get_chat_model(Task.GUARDRAIL).runnable.max_tokens == 8 + GROQ_REASONING_HEADROOM
        assert get_chat_model(Task.SCOPE).runnable.max_tokens == 8 + GROQ_REASONING_HEADROOM

    def test_gemini_gets_headroom_for_its_hidden_reasoning(self, hosted):
        """8 tokens of which Gemini spends some thinking would return '' and admit the input."""
        gemini = get_chat_model(Task.GUARDRAIL).fallbacks[0]
        assert gemini.max_output_tokens == 8 + GEMINI_THINKING_HEADROOM

    def test_primary_fails_fast_when_it_has_somewhere_to_go(self, hosted):
        chain = get_chat_model(Task.SYNTHESIS)
        assert chain.runnable.max_retries == 1
        assert chain.fallbacks[0].max_retries == 2

    def test_model_override_applies_to_the_primary_only(self, hosted, monkeypatch):
        monkeypatch.setattr(settings, "LLM_MODEL_SYNTHESIS", "some-new-model")
        chain = get_chat_model(Task.SYNTHESIS)
        assert chain.runnable.model_name == "some-new-model"
        assert chain.fallbacks[0].model == llm.DEFAULT_MODELS["gemini"][Task.SYNTHESIS]

    def test_missing_primary_key_without_fallback_is_a_clear_error(self, monkeypatch):
        monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
        monkeypatch.setattr(settings, "GROQ_API_KEY", "")
        with pytest.raises(LLMConfigError, match="GROQ_API_KEY"):
            get_chat_model(Task.SYNTHESIS)

    def test_missing_primary_key_serves_from_the_fallback(self, hosted, monkeypatch):
        monkeypatch.setattr(settings, "GROQ_API_KEY", "")
        assert isinstance(get_chat_model(Task.SYNTHESIS), ChatGoogleGenerativeAI)

    def test_missing_fallback_key_runs_the_primary_alone(self, hosted, monkeypatch):
        monkeypatch.setattr(settings, "GOOGLE_API_KEY", "")
        assert isinstance(get_chat_model(Task.SYNTHESIS), ChatGroq)

    def test_fallback_equal_to_primary_is_not_a_chain(self, hosted, monkeypatch):
        monkeypatch.setattr(settings, "LLM_FALLBACK_PROVIDER", "groq")
        assert isinstance(get_chat_model(Task.SYNTHESIS), ChatGroq)

    def test_structured_output_is_bound_on_both_providers(self, hosted):
        from app.pipeline.memory_graph import MemoryUpdate

        chain = get_structured_model(Task.MEMORY, MemoryUpdate)
        assert isinstance(chain, RunnableWithFallbacks)
        assert len(chain.fallbacks) == 1

    def test_unknown_provider_is_rejected_at_startup(self):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, LLM_PROVIDER="openai")


# ------------------------------------------------------------------ failover

class TestFailover:
    def test_a_primary_failure_reaches_the_secondary(self, hosted, monkeypatch):
        monkeypatch.setattr(llm, "_build", lambda provider, *a, **k: _down() if provider == "groq" else _up("from gemini"))
        reply = asyncio.run(get_chat_model(Task.SYNTHESIS).ainvoke([HumanMessage(content="hi")]))
        assert reply.content == "from gemini"

    def test_every_provider_down_still_ships_the_verdict(self, monkeypatch):
        """The third rung: the deterministic narrative, carrying the Gold verdict unchanged."""
        monkeypatch.setattr(orchestrator, "get_chat_model", lambda *a, **k: _down().with_fallbacks([_down()]))
        state = {
            "ticker": "TEST.NS",
            "timeframe": "swing",
            "user_profile": {},
            "silver": {"rsi_14": 50.0},
            "gold": {"verdict": "CAUTION", "confidence_score": 61.0, "primary_reason": "weak trend"},
            "errors": [],
        }
        out = asyncio.run(orchestrator.llm_synthesizer_node(state))["llm_output"]
        assert out["verdict"] == "CAUTION"
        assert out["confidence_score"] == 61.0
        assert "LLM_OFFLINE" in out["tutor_triggers"]

    def test_the_tutor_streams_from_the_fallback_mid_graph(self, monkeypatch):
        """Streaming is where failover is easiest to get wrong: tokens must still
        reach the SSE stream when the answering model is the second in the chain."""
        answer = "RSI measures momentum"
        monkeypatch.setattr(tutor_graph, "get_chat_model", lambda *a, **k: _down().with_fallbacks([_up(answer)]))
        monkeypatch.setattr(tutor_graph, "get_embedder", _raising_embedder)

        async def collect():
            graph = tutor_graph.build_tutor_graph()
            tokens = []
            state = {
                "messages": [HumanMessage(content="what is RSI?")],
                "analysis_state": {"ticker": "TEST.NS"},
                "user_profile": {},
                "routed_mode": "",
                "tool_data": "",
            }
            async for chunk, meta in graph.astream(state, stream_mode="messages"):
                if meta.get("langgraph_node") == "generate" and chunk.content:
                    tokens.append(chunk.content)
            return tokens

        tokens = asyncio.run(collect())
        assert len(tokens) > 1, "the answer should arrive as a stream, not one block"
        assert "".join(tokens) == answer


# ------------------------------------------------------------------ identity

class TestModelIdentity:
    def test_names_the_whole_chain(self, hosted):
        assert model_identity(Task.SYNTHESIS) == "groq:openai/gpt-oss-120b>gemini:gemini-3.6-flash"

    def test_local_identity(self):
        assert model_identity(Task.GUARDRAIL) == "ollama:llama3.1"

    def test_switching_provider_invalidates_the_synthesis_cache(self, monkeypatch):
        calls = []

        class _Counting:
            async def ainvoke(self, messages, *a, **k):
                calls.append(1)
                return AIMessage(content='{"personalized_reasoning": ["x"], "what_to_watch": ["y"], '
                                         '"risk_warning": "r", "tutor_triggers": ["RSI", "ATR"]}')

        monkeypatch.setattr(orchestrator, "get_chat_model", lambda *a, **k: _Counting())
        state = {
            "ticker": "TEST.NS",
            "timeframe": "swing",
            "user_profile": {"goal": "g", "risk_tolerance": "moderate"},
            "silver": {"rsi_14": 50.0},
            "gold": {"verdict": "MONITOR"},
            "errors": [],
        }
        asyncio.run(orchestrator.llm_synthesizer_node(state))
        asyncio.run(orchestrator.llm_synthesizer_node(state))
        assert len(calls) == 1, "same model: the second run is a cache hit"

        monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
        asyncio.run(orchestrator.llm_synthesizer_node(state))
        assert len(calls) == 2, "new model: the old narrative must not be served"


# -------------------------------------------------------------------- router

class _FakeEmbedder:
    def __init__(self, vector):
        self.vector = vector
        self.calls = 0

    async def aembed_query(self, text):
        self.calls += 1
        return list(self.vector)


def _raising_embedder():
    raise RuntimeError("embedding quota exhausted")


def _route(message):
    state = {"messages": [HumanMessage(content=message)]}
    return asyncio.run(tutor_graph.semantic_router_node(state))["routed_mode"]


class TestRouter:
    @pytest.fixture(autouse=True)
    def fresh_centroid_cache(self, monkeypatch):
        monkeypatch.setattr(tutor_graph, "_CATEGORY_VECTORS", {})

    def test_embedding_failure_routes_to_fallback_instead_of_failing(self, monkeypatch):
        monkeypatch.setattr(tutor_graph, "get_embedder", _raising_embedder)
        assert _route("what is RSI?") == "fallback"

    def _write_centroids(self, path, sha):
        vectors = {cat: np.eye(len(tutor_graph.CATEGORY_DESCRIPTIONS))[i].tolist()
                   for i, cat in enumerate(tutor_graph.CATEGORY_DESCRIPTIONS)}
        path.write_text(json.dumps({
            "ollama:nomic-embed-text": {"descriptions_sha": sha, "vectors": vectors}
        }), encoding="utf-8")
        return vectors

    def test_committed_centroids_are_used_without_re_embedding(self, tmp_path, monkeypatch):
        path = tmp_path / "centroids.json"
        vectors = self._write_centroids(path, tutor_graph.descriptions_fingerprint())
        monkeypatch.setattr(tutor_graph, "CENTROIDS_PATH", path)
        embedder = _FakeEmbedder(vectors["news"])
        monkeypatch.setattr(tutor_graph, "get_embedder", lambda: embedder)

        assert _route("any headlines today?") == "news"
        assert embedder.calls == 1, "only the message is embedded; the five centroids come from disk"

    def test_centroids_for_edited_descriptions_are_ignored(self, tmp_path, monkeypatch):
        path = tmp_path / "centroids.json"
        self._write_centroids(path, "stale-fingerprint")
        monkeypatch.setattr(tutor_graph, "CENTROIDS_PATH", path)
        assert tutor_graph.load_precomputed_centroids("ollama:nomic-embed-text") is None

    def test_the_committed_file_matches_the_current_descriptions(self):
        """Edit a category description without rebuilding and this fails, rather
        than the router silently comparing against vectors for the old text."""
        stored = json.loads(tutor_graph.CENTROIDS_PATH.read_text(encoding="utf-8"))
        assert stored, "run `python -m scripts.build_centroids`"
        for identity, entry in stored.items():
            assert entry["descriptions_sha"] == tutor_graph.descriptions_fingerprint(), (
                f"{identity} centroids are stale; run `python -m scripts.build_centroids`"
            )
            assert set(entry["vectors"]) == set(tutor_graph.CATEGORY_DESCRIPTIONS)
