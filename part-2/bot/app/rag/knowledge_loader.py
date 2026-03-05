from __future__ import annotations

import logging
from pathlib import Path

from app.adapters.embeddings.base import EmbeddingsProvider
from app.adapters.embeddings.openai_adapter import OpenAIEmbeddingsAdapter
from app.config import get_settings
from app.db.connection import create_connection_pool
from app.rag.chunker import split_into_chunks
from app.rag.indexer import index_chunks
from app.repositories.knowledge_repository import KnowledgeRepository

logger = logging.getLogger(__name__)


def _build_default_embeddings_provider() -> EmbeddingsProvider:
    """Собирает OpenAI-провайдер из настроек проекта."""

    settings = get_settings()
    if not settings.embeddings_api_key:
        raise RuntimeError(
            "Не задан EMBEDDINGS_API_KEY или OPENAI_API_KEY для построения embeddings."
        )

    return OpenAIEmbeddingsAdapter(
        api_key=settings.embeddings_api_key,
        base_url=settings.embeddings_base_url,
        model=settings.embeddings_model,
        timeout_seconds=settings.embeddings_timeout_seconds,
        max_retries=settings.embeddings_max_retries,
    )


async def load_knowledge(
    filepath: str | Path,
    *,
    embeddings_provider: EmbeddingsProvider | None = None,
) -> int:
    """
    Читает knowledge.md, режет на чанки, строит embeddings и сохраняет всё в pgvector.

    Возвращаем количество чанков, которые реально записали в базу.
    """

    source_path = Path(filepath).expanduser().resolve()
    logger.info("Начинаем загрузку базы знаний из %s", source_path)

    raw_text = source_path.read_text(encoding="utf-8")
    chunks = split_into_chunks(raw_text, source=str(source_path))
    logger.info("Файл %s разбит на %s чанков.", source_path, len(chunks))

    provider = embeddings_provider or _build_default_embeddings_provider()
    pool = await create_connection_pool()
    try:
        repository = KnowledgeRepository(pool)
        await repository.ensure_schema()
        stored_count = await index_chunks(
            chunks=chunks,
            raw_text=raw_text,
            embeddings_provider=provider,
            repository=repository,
        )
    finally:
        await pool.close()

    logger.info(
        "Загрузка базы знаний завершена. source=%s, chunks_saved=%s",
        source_path,
        stored_count,
    )
    return stored_count
