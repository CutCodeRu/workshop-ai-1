from __future__ import annotations

import asyncio

from app.config import Settings, SystemPrompt
from app.providers.openai_chat import generate_answer
from app.rag import search


async def answer_company_question(
    settings: Settings,
    system_prompt: SystemPrompt,
    question: str,
) -> str | None:
    """Answer a company-related question using RAG context and GPT."""
    chunks = await asyncio.to_thread(search, question)
    if not chunks:
        return None

    context = _build_context(chunks)
    return await generate_answer(
        api_key=settings.openai_api_key,
        system_prompt=system_prompt.content,
        context=context,
        question=question,
    )


def _build_context(chunks: list[str]) -> str:
    return "\n\n".join(
        f"Фрагмент {index}:\n{chunk}"
        for index, chunk in enumerate(chunks, start=1)
    )
