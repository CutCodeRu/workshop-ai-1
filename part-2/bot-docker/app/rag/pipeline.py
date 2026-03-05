from __future__ import annotations

from pathlib import Path

from app.config import DEFAULT_KNOWLEDGE_DIR, load_rag_settings
from app.db import connect_sync, init_db_sync
from app.db.repositories.document_chunks import replace_document_chunks, search_similar_chunks
from app.db.repositories.documents import upsert_document
from app.knowledge.chunker import chunk_sections
from app.knowledge.embedder import embed_chunks
from app.knowledge.section_parser import parse_sections
from app.knowledge.source_reader import build_checksum, read_knowledge_source, resolve_knowledge_paths
from app.providers.openai_embeddings import embed_text
from app.schemas.document import KnowledgeDocument


def load_knowledge(filepath: str | Path = DEFAULT_KNOWLEDGE_DIR) -> int:
    """Read KB files, chunk them, embed them, and store them in pgvector."""
    settings = load_rag_settings()
    init_db_sync(settings)

    knowledge_paths = resolve_knowledge_paths(filepath)
    indexed_chunks = 0

    with connect_sync(settings) as conn:
        for knowledge_path in knowledge_paths:
            document = _build_document(knowledge_path)
            document_id = upsert_document(conn, document.source_path, document.checksum)

            if document.chunks:
                embeddings = embed_chunks(document.chunks, api_key=settings.openai_api_key)
                indexed_chunks += replace_document_chunks(conn, document_id, document.chunks, embeddings)
            else:
                replace_document_chunks(conn, document_id, [], [])

        conn.commit()

    return indexed_chunks


def search(query: str, top_k: int = 3) -> list[str]:
    """Generate a query embedding and return the most similar KB chunks."""
    if top_k < 1:
        raise ValueError("top_k must be greater than 0.")

    normalized_query = query.strip()
    if not normalized_query:
        return []

    settings = load_rag_settings()
    init_db_sync(settings)
    query_embedding = embed_text(normalized_query, api_key=settings.openai_api_key)

    with connect_sync(settings) as conn:
        chunks = search_similar_chunks(conn, query_embedding, top_k=top_k)

    return [chunk.text for chunk in chunks]


def _build_document(path: Path) -> KnowledgeDocument:
    content = read_knowledge_source(path)
    sections = parse_sections(content)
    chunks = chunk_sections(sections, source_path=str(path.resolve()))
    return KnowledgeDocument(
        source_path=str(path.resolve()),
        checksum=build_checksum(content),
        chunks=tuple(chunks),
    )
