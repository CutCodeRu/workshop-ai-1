from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RetrievedChunk:
    """A KB chunk returned from vector search."""

    text: str
    score: float
    section_slug: str
    source_path: str
