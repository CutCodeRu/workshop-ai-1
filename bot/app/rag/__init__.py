from __future__ import annotations


async def load_knowledge(*args, **kwargs):
    """Ленивый экспорт, чтобы пакет app.rag импортировался без лишних зависимостей."""

    from .knowledge_loader import load_knowledge as _load_knowledge

    return await _load_knowledge(*args, **kwargs)


async def search(*args, **kwargs):
    """Ленивый экспорт, чтобы пакет app.rag импортировался без лишних зависимостей."""

    from .retriever import search as _search

    return await _search(*args, **kwargs)

__all__ = ["load_knowledge", "search"]
