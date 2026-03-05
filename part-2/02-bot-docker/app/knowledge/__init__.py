from __future__ import annotations

from importlib import import_module

__all__ = [
    "build_checksum",
    "chunk_sections",
    "embed_chunks",
    "parse_sections",
    "read_knowledge_source",
    "resolve_knowledge_paths",
]

_EXPORTS = {
    "build_checksum": ("app.knowledge.source_reader", "build_checksum"),
    "chunk_sections": ("app.knowledge.chunker", "chunk_sections"),
    "embed_chunks": ("app.knowledge.embedder", "embed_chunks"),
    "parse_sections": ("app.knowledge.section_parser", "parse_sections"),
    "read_knowledge_source": ("app.knowledge.source_reader", "read_knowledge_source"),
    "resolve_knowledge_paths": ("app.knowledge.source_reader", "resolve_knowledge_paths"),
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = _EXPORTS[name]
    module = import_module(module_name)
    return getattr(module, attribute_name)
