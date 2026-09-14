"""Embedding model for the tutor's semantic router.

deployment_plan.md §1.4. The router embeds each incoming message and compares
it with five category centroids, so the query and the centroids must come from
the same model and the same dimensionality. `embedding_identity()` names that
pair, and precomputed centroids are stored under it (see
app/pipeline/router_centroids.json and scripts/build_centroids.py).

There is deliberately no fallback provider here. Falling back from one
embedding space to another would compare vectors that share nothing, and the
router would pick categories at random while looking healthy. When embedding
fails the router routes to `fallback` instead, which only costs context
trimming, never correctness.
"""
from __future__ import annotations

from typing import Any

from app.config import settings

DEFAULT_EMBEDDING_MODELS = {
    "ollama": "nomic-embed-text",
    # text-embedding-004 was retired in January 2026.
    "gemini": "models/gemini-embedding-001",
}

# gemini-embedding-001 is trained so its leading dimensions stand on their own.
# 768 matches nomic-embed-text, keeps the committed centroid file small, and
# loses nothing a five-way classification can use. Cosine similarity normalises,
# so the truncated vectors need no rescaling.
GEMINI_EMBEDDING_DIM = 768

_EMBEDDERS: dict[str, Any] = {}


class EmbeddingConfigError(RuntimeError):
    pass


def embedding_model_name() -> str:
    return (settings.EMBEDDING_MODEL or "").strip() or DEFAULT_EMBEDDING_MODELS[settings.EMBEDDING_PROVIDER]


def embedding_identity() -> str:
    """e.g. `ollama:nomic-embed-text` or `gemini:models/gemini-embedding-001@768`."""
    provider = settings.EMBEDDING_PROVIDER
    ident = f"{provider}:{embedding_model_name()}"
    if provider == "gemini":
        ident += f"@{GEMINI_EMBEDDING_DIM}"
    return ident


def get_embedder() -> Any:
    """The embedding model for the configured provider, built once per identity."""
    ident = embedding_identity()
    if ident in _EMBEDDERS:
        return _EMBEDDERS[ident]

    provider = settings.EMBEDDING_PROVIDER
    name = embedding_model_name()
    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        embedder = OllamaEmbeddings(model=name, base_url=settings.OLLAMA_BASE_URL)
    elif provider == "gemini":
        if not settings.GOOGLE_API_KEY:
            raise EmbeddingConfigError("EMBEDDING_PROVIDER=gemini but GOOGLE_API_KEY is not set")
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        embedder = GoogleGenerativeAIEmbeddings(
            model=name,
            google_api_key=settings.GOOGLE_API_KEY,
            output_dimensionality=GEMINI_EMBEDDING_DIM,
        )
    else:
        raise EmbeddingConfigError(f"Unknown EMBEDDING_PROVIDER {provider!r}")

    _EMBEDDERS[ident] = embedder
    return embedder
