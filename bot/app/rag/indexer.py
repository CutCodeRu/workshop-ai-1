from __future__ import annotations

import hashlib
import logging

from app.adapters.embeddings.base import EmbeddingsProvider
from app.rag.chunker import ChunkDraft
from app.repositories.knowledge_repository import KnowledgeRepository, StoredChunk

logger = logging.getLogger(__name__)


def build_checksum(text: str) -> str:
    """Хэш нужен, чтобы в логах было видно, какая версия файла загружена в базу."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def index_chunks(
    chunks: list[ChunkDraft],
    raw_text: str,
    embeddings_provider: EmbeddingsProvider,
    repository: KnowledgeRepository,
) -> int:
    """
    Строит embeddings для чанков и сохраняет их в PostgreSQL.

    Мы сначала считаем embeddings для всех чанков, затем одним шагом
    заменяем старую версию документа в таблице knowledge_chunks.
    """

    if not chunks:
        logger.warning("Индексация пропущена: после разбиения нет ни одного чанка.")
        return 0

    logger.info("Начинаем генерацию embeddings для %s чанков.", len(chunks))
    chunk_embeddings = await embeddings_provider.embed_texts(
        [chunk.content for chunk in chunks]
    )

    checksum = build_checksum(raw_text)
    stored_chunks = [
        StoredChunk(
            content=chunk.content,
            source=chunk.source,
            chunk_index=chunk.chunk_index,
            heading=chunk.heading,
            checksum=checksum,
            embedding=embedding,
        )
        for chunk, embedding in zip(chunks, chunk_embeddings, strict=True)
    ]

    logger.info("Embeddings готовы, записываем чанки в PostgreSQL.")
    return await repository.replace_chunks(
        source=chunks[0].source,
        checksum=checksum,
        chunks=stored_chunks,
    )
