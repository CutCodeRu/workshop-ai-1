from __future__ import annotations

import logging

from app.adapters.llm.base import LLMProvider
from app.adapters.llm.openai_adapter import OpenAILLMAdapter
from app.config import get_settings
from app.rag.direct_answer_resolver import build_extract_fallback
from app.rag.prompt_builder import build_rag_user_prompt
from app.rag.relevance_policy import has_context_for_answer
from app.rag.retriever import search

logger = logging.getLogger(__name__)


def _build_default_llm_provider() -> LLMProvider | None:
    """
    Собирает LLM-провайдер из настроек.

    Если LLM-ключ не задан, возвращаем None и ниже используем простой
    extractive fallback без генерации.
    """

    settings = get_settings()
    if not settings.llm_api_key:
        logger.warning("LLM_API_KEY / OPENAI_API_KEY не задан, используем fallback без LLM.")
        return None

    return OpenAILLMAdapter(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )


async def generate_answer(
    question: str,
    system_prompt: str,
    *,
    llm_provider: LLMProvider | None = None,
) -> str:
    """
    Главная точка входа для ответа на вопрос пользователя.

    Pipeline:
    1. достаём релевантные чанки из базы знаний;
    2. если ничего не нашли, честно говорим об отсутствии данных;
    3. если LLM настроена, просим её собрать короткий ответ по найденному контексту;
    4. если LLM недоступна, возвращаем лучший найденный фрагмент как fallback.
    """

    settings = get_settings()
    context_chunks = await search(question, top_k=settings.rag_top_k)

    if not has_context_for_answer(context_chunks):
        logger.info("Для вопроса %r не найдено ни одного контекстного чанка.", question)
        return (
            "У меня нет точной информации по этому вопросу в базе знаний компании. "
            "Если хотите, могу помочь оставить заявку для связи."
        )

    provider = llm_provider if llm_provider is not None else _build_default_llm_provider()
    if provider is None:
        return build_extract_fallback(context_chunks)

    user_prompt = build_rag_user_prompt(question, context_chunks)
    try:
        answer = await provider.generate_answer(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    except Exception:
        logger.exception("Не удалось сгенерировать ответ через LLM, используем fallback.")
        return build_extract_fallback(context_chunks)

    if not answer.strip():
        logger.warning("LLM вернула пустой ответ, используем fallback.")
        return build_extract_fallback(context_chunks)

    return answer.strip()
