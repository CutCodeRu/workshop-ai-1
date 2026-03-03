from __future__ import annotations

import logging

from .base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAILLMAdapter(LLMProvider):
    """Обёртка над OpenAI Chat Completions API для генерации ответа бота."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
    ) -> None:
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

    async def generate_answer(self, system_prompt: str, user_prompt: str) -> str:
        """Генерирует ответ модели в коротком и предсказуемом режиме."""

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            from openai import APIConnectionError, APITimeoutError

            if isinstance(exc, APITimeoutError):
                logger.exception(
                    "LLM timeout. model=%s, timeout=%s, base_url=%s",
                    self._model,
                    self._timeout_seconds,
                    self._base_url or "https://api.openai.com/v1",
                )
                raise RuntimeError(
                    "Не удалось получить ответ от LLM: запрос превысил таймаут."
                ) from exc

            if isinstance(exc, APIConnectionError):
                logger.exception(
                    "LLM connection error. model=%s, base_url=%s",
                    self._model,
                    self._base_url or "https://api.openai.com/v1",
                )
                raise RuntimeError(
                    "Не удалось подключиться к LLM API. Проверьте сеть и LLM_BASE_URL."
                ) from exc

            raise

        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("LLM вернула пустой ответ.")

        return content.strip()
