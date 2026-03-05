from __future__ import annotations


def build_rag_user_prompt(question: str, context_chunks: list[str]) -> str:
    """
    Собирает user prompt для RAG.

    В system prompt уже лежат правила поведения бота. Здесь мы просто
    передаём вопрос пользователя и проверенные фрагменты базы знаний.
    """

    formatted_context = "\n\n".join(
        f"[Фрагмент {index}]\n{chunk.strip()}"
        for index, chunk in enumerate(context_chunks, start=1)
    )

    return (
        "Вопрос пользователя:\n"
        f"{question.strip()}\n\n"
        "Проверенные фрагменты базы знаний:\n"
        f"{formatted_context}\n\n"
        "Ответь только на основе этих фрагментов. "
        "Если в них нет точного ответа, честно скажи об этом. "
        "Не ссылайся на 'фрагменты' и 'базу знаний' в каждом предложении, "
        "пиши как живой секретарь компании."
    )
