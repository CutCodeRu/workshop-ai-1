from __future__ import annotations

from openai import AsyncOpenAI

DEFAULT_CHAT_MODEL = "gpt-4o-mini"


class ChatProviderError(RuntimeError):
    """Raised when the chat provider cannot build an answer."""


async def generate_answer(
    *,
    api_key: str,
    system_prompt: str,
    context: str,
    question: str,
    model: str = DEFAULT_CHAT_MODEL,
) -> str:
    """Generate an answer from the system prompt, KB context, and user question."""
    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Контекст из базы знаний:\n"
                    f"{context}\n\n"
                    "Вопрос пользователя:\n"
                    f"{question}"
                ),
            },
        ],
    )

    content = response.choices[0].message.content if response.choices else None
    if not content:
        raise ChatProviderError("OpenAI returned an empty chat completion.")
    return content.strip()
