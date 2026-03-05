from __future__ import annotations

from collections.abc import Sequence

from app.providers.openai_embeddings import embed_texts
from app.schemas.document import KnowledgeChunk


def embed_chunks(chunks: Sequence[KnowledgeChunk], *, api_key: str) -> list[list[float]]:
    """Generate embeddings for KB chunks in a single batch."""
    return embed_texts([chunk.content for chunk in chunks], api_key=api_key)
