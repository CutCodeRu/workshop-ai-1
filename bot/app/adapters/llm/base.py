from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Общий интерфейс для провайдера, который умеет генерировать текстовый ответ."""

    @abstractmethod
    async def generate_answer(self, system_prompt: str, user_prompt: str) -> str:
        """Возвращает готовый ответ модели на основе system и user prompt."""
