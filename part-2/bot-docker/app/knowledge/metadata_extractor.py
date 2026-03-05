from __future__ import annotations


def extract_metadata(lines: list[str]) -> tuple[dict[str, str], str]:
    """Extract `key: value` metadata lines that appear before the main section body."""
    metadata: dict[str, str] = {}
    body_start_index = 0

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            body_start_index = index + 1
            break
        if ":" not in stripped:
            body_start_index = index
            break
        key, value = stripped.split(":", 1)
        metadata[key.strip().lower()] = value.strip()
        body_start_index = index + 1
    else:
        body_start_index = len(lines)

    body = "\n".join(lines[body_start_index:]).strip()
    return metadata, body
