from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class KnowledgeSection:
    """A single logical KB section parsed from Markdown."""

    slug: str
    category: str | None
    topic: str | None
    tags: tuple[str, ...]
    body: str


@dataclass(slots=True, frozen=True)
class KnowledgeChunk:
    """A searchable chunk ready for embedding and storage."""

    source_path: str
    section_slug: str
    chunk_index: int
    category: str | None
    topic: str | None
    tags: tuple[str, ...]
    content: str


@dataclass(slots=True, frozen=True)
class KnowledgeDocument:
    """A parsed KB document with its chunk payload."""

    source_path: str
    checksum: str
    chunks: tuple[KnowledgeChunk, ...]
