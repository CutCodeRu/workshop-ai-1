from __future__ import annotations

from typing import Any

import asyncpg
import psycopg

from app.config import RagSettings, Settings


class DatabaseConnectionError(ConnectionError):
    """Ошибка подключения к PostgreSQL."""


SCHEMA_STATEMENTS = (
    "CREATE EXTENSION IF NOT EXISTS vector;",
    """
    CREATE TABLE IF NOT EXISTS leads (
        id BIGSERIAL PRIMARY KEY,
        telegram_chat_id BIGINT NOT NULL,
        telegram_user_id BIGINT NULL,
        telegram_username TEXT NULL,
        customer_name TEXT NOT NULL,
        phone_raw TEXT NOT NULL,
        phone_normalized TEXT NOT NULL,
        question TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'new',
        notified_at TIMESTAMPTZ NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_leads_status_created_at
    ON leads (status, created_at DESC);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_leads_phone_normalized
    ON leads (phone_normalized);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_leads_telegram_user_id_created_at
    ON leads (telegram_user_id, created_at DESC);
    """,
    """
    CREATE TABLE IF NOT EXISTS documents (
        id BIGSERIAL PRIMARY KEY,
        source_path TEXT NOT NULL UNIQUE,
        checksum TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS document_chunks (
        id BIGSERIAL PRIMARY KEY,
        document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        section_slug TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        category TEXT NULL,
        topic TEXT NULL,
        tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
        content TEXT NOT NULL,
        embedding vector(1536) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (document_id, section_slug, chunk_index)
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
    ON document_chunks (document_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_cosine
    ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
    """,
)


def get_asyncpg_connection_kwargs(settings: Settings | RagSettings) -> dict[str, Any]:
    """Собирает параметры подключения для asyncpg."""
    return {
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "database": settings.postgres_db,
        "user": settings.postgres_user,
        "password": settings.postgres_password,
    }


def get_psycopg_connection_kwargs(settings: Settings | RagSettings) -> dict[str, Any]:
    """Собирает параметры подключения для psycopg."""
    return {
        "host": settings.postgres_host,
        "port": settings.postgres_port,
        "dbname": settings.postgres_db,
        "user": settings.postgres_user,
        "password": settings.postgres_password,
    }


async def connect(settings: Settings | RagSettings) -> asyncpg.Connection:
    """Открывает асинхронное соединение с PostgreSQL и нормализует ошибки подключения."""
    try:
        return await asyncpg.connect(**get_asyncpg_connection_kwargs(settings))
    except (
        OSError,
        ValueError,
        asyncpg.CannotConnectNowError,
        asyncpg.InvalidCatalogNameError,
        asyncpg.InvalidPasswordError,
        asyncpg.PostgresConnectionError,
    ) as exc:
        raise DatabaseConnectionError(
            "Не удалось подключиться к PostgreSQL. Проверьте параметры подключения и доступность базы данных."
        ) from exc


def connect_sync(settings: Settings | RagSettings) -> psycopg.Connection:
    """Открывает синхронное соединение с PostgreSQL и нормализует ошибки подключения."""
    try:
        return psycopg.connect(**get_psycopg_connection_kwargs(settings))
    except (OSError, ValueError, psycopg.Error) as exc:
        raise DatabaseConnectionError(
            "Не удалось подключиться к PostgreSQL. Проверьте параметры подключения и доступность базы данных."
        ) from exc


async def init_db(settings: Settings | RagSettings) -> None:
    """Создаёт таблицы, необходимые для первого этапа бота."""
    conn = await connect(settings)
    try:
        for statement in SCHEMA_STATEMENTS:
            await conn.execute(statement)
    finally:
        await conn.close()


def init_db_sync(settings: Settings | RagSettings) -> None:
    """Создаёт таблицы, необходимые для standalone ingestion и поиска."""
    with connect_sync(settings) as conn:
        with conn.cursor() as cursor:
            for statement in SCHEMA_STATEMENTS:
                cursor.execute(statement)
        conn.commit()
