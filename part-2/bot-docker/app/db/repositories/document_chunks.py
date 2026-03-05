from __future__ import annotations

from collections.abc import Sequence

from psycopg import Connection

from app.schemas.document import KnowledgeChunk
from app.schemas.retrieval import RetrievedChunk


def replace_document_chunks(
    conn: Connection,
    document_id: int,
    chunks: Sequence[KnowledgeChunk],
    embeddings: Sequence[Sequence[float]],
) -> int:
    """Replace all chunks for a document with a newly indexed set."""
    if len(chunks) != len(embeddings):
        raise ValueError("Chunks and embeddings must have the same length.")

    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM document_chunks WHERE document_id = %s;", (document_id,))
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            cursor.execute(
                """
                INSERT INTO document_chunks (
                    document_id,
                    section_slug,
                    chunk_index,
                    category,
                    topic,
                    tags,
                    content,
                    embedding
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector(1536));
                """,
                (
                    document_id,
                    chunk.section_slug,
                    chunk.chunk_index,
                    chunk.category,
                    chunk.topic,
                    list(chunk.tags),
                    chunk.content,
                    _vector_literal(embedding),
                ),
            )

    return len(chunks)


def search_similar_chunks(
    conn: Connection,
    query_embedding: Sequence[float],
    top_k: int,
) -> list[RetrievedChunk]:
    """Search KB chunks by cosine distance in pgvector."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                content,
                embedding <=> %s::vector(1536) AS score,
                section_slug,
                documents.source_path
            FROM document_chunks
            JOIN documents ON documents.id = document_chunks.document_id
            ORDER BY embedding <=> %s::vector(1536), document_chunks.id
            LIMIT %s;
            """,
            (_vector_literal(query_embedding), _vector_literal(query_embedding), top_k),
        )
        rows = cursor.fetchall()

    return [
        RetrievedChunk(
            text=row[0],
            score=float(row[1]),
            section_slug=row[2],
            source_path=row[3],
        )
        for row in rows
    ]


def _vector_literal(values: Sequence[float]) -> str:
    return "[" + ",".join(f"{value:.12f}" for value in values) + "]"
