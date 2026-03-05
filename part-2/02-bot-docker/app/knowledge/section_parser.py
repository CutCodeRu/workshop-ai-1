from __future__ import annotations

import re

from app.knowledge.metadata_extractor import extract_metadata
from app.schemas.document import KnowledgeSection

SECTION_SEPARATOR_RE = re.compile(r"(?m)^\s*---\s*$")


def parse_sections(markdown: str) -> list[KnowledgeSection]:
    """Split the KB Markdown into logical sections separated by `---`."""
    raw_sections = [part.strip() for part in SECTION_SEPARATOR_RE.split(markdown) if part.strip()]
    parsed_sections: list[KnowledgeSection] = []

    for raw_section in raw_sections:
        lines = raw_section.splitlines()
        if not lines:
            continue

        header_index = next(
            (index for index, line in enumerate(lines) if line.strip().startswith("## ")),
            None,
        )
        if header_index is None:
            continue

        lines = lines[header_index:]
        header = lines[0].strip()
        slug = header.removeprefix("## ").strip()
        metadata, body = extract_metadata(lines[1:])
        tags = tuple(
            tag.strip()
            for tag in metadata.get("tags", "").split(",")
            if tag.strip()
        )

        parsed_sections.append(
            KnowledgeSection(
                slug=slug,
                category=metadata.get("category"),
                topic=metadata.get("topic"),
                tags=tags,
                body=body,
            )
        )

    return parsed_sections
