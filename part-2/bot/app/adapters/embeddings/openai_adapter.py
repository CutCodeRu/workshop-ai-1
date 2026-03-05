from __future__ import annotations

import logging
import math

from .base import EmbeddingsProvider

logger = logging.getLogger(__name__)


def normalize_embedding(vector: list[float]) -> list[float]:
    """
    Нормализует вектор до длины 1.

    Мы делаем это специально, чтобы потом искать через оператор `<->`.
    Для нормализованных векторов L2-distance и cosine similarity дают
    одинаковый порядок ранжирования.
    """

    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        return vector
    return [value / length for value in vector]


class OpenAIEmbeddingsAdapter(EmbeddingsProvider):
    """Обёртка над OpenAI embeddings API."""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        model: str = "text-embedding-3-small",
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
    ) -> None:
        # Импортируем SDK лениво, чтобы модуль можно было тестировать
        # с фейковыми провайдерами даже в окружении без пакета openai.
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )
        self._model = model
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Строит embeddings пачкой, чтобы делать меньше сетевых запросов."""

        if not texts:
            return []

        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=texts,
            )
        except Exception as exc:
            # Импортируем исключения внутри метода по той же причине:
            # модуль должен импортироваться даже без пакета openai.
            from openai import APIConnectionError, APITimeoutError

            if isinstance(exc, APITimeoutError):
                logger.exception(
                    "OpenAI embeddings timeout. model=%s, timeout=%s, base_url=%s",
                    self._model,
                    self._timeout_seconds,
                    self._base_url or "https://api.openai.com/v1",
                )
                raise RuntimeError(
                    "Не удалось получить embeddings: запрос к OpenAI превысил таймаут. "
                    "Проверьте доступ к сети, корректность OPENAI/EMBEDDINGS_BASE_URL "
                    "и при необходимости увеличьте EMBEDDINGS_TIMEOUT_SECONDS."
                ) from exc

            if isinstance(exc, APIConnectionError):
                logger.exception(
                    "OpenAI embeddings connection error. model=%s, base_url=%s",
                    self._model,
                    self._base_url or "https://api.openai.com/v1",
                )
                raise RuntimeError(
                    "Не удалось подключиться к embeddings API. "
                    "Проверьте сеть, API endpoint и переменную OPENAI/EMBEDDINGS_BASE_URL."
                ) from exc

            raise

        return [normalize_embedding(list(item.embedding)) for item in response.data]

    async def embed_query(self, text: str) -> list[float]:
        """Для одного запроса используем тот же API и возвращаем первый результат."""

        embeddings = await self.embed_texts([text])
        return embeddings[0]
