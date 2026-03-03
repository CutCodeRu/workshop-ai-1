from __future__ import annotations

import logging
import os

import asyncpg
from asyncpg import Pool
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class DatabaseConnectionError(RuntimeError):
    """Ошибка подключения к PostgreSQL."""


def _normalize_database_url(database_url: str) -> str:
    """Приводит строку подключения к формату, понятному asyncpg."""

    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    if database_url.startswith("postgres+asyncpg://"):
        return database_url.replace("postgres+asyncpg://", "postgresql://", 1)

    return database_url


def _get_database_url() -> str:
    """Читает строку подключения к базе из переменной окружения DATABASE_URL."""

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise DatabaseConnectionError(
            "Не задана переменная окружения DATABASE_URL для подключения к PostgreSQL."
        )

    return _normalize_database_url(database_url)


async def create_connection_pool() -> Pool:
    """Создаёт пул соединений asyncpg и выбрасывает понятную ошибку при недоступности БД."""

    try:
        return await asyncpg.create_pool(
            dsn=_get_database_url(),
            min_size=1,
            max_size=5,
            command_timeout=10,
        )
    except (OSError, asyncpg.PostgresError) as exc:
        logger.exception("Не удалось подключиться к PostgreSQL.")
        raise DatabaseConnectionError(
            "Не удалось подключиться к PostgreSQL. Проверьте DATABASE_URL и доступность базы."
        ) from exc
