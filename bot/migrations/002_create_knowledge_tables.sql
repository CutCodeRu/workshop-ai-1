CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    source TEXT,
    chunk_index INTEGER,
    heading TEXT,
    checksum TEXT,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE knowledge_chunks
    ADD COLUMN IF NOT EXISTS heading TEXT;

ALTER TABLE knowledge_chunks
    ADD COLUMN IF NOT EXISTS checksum TEXT;

ALTER TABLE knowledge_chunks
    ADD COLUMN IF NOT EXISTS embedding vector(1536);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source_chunk_index
    ON knowledge_chunks (source, chunk_index);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source_checksum
    ON knowledge_chunks (source, checksum);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_l2
    ON knowledge_chunks
    USING ivfflat (embedding vector_l2_ops)
    WITH (lists = 100);
