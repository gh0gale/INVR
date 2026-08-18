"""Prompt versions and generation limits.

Audit findings P4-05 (no prompt versioning, so a rewrite was unattributable in
telemetry and had no rollback marker) and NEW-LLM-02 (no token ceiling, so an
unbounded generation could stall a streaming response indefinitely).

Bump the relevant version whenever you change the wording, the directives or
the output contract of a prompt. The value is attached to the OTel span for
that generation, so a shift in output quality can be traced to the exact prompt
revision that caused it.

History
-------
v1  Original prompts. Every placeholder was double-braced, so the models
    received literal `{state['ticker']}` text and no context at all.
v2  2026-08-18. Braces fixed so data actually interpolates; the tutor prompt
    now pins the displayed ticker and forbids naming another company; both
    prompts ask for `**bold**` headers, which the frontend renders as typography.
"""

SYNTHESIZER_PROMPT_VERSION = "synth-v2"
TUTOR_PROMPT_VERSION = "tutor-v2"
MEMORY_PROMPT_VERSION = "memory-v1"
GUARDRAIL_PROMPT_VERSION = "guard-v1"

# Generation ceilings, in tokens. Ollama calls this `num_predict`.
# Sized from the output each prompt actually asks for, with headroom: the
# synthesiser emits a JSON tear sheet, the tutor a few short sections, the
# memory extractor two sentences, and the guardrail a single word.
SYNTHESIZER_MAX_TOKENS = 1200
TUTOR_MAX_TOKENS = 900
MEMORY_MAX_TOKENS = 400
GUARDRAIL_MAX_TOKENS = 8
