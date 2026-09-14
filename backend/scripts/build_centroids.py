"""Precompute the tutor router's category centroids and commit them.

Audit MU-08 / deployment_plan.md §1.4. The five centroids are embeddings of
static text in `app/pipeline/tutor_graph.py`, so there is no reason to compute
them at runtime - where they cost five embedding calls on every cold start of
every instance before the first message can be routed.

Builds for whichever EMBEDDING_PROVIDER is configured and merges the result
into `app/pipeline/router_centroids.json` under that provider's identity, so
the file can hold both the local (Ollama) and the hosted (Gemini) vectors:

    python -m scripts.build_centroids                           # current .env
    EMBEDDING_PROVIDER=gemini python -m scripts.build_centroids  # needs GOOGLE_API_KEY

Re-run it whenever CATEGORY_DESCRIPTIONS changes;
tests/test_llm_provider.py fails until you do.
"""
import asyncio
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts._log import get_logger  # noqa: E402
from app.embeddings import embedding_identity  # noqa: E402
from app.pipeline.tutor_graph import (  # noqa: E402
    CENTROIDS_PATH,
    compute_centroids,
    descriptions_fingerprint,
)

logger = get_logger(__name__)


async def build() -> None:
    identity = embedding_identity()
    logger.info("Embedding %s category descriptions with %s ...", "router", identity)
    vectors = await compute_centroids()

    try:
        stored = json.loads(CENTROIDS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stored = {}

    stored[identity] = {
        "descriptions_sha": descriptions_fingerprint(),
        "dimensions": len(next(iter(vectors.values()))),
        # 7 decimal places moves a cosine score by well under 1e-6.
        "vectors": {k: [round(float(x), 7) for x in v] for k, v in vectors.items()},
    }
    CENTROIDS_PATH.write_text(json.dumps(stored, sort_keys=True) + "\n", encoding="utf-8")
    logger.info("Wrote %d centroids for %s to %s", len(vectors), identity, CENTROIDS_PATH.name)


if __name__ == "__main__":
    asyncio.run(build())
