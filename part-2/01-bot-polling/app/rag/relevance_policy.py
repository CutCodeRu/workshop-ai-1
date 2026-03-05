from __future__ import annotations


def has_context_for_answer(context_chunks: list[str]) -> bool:
    """Считаем, что отвечать можно, только если поиск вернул хотя бы один непустой чанк."""

    return any(chunk.strip() for chunk in context_chunks)
