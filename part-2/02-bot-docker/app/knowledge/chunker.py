from __future__ import annotations

from app.schemas.document import KnowledgeChunk, KnowledgeSection

MAX_CHUNK_CHARS = 1200


def chunk_sections(
    sections: list[KnowledgeSection],
    source_path: str,
    max_chunk_chars: int = MAX_CHUNK_CHARS,
) -> list[KnowledgeChunk]:
    """Turn parsed sections into chunks small enough for retrieval."""
    chunks: list[KnowledgeChunk] = []

    for section in sections:
        parts = _split_body(section.body, max_chunk_chars=max_chunk_chars)
        for chunk_index, part in enumerate(parts):
            chunks.append(
                KnowledgeChunk(
                    source_path=source_path,
                    section_slug=section.slug,
                    chunk_index=chunk_index,
                    category=section.category,
                    topic=section.topic,
                    tags=section.tags,
                    content=_compose_chunk_text(section.topic, part),
                )
            )

    return chunks


def _compose_chunk_text(topic: str | None, body: str) -> str:
    if topic:
        return f"{topic}\n\n{body.strip()}"
    return body.strip()


def _split_body(body: str, max_chunk_chars: int) -> list[str]:
    normalized_body = body.strip()
    if not normalized_body:
        return []
    if len(normalized_body) <= max_chunk_chars:
        return [normalized_body]

    paragraphs = [paragraph.strip() for paragraph in normalized_body.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        paragraph_len = len(paragraph)
        separator_len = 2 if current else 0
        if current and current_len + separator_len + paragraph_len > max_chunk_chars:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_len = paragraph_len
            continue

        current.append(paragraph)
        current_len += separator_len + paragraph_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks
