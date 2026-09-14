"""Check that the configured model providers actually answer, one at a time.

Run this after adding API keys and before starting the server:

    python -m scripts.check_llm

It reads the same settings as the app (`backend/.env`), then for every
provider in the chain (LLM_PROVIDER, then LLM_FALLBACK_PROVIDER) sends one tiny
request per task and prints the model, the latency and a short excerpt of the
reply. Providers are tested separately, never through the failover chain,
because a broken primary key is invisible whenever the fallback answers.

It also embeds one sentence with EMBEDDING_PROVIDER and says whether
precomputed router centroids exist for it.

Keys are reported as set or missing, never printed. Costs a handful of free-tier
requests. Exit code 0 only if every task works on the primary provider.
"""
import asyncio
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, SystemMessage  # noqa: E402

from scripts._log import get_logger  # noqa: E402
from app.config import settings  # noqa: E402
from app.embeddings import embedding_identity, get_embedder  # noqa: E402
from app.llm import Task, configured_providers, get_single_provider_model, message_text, model_name  # noqa: E402

logger = get_logger(__name__)

PROBES = {
    Task.SYNTHESIS: "Reply with one short sentence about the NSE.",
    Task.TUTOR: "In one sentence, what does RSI measure?",
    Task.GUARDRAIL: "Reply with exactly one word: NO",
    Task.SCOPE: "Reply with exactly one word: IN",
}
MEMORY_CHUNK = "User: what is RSI?\nTutor: RSI measures momentum on a 0-100 scale."


def _short(error: Exception) -> str:
    text = " ".join(str(error).split())
    return f"{type(error).__name__}: {text[:160]}"


async def probe(provider: str, task: Task) -> tuple[bool, str]:
    model = get_single_provider_model(provider, task)
    if task is Task.MEMORY:
        # Memory extraction uses structured output, which some provider/model
        # pairs do not support. Worth proving, not assuming.
        from app.pipeline.memory_graph import MemoryUpdate

        model = model.with_structured_output(MemoryUpdate)
        messages = [SystemMessage(content="Extract memory from this chat."), HumanMessage(content=MEMORY_CHUNK)]
    else:
        messages = [HumanMessage(content=PROBES[task])]

    started = time.perf_counter()
    reply = await asyncio.wait_for(model.ainvoke(messages), timeout=settings.LLM_TIMEOUT_SECONDS + 5)
    elapsed = time.perf_counter() - started

    if task is Task.MEMORY:
        excerpt = f"concepts={reply.new_learned_concepts}"
    else:
        text = message_text(reply)
        excerpt = " ".join(text.split())[:70] or "(empty reply)"
        if not text:
            return False, f"{elapsed:5.1f}s  empty reply"
    return True, f"{elapsed:5.1f}s  {excerpt}"


async def main() -> int:
    chain = configured_providers()
    logger.info("Provider chain: %s", " -> ".join(chain) + " -> deterministic fallback")
    for key in ("GROQ_API_KEY", "GOOGLE_API_KEY"):
        logger.info("%-15s %s", key, "set" if getattr(settings, key) else "missing")

    primary_ok = True
    for provider in chain:
        role = "primary" if provider == chain[0] else "fallback"
        logger.info("\n[%s] %s", role, provider)
        for task in Task:
            label = f"  {task.value:<10} {model_name(provider, task, primary=(role == 'primary')):<28}"
            try:
                ok, detail = await probe(provider, task)
            except Exception as e:  # noqa: BLE001 - reporting every failure is the point
                ok, detail = False, _short(e)
            (logger.info if ok else logger.warning)("%s %s  %s", label, "PASS" if ok else "FAIL", detail)
            if role == "primary" and not ok:
                primary_ok = False

    ident = embedding_identity()
    logger.info("\n[embeddings] %s", ident)
    try:
        started = time.perf_counter()
        vector = await get_embedder().aembed_query("what is RSI?")
        logger.info("  PASS  %.1fs  %d dimensions", time.perf_counter() - started, len(vector))
    except Exception as e:  # noqa: BLE001
        logger.warning("  FAIL  %s", _short(e))
        primary_ok = False

    from app.pipeline.tutor_graph import load_precomputed_centroids

    if load_precomputed_centroids(ident) is None:
        logger.warning("  router centroids: not precomputed for %s. Run `python -m scripts.build_centroids`.", ident)
    else:
        logger.info("  router centroids: precomputed")

    logger.info("\n%s", "All primary tasks answered." if primary_ok else "Some primary tasks FAILED - see above.")
    return 0 if primary_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
