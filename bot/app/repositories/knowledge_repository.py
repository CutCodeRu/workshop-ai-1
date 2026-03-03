from __future__ import annotations

import logging
from dataclasses import dataclass

from asyncpg import Pool

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 1536


@dataclass(slots=True)
class StoredChunk:
    """Чанк, который уже готов к записи в PostgreSQL."""

    content: str
    source: str
    chunk_index: int
    heading: str | None
    checksum: str
    embedding: list[float]


@dataclass(slots=True)
class SearchResult:
    """Результат векторного поиска по базе знаний."""

    content: str
    source: str | None
    chunk_index: int | None
    heading: str | None
    distance: float
    similarity: float


def vector_to_pg_literal(vector: list[float]) -> str:
    """Преобразует Python-список в строку формата pgvector: [0.1,0.2,...]."""

    return "[" + ",".join(f"{value:.12f}" for value in vector) + "]"


def l2_distance_to_cosine_similarity(distance: float) -> float:
    """
    Пересчитывает L2-distance в cosine similarity.

    Формула работает только потому, что embeddings заранее нормализованы.
    Для unit-векторов: ||a - b||^2 = 2 - 2 * cosine_similarity.
    """

    similarity = 1 - (distance * distance) / 2
    return max(-1.0, min(1.0, similarity))


class KnowledgeRepository:
    """SQL-слой для загрузки и поиска чанков базы знаний."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def ensure_schema(self) -> None:
        """
        Готовит расширение vector, таблицу и индексы.

        Метод можно вызывать перед каждой индексацией и поиском:
        PostgreSQL просто пропустит уже существующие объекты.
        """

        statements = (
            "CREATE EXTENSION IF NOT EXISTS vector;",
            """
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id BIGSERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                source TEXT,
                chunk_index INTEGER,
                heading TEXT,
                checksum TEXT,
                embedding vector(1536),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """,
            "ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS heading TEXT;",
            "ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS checksum TEXT;",
            """
            ALTER TABLE knowledge_chunks
                ADD COLUMN IF NOT EXISTS embedding vector(1536);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source_chunk_index
                ON knowledge_chunks (source, chunk_index);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source_checksum
                ON knowledge_chunks (source, checksum);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_l2
                ON knowledge_chunks
                USING ivfflat (embedding vector_l2_ops)
                WITH (lists = 100);
            """,
        )

        async with self._pool.acquire() as connection:
            async with connection.transaction():
                for statement in statements:
                    await connection.execute(statement)

    async def replace_chunks(self, source: str, checksum: str, chunks: list[StoredChunk]) -> int:
        """
        Полностью переиндексирует один исходный файл.

        Это проще и надёжнее, чем пытаться обновлять отдельные чанки по месту:
        если текст изменился, мы удаляем старую версию и вставляем новую.
        """

        async with self._pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "DELETE FROM knowledge_chunks WHERE source = $1;",
                    source,
                )

                if not chunks:
                    logger.info("Файл %s не дал ни одного чанка для записи.", source)
                    return 0

                await connection.executemany(
                    """
                    INSERT INTO knowledge_chunks (
                        content,
                        source,
                        chunk_index,
                        heading,
                        checksum,
                        embedding
                    )
                    VALUES ($1, $2, $3, $4, $5, $6::vector);
                    """,
                    [
                        (
                            chunk.content,
                            chunk.source,
                            chunk.chunk_index,
                            chunk.heading,
                            checksum,
                            vector_to_pg_literal(chunk.embedding),
                        )
                        for chunk in chunks
                    ],
                )

        logger.info(
            "Сохранили %s чанков в knowledge_chunks для файла %s (checksum=%s).",
            len(chunks),
            source,
            checksum,
        )
        return len(chunks)

    async def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        """
        Ищет top-k похожих чанков через pgvector.

        Используем оператор `<->`, как просил пользователь. Поскольку и
        document embeddings, и query embedding нормализованы, такой поиск
        эквивалентен cosine-ранжированию.
        """

        if top_k <= 0:
            return []

        async with self._pool.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT
                    content,
                    source,
                    chunk_index,
                    heading,
                    embedding <-> $1::vector AS distance
                FROM knowledge_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <-> $1::vector ASC
                LIMIT $2;
                """,
                vector_to_pg_literal(query_embedding),
                top_k,
            )

        results = [
            SearchResult(
                content=row["content"],
                source=row["source"],
                chunk_index=row["chunk_index"],
                heading=row["heading"],
                distance=float(row["distance"]),
                similarity=l2_distance_to_cosine_similarity(float(row["distance"])),
            )
            for row in rows
        ]

        for index, result in enumerate(results, start=1):
            preview = result.content.replace("\n", " ")[:120]
            logger.info(
                "RAG hit #%s | source=%s | chunk=%s | similarity=%.4f | distance=%.4f | preview=%s",
                index,
                result.source,
                result.chunk_index,
                result.similarity,
                result.distance,
                preview,
            )

        return results
