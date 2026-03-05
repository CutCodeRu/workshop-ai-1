from __future__ import annotations

from pathlib import Path

from app.config import DEFAULT_KNOWLEDGE_DIR
from app.rag import load_knowledge


def reindex_knowledge_base(filepath: str | Path = DEFAULT_KNOWLEDGE_DIR) -> int:
    """Rebuild the KB vector index from Markdown files."""
    return load_knowledge(filepath)
