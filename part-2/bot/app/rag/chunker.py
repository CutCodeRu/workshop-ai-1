from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class ChunkDraft:
    """Чанк до стадии построения embeddings и записи в БД."""

    content: str
    source: str
    chunk_index: int
    heading: str | None


def _extract_heading(section_text: str) -> str | None:
    """Берём первую markdown-строку-заголовок, если она есть."""

    for line in section_text.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("#"):
            return stripped_line.lstrip("#").strip() or None
    return None


def _split_by_positions(text: str, matches: list[re.Match[str]]) -> list[str]:
    """Разрезает исходный текст по найденным позициям начала секций."""

    sections: list[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        candidate = text[start:end].strip()
        if candidate:
            sections.append(candidate)
    return sections


def split_into_chunks(text: str, source: str) -> list[ChunkDraft]:
    """
    Делит markdown-документ на логические чанки.

    Порядок стратегий такой:
    1. Явные маркеры `## CHUNK ...` из knowledge.md.
    2. Горизонтальные разделители `---`.
    3. Заголовки второго уровня `##`.
    4. Если ничего не нашли, возвращаем документ целиком одним чанком.
    """

    normalized_text = text.replace("\r\n", "\n").strip()
    if not normalized_text:
        return []

    chunk_heading_matches = list(
        re.finditer(r"(?m)^##\s+CHUNK\b.*$", normalized_text)
    )
    if chunk_heading_matches:
        sections = _split_by_positions(normalized_text, chunk_heading_matches)
    elif re.search(r"(?m)^---+\s*$", normalized_text):
        sections = [
            section.strip()
            for section in re.split(r"(?m)^---+\s*$", normalized_text)
            if section.strip()
        ]
    else:
        second_level_heading_matches = list(
            re.finditer(r"(?m)^##\s+.+$", normalized_text)
        )
        if second_level_heading_matches:
            sections = _split_by_positions(normalized_text, second_level_heading_matches)
        else:
            sections = [normalized_text]

    return [
        ChunkDraft(
            content=section,
            source=source,
            chunk_index=index,
            heading=_extract_heading(section),
        )
        for index, section in enumerate(sections)
    ]
