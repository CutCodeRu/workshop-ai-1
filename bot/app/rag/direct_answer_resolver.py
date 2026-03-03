from __future__ import annotations


def _cleanup_chunk_text(chunk_text: str) -> str:
    """Убирает из чанка служебные markdown-строки, которые не нужны пользователю."""

    cleaned_lines: list[str] = []
    for line in chunk_text.splitlines():
        stripped_line = line.strip()

        if not stripped_line:
            cleaned_lines.append("")
            continue

        if stripped_line.startswith("#"):
            continue

        if stripped_line.startswith("- ") and ":" in stripped_line:
            continue

        cleaned_lines.append(stripped_line)

    cleaned_text = "\n".join(cleaned_lines).strip()
    return cleaned_text or chunk_text.strip()


def build_extract_fallback(context_chunks: list[str]) -> str:
    """
    Делает простой ответ без LLM.

    Это запасной вариант на случай, если LLM не настроена или временно недоступна.
    Мы не пытаемся красиво пересказать всё содержимое, а аккуратно возвращаем
    самый релевантный текст из базы знаний.
    """

    if not context_chunks:
        return (
            "У меня нет точной информации по этому вопросу в базе знаний компании. "
            "Если хотите, могу помочь оставить заявку для связи."
        )

    best_chunk = _cleanup_chunk_text(context_chunks[0])
    return best_chunk
