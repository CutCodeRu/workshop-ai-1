from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingsProvider(ABC):
    """Общий интерфейс для любого провайдера embeddings."""

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Строит embedding для списка текстов в том же порядке, что и вход."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Строит embedding для одного пользовательского запроса."""
