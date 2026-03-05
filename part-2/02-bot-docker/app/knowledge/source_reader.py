from __future__ import annotations

import hashlib
from pathlib import Path

SKIPPED_FILENAMES = {"kb_template.md"}


def resolve_knowledge_paths(filepath: str | Path) -> list[Path]:
    """Resolve a file or directory path into a sorted list of KB Markdown files."""
    root = Path(filepath)
    if root.is_file():
        return [root]
    if not root.exists():
        raise FileNotFoundError(f"Knowledge path does not exist: {root}")
    return sorted(
        path
        for path in root.glob("*.md")
        if path.is_file() and path.name not in SKIPPED_FILENAMES
    )


def read_knowledge_source(path: str | Path) -> str:
    """Read UTF-8 Markdown content from disk."""
    return Path(path).read_text(encoding="utf-8").strip()


def build_checksum(content: str) -> str:
    """Create a stable content checksum used for reindexing."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
