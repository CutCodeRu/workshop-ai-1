from __future__ import annotations

import logging

import asyncpg

from .connection import DatabaseConnectionError, create_connection_pool

logger = logging.getLogger(__name__)

_CREATE_TABLES_STATEMENTS = (
    """
    CREATE EXTENSION IF NOT EXISTS vector;
    """,
    """
    CREATE TABLE IF NOT EXISTS applications (
        id BIGSERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        question TEXT NOT NULL,
        user_id BIGINT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
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
    """
    ALTER TABLE knowledge_chunks
        ADD COLUMN IF NOT EXISTS heading TEXT;
    """,
    """
    ALTER TABLE knowledge_chunks
        ADD COLUMN IF NOT EXISTS checksum TEXT;
    """,
    """
    ALTER TABLE knowledge_chunks
        ADD COLUMN IF NOT EXISTS embedding vector(1536);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_applications_user_id
        ON applications (user_id);
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


async def init_db() -> None:
    """Создаёт в PostgreSQL таблицы applications и knowledge_chunks, если они ещё не существуют."""

    pool = await create_connection_pool()
    try:
        async with pool.acquire() as connection:
            async with connection.transaction():
                for statement in _CREATE_TABLES_STATEMENTS:
                    await connection.execute(statement)
    except DatabaseConnectionError:
        raise
    except asyncpg.PostgresError as exc:
        logger.exception("Не удалось инициализировать схему базы данных.")
        raise RuntimeError("Не удалось создать таблицы в PostgreSQL.") from exc
    finally:
        await pool.close()


async def save_application(name: str, phone: str, question: str, user_id: int) -> int:
    """Сохраняет заявку пользователя в таблицу applications и возвращает идентификатор новой записи."""

    pool = await create_connection_pool()
    try:
        async with pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                INSERT INTO applications (name, phone, question, user_id)
                VALUES ($1, $2, $3, $4)
                RETURNING id;
                """,
                name.strip(),
                phone.strip(),
                question.strip(),
                user_id,
            )
    except DatabaseConnectionError:
        raise
    except asyncpg.PostgresError as exc:
        logger.exception("Не удалось сохранить заявку пользователя user_id=%s.", user_id)
        raise RuntimeError("Не удалось сохранить заявку в PostgreSQL.") from exc
    finally:
        await pool.close()

    if row is None:
        raise RuntimeError("PostgreSQL не вернул идентификатор сохранённой заявки.")

    return int(row["id"])
