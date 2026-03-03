from __future__ import annotations

from pathlib import Path

import pytest

from app.rag.chunker import split_into_chunks
from app.rag.indexer import index_chunks
from app.rag.retriever import search
from app.repositories.knowledge_repository import SearchResult


class FakeEmbeddingsProvider:
    def __init__(self) -> None:
        self.texts_calls: list[list[str]] = []
        self.query_calls: list[str] = []

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.texts_calls.append(texts)
        return [[1.0, 0.0], [0.0, 1.0]]

    async def embed_query(self, text: str) -> list[float]:
        self.query_calls.append(text)
        return [0.6, 0.8]


class FakeKnowledgeRepository:
    def __init__(self) -> None:
        self.ensure_schema_called = False
        self.saved_chunks = []
        self.saved_source = None
        self.saved_checksum = None
        self.query_embedding = None
        self.query_top_k = None
        self.search_results = [
            SearchResult(
                content="Первый релевантный чанк",
                source="knowledge.md",
                chunk_index=0,
                heading="CHUNK 1",
                distance=0.10,
                similarity=0.995,
            ),
            SearchResult(
                content="Второй релевантный чанк",
                source="knowledge.md",
                chunk_index=1,
                heading="CHUNK 2",
                distance=0.22,
                similarity=0.9758,
            ),
        ]

    async def ensure_schema(self) -> None:
        self.ensure_schema_called = True

    async def replace_chunks(self, source: str, checksum: str, chunks: list) -> int:
        self.saved_source = source
        self.saved_checksum = checksum
        self.saved_chunks = chunks
        return len(chunks)

    async def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        self.query_embedding = query_embedding
        self.query_top_k = top_k
        return self.search_results[:top_k]


@pytest.mark.asyncio
async def test_index_chunks_builds_embeddings_and_passes_chunks_to_repository() -> None:
    raw_text = """
## CHUNK CC-001
Первый блок текста.

## CHUNK CC-002
Второй блок текста.
""".strip()
    chunks = split_into_chunks(raw_text, source="knowledge.md")
    embeddings_provider = FakeEmbeddingsProvider()
    repository = FakeKnowledgeRepository()

    stored_count = await index_chunks(
        chunks=chunks,
        raw_text=raw_text,
        embeddings_provider=embeddings_provider,
        repository=repository,
    )

    assert stored_count == 2
    assert embeddings_provider.texts_calls == [[chunk.content for chunk in chunks]]
    assert repository.saved_source == "knowledge.md"
    assert repository.saved_checksum
    assert [chunk.chunk_index for chunk in repository.saved_chunks] == [0, 1]


def test_split_into_chunks_uses_explicit_chunk_delimiters_from_knowledge_file() -> None:
    knowledge_path = Path(__file__).resolve().parents[1] / "knowledge.md"
    raw_text = knowledge_path.read_text(encoding="utf-8")

    chunks = split_into_chunks(raw_text, source=str(knowledge_path))

    assert len(chunks) == 15
    assert chunks[0].heading == "CHUNK CC-001"
    assert "веб-студия полного цикла" in chunks[0].content
    assert chunks[-1].chunk_index == 14


@pytest.mark.asyncio
async def test_search_returns_only_chunk_texts(monkeypatch) -> None:
    provider = FakeEmbeddingsProvider()
    repository = FakeKnowledgeRepository()

    class FakePool:
        async def close(self) -> None:
            return None

    async def fake_create_connection_pool() -> FakePool:
        return FakePool()

    monkeypatch.setattr("app.rag.retriever.create_connection_pool", fake_create_connection_pool)
    monkeypatch.setattr(
        "app.rag.retriever.KnowledgeRepository",
        lambda _pool: repository,
    )

    texts = await search(
        "Сколько стоит корпоративный сайт?",
        top_k=2,
        embeddings_provider=provider,
    )

    assert provider.query_calls == ["Сколько стоит корпоративный сайт?"]
    assert repository.ensure_schema_called is True
    assert repository.query_embedding == [0.6, 0.8]
    assert repository.query_top_k == 2
    assert texts == [
        "Первый релевантный чанк",
        "Второй релевантный чанк",
    ]
