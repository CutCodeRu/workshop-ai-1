from __future__ import annotations

from collections.abc import Sequence

from openai import OpenAI

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


class EmbeddingProviderError(RuntimeError):
    """Raised when embeddings cannot be produced."""


def embed_texts(
    texts: Sequence[str],
    *,
    api_key: str,
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[list[float]]:
    """Generate OpenAI embeddings for a batch of texts."""
    if not texts:
        return []

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(model=model, input=list(texts))
    return [list(item.embedding) for item in response.data]


def embed_text(
    text: str,
    *,
    api_key: str,
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[float]:
    """Generate an embedding for a single text."""
    embeddings = embed_texts([text], api_key=api_key, model=model)
    if not embeddings:
        raise EmbeddingProviderError("OpenAI embeddings API returned an empty result.")
    return embeddings[0]
