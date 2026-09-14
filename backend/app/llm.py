"""The single place where a chat model provider is chosen.

deployment_plan.md §1.3. Five call sites used to construct their own
`ChatOllama`. Centralising them means a provider change, a model rename or a
failover chain is one edit rather than five, and it is the seam that makes the
free-tier ceiling in audit MU-06 survivable.

Selection is entirely env-driven (see app/config.py):

    LLM_PROVIDER=groq            primary
    LLM_FALLBACK_PROVIDER=gemini used when the primary raises (429, timeout, 5xx)
    LLM_MODEL_<TASK>=...         optional per-task override for the primary

The third rung is not here: when every provider fails, `llm_synthesizer_node`
returns a deterministic narrative built from the Gold verdict, and the verdict
never depended on the model in the first place.

`ollama` stays a valid provider and is the default, so local development runs
offline and free, and the migration is reversible by changing one variable.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from langchain_core.runnables import Runnable

from app.config import settings
from app.prompts import (
    GUARDRAIL_MAX_TOKENS,
    MEMORY_MAX_TOKENS,
    SYNTHESIZER_MAX_TOKENS,
    TUTOR_MAX_TOKENS,
)

logger = logging.getLogger(__name__)


class Task(str, Enum):
    SYNTHESIS = "synthesis"   # tear-sheet narrative, long JSON output
    TUTOR = "tutor"           # streamed chat
    MEMORY = "memory"         # short structured extraction
    GUARDRAIL = "guardrail"   # one-word classification
    SCOPE = "scope"           # one-word IN/OUT, is a tutor message on topic


@dataclass(frozen=True)
class TaskSpec:
    temperature: float
    max_tokens: int


# Temperatures and ceilings are carried over unchanged from the Ollama call
# sites. They were chosen deliberately (audit NEW-LLM-02) and a provider
# migration is not the place to change them silently.
TASK_SPECS: dict[Task, TaskSpec] = {
    Task.SYNTHESIS: TaskSpec(0.0, SYNTHESIZER_MAX_TOKENS),
    Task.TUTOR: TaskSpec(0.3, TUTOR_MAX_TOKENS),
    Task.MEMORY: TaskSpec(0.0, MEMORY_MAX_TOKENS),
    Task.GUARDRAIL: TaskSpec(0.0, GUARDRAIL_MAX_TOKENS),
    Task.SCOPE: TaskSpec(0.0, GUARDRAIL_MAX_TOKENS),
}

# Model names move faster than code. Every one of these can be overridden per
# task with LLM_MODEL_<TASK>, so a retirement is a config change.
#
# Chosen on 2026-09-13 from the providers' live model lists, not from
# documentation, after the first hosted run failed on names that no longer
# existed: Groq had withdrawn every Llama chat model (404 on
# llama-3.3-70b-versatile and llama-3.1-8b-instant), and Gemini's rolling
# `gemini-flash-latest` alias, like 3.7-flash, returned 503 "high demand" while
# the pinned 3.6-flash and the lite models answered. Pinned ids are therefore
# used for Gemini; re-check with `python -m scripts.check_llm` when a provider
# announces retirements.
DEFAULT_MODELS: dict[str, dict[Task, str]] = {
    # The local guardrail uses llama3.1 rather than phi3:mini. phi3:mini was
    # never pulled on the dev machine, so Stage B failed closed and refused
    # every merely-suspicious input, benign or not (audit OBS-03). A model that
    # is already loaded for the other three tasks costs nothing extra, and a
    # one-word YES/NO classification does not need a smaller one.
    "ollama": {
        Task.SYNTHESIS: "llama3.1",
        Task.TUTOR: "llama3.1",
        Task.MEMORY: "llama3.1",
        Task.GUARDRAIL: "llama3.1",
        Task.SCOPE: "llama3.1",
    },
    "groq": {
        Task.SYNTHESIS: "openai/gpt-oss-120b",
        Task.TUTOR: "openai/gpt-oss-120b",
        Task.MEMORY: "openai/gpt-oss-20b",
        Task.GUARDRAIL: "openai/gpt-oss-20b",
        Task.SCOPE: "openai/gpt-oss-20b",
    },
    "gemini": {
        Task.SYNTHESIS: "gemini-3.6-flash",
        Task.TUTOR: "gemini-3.6-flash",
        Task.MEMORY: "gemini-3.5-flash-lite",
        Task.GUARDRAIL: "gemini-3.5-flash-lite",
        Task.SCOPE: "gemini-3.5-flash-lite",
    },
}

# Both hosted families reason before they answer, and the reasoning is billed
# against the same output ceiling. Measured: gpt-oss at an 8-token ceiling spent
# 6 on reasoning and returned an empty string, with or without
# reasoning_effort=low; Gemini Flash spent 100-260. An empty reply is the worst
# case for the one-word classifiers: the guardrail reads it as "not YES" and
# admits the input. The headroom is only consumed when the model reasons.
# Gemini's reasoning on the real tear-sheet prompt measured 1,296-1,747 tokens
# over three runs, finishing within ~450 tokens of a 2,048 headroom. A longer
# tear sheet would have been cut mid-JSON, so the headroom is doubled.
GEMINI_THINKING_HEADROOM = 4096
GROQ_REASONING_HEADROOM = 1024

_API_KEY_SETTING = {"groq": "GROQ_API_KEY", "gemini": "GOOGLE_API_KEY"}


class LLMConfigError(RuntimeError):
    """A provider was selected but cannot be constructed (usually a missing key)."""


def model_name(provider: str, task: Task, *, primary: bool = True) -> str:
    """The model a provider will use for a task. Overrides apply to the primary only."""
    if primary:
        override = getattr(settings, f"LLM_MODEL_{task.name}", "") or ""
        if override.strip():
            return override.strip()
    return DEFAULT_MODELS[provider][task]


def _build(provider: str, task: Task, *, primary: bool, has_fallback: bool) -> Any:
    spec = TASK_SPECS[task]
    name = model_name(provider, task, primary=primary)

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=name,
            temperature=spec.temperature,
            num_predict=spec.max_tokens,
            base_url=settings.OLLAMA_BASE_URL,
        )

    key_setting = _API_KEY_SETTING[provider]
    api_key = getattr(settings, key_setting, "")
    if not api_key:
        raise LLMConfigError(f"LLM provider {provider!r} selected but {key_setting} is not set")

    # A primary with somewhere to fail over to should fail fast: retrying a
    # 429 on an exhausted free quota only delays the fallback that would work.
    retries = 1 if (primary and has_fallback) else 2

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=name,
            temperature=spec.temperature,
            max_tokens=spec.max_tokens + GROQ_REASONING_HEADROOM,
            api_key=api_key,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            max_retries=retries,
        )

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=name,
            temperature=spec.temperature,
            max_output_tokens=spec.max_tokens + GEMINI_THINKING_HEADROOM,
            google_api_key=api_key,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            max_retries=retries,
        )

    raise LLMConfigError(f"Unknown LLM provider {provider!r}")


def _chain(task: Task, adapt=lambda model: model) -> Runnable:
    """Primary provider, with the fallback provider behind it when one is usable.

    `adapt` is applied to each model before chaining, so structured output is
    bound per provider rather than on the fallback wrapper, which has no
    `with_structured_output` of its own.
    """
    primary_name = settings.LLM_PROVIDER
    fallback_name = settings.LLM_FALLBACK_PROVIDER
    if fallback_name == primary_name:
        fallback_name = ""

    try:
        primary = adapt(_build(primary_name, task, primary=True, has_fallback=bool(fallback_name)))
    except LLMConfigError as exc:
        if not fallback_name:
            raise
        # Misconfigured primary but a usable fallback: serve from the fallback
        # rather than failing every request, and say so loudly.
        logger.error("%s. Serving %s from fallback provider %r.", exc, task.value, fallback_name)
        return adapt(_build(fallback_name, task, primary=False, has_fallback=False))

    if not fallback_name:
        return primary

    try:
        secondary = adapt(_build(fallback_name, task, primary=False, has_fallback=False))
    except LLMConfigError as exc:
        logger.warning("%s. Running %s without failover.", exc, task.value)
        return primary

    return primary.with_fallbacks([secondary])


def get_chat_model(task: Task) -> Runnable:
    """A chat model for this task, honouring LLM_PROVIDER and LLM_FALLBACK_PROVIDER.

    Supports `ainvoke`. Token streaming for the tutor needs no flag: LangGraph's
    `stream_mode="messages"` streams through callbacks, and those reach
    whichever provider in the chain actually answers.
    """
    return _chain(task)


def get_structured_model(task: Task, schema: type) -> Runnable:
    """As get_chat_model, with structured output bound on every provider in the chain."""
    return _chain(task, adapt=lambda model: model.with_structured_output(schema))


def configured_providers() -> list[str]:
    """The providers in the chain, primary first."""
    chain = [settings.LLM_PROVIDER]
    fallback = settings.LLM_FALLBACK_PROVIDER
    if fallback and fallback != settings.LLM_PROVIDER:
        chain.append(fallback)
    return chain


def get_single_provider_model(provider: str, task: Task) -> Any:
    """One provider with no failover behind it.

    For diagnostics only (scripts/check_llm.py). Through a chain, a broken
    primary key is invisible whenever the fallback answers, which is exactly
    what a key check has to expose.
    """
    return _build(provider, task, primary=(provider == settings.LLM_PROVIDER), has_fallback=False)


def model_identity(task: Task) -> str:
    """A stable string naming the configured chain, e.g. `groq:llama-3.3-70b-versatile>gemini:gemini-flash-latest`.

    Part of the synthesis cache key and attached to the generation span, so a
    change of model invalidates cached narratives and is visible in traces.
    Without it, switching provider would keep serving the old model's text for
    the whole cache TTL.
    """
    primary = settings.LLM_PROVIDER
    ident = f"{primary}:{model_name(primary, task)}"
    fallback = settings.LLM_FALLBACK_PROVIDER
    if fallback and fallback != primary:
        ident += f">{fallback}:{model_name(fallback, task, primary=False)}"
    return ident


def message_text(message: Any) -> str:
    """The text of a model reply, whatever shape the provider returned it in.

    Newer Gemini models return `content` as a list of parts
    (`[{"type": "text", "text": ...}]`) rather than a string. Every call site
    that did `.content.upper()` or `.content.split()` raised on that, and through
    the failover chain a Gemini answer became the deterministic fallback.
    LangChain's `.text` property flattens both shapes, for whole messages and
    streamed chunks alike. Always read replies through this.
    """
    if message is None:
        return ""
    text = getattr(message, "text", None)
    if isinstance(text, str):
        return text
    content = getattr(message, "content", message)
    return content if isinstance(content, str) else ""


def responding_model(response: Any) -> str | None:
    """The model that actually produced a response, when the provider reports it."""
    meta = getattr(response, "response_metadata", None) or {}
    return meta.get("model_name") or meta.get("model")
