from __future__ import annotations

import logging

from app.adapters.embeddings.base import EmbeddingsProvider
from app.adapters.embeddings.openai_adapter import OpenAIEmbeddingsAdapter
from app.config import get_settings
from app.db.connection import create_connection_pool
from app.repositories.knowledge_repository import KnowledgeRepository

logger = logging.getLogger(__name__)


def _build_default_embeddings_provider() -> EmbeddingsProvider:
    """Создаёт тот же embeddings-провайдер, который использовался при индексации."""

    settings = get_settings()
    if not settings.embeddings_api_key:
        raise RuntimeError(
            "Не задан EMBEDDINGS_API_KEY или OPENAI_API_KEY для выполнения поиска."
        )

    return OpenAIEmbeddingsAdapter(
        api_key=settings.embeddings_api_key,
        base_url=settings.embeddings_base_url,
        model=settings.embeddings_model,
        timeout_seconds=settings.embeddings_timeout_seconds,
        max_retries=settings.embeddings_max_retries,
    )


async def search(
    query: str,
    top_k: int = 3,
    *,
    embeddings_provider: EmbeddingsProvider | None = None,
) -> list[str]:
    """
    Ищет top_k похожих чанков и возвращает только тексты.

    Под капотом:
    1. строим embedding пользовательского вопроса;
    2. ищем ближайшие чанки в pgvector;
    3. логируем, что именно нашли и насколько это близко;
    4. отдаём список текстов, который дальше можно скормить LLM.
    """

    normalized_query = query.strip()
    if not normalized_query:
        logger.info("Пустой запрос в search(), возвращаем пустой список.")
        return []

    logger.info("Запускаем RAG-поиск. query=%r, top_k=%s", normalized_query, top_k)

    provider = embeddings_provider or _build_default_embeddings_provider()
    query_embedding = await provider.embed_query(normalized_query)

    pool = await create_connection_pool()
    try:
        repository = KnowledgeRepository(pool)
        await repository.ensure_schema()
        results = await repository.search(query_embedding=query_embedding, top_k=top_k)
    finally:
        await pool.close()

    logger.info("RAG-поиск завершён. Найдено %s чанков.", len(results))
    return [result.content for result in results]
