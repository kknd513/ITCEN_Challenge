-- CENOps Copilot Railway Prototype Schema
-- PostgreSQL + pgvector 권장. Railway 표준 Postgres에는 pgvector가 없을 수 있으므로 pgvector 템플릿 또는 확장 가능 이미지를 사용한다.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'central-rag-document',
    target_server TEXT,
    file_path TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    target_server TEXT,
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_target_server ON document_chunks(target_server);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS server_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_key TEXT NOT NULL UNIQUE,
    host_alias TEXT NOT NULL,
    role TEXT NOT NULL,
    agent_url TEXT,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO server_agents (server_key, host_alias, role)
VALUES
    ('A', 'WEB-01', 'WEB'),
    ('B', 'WAS-01', 'WAS'),
    ('C', 'DB-01', 'DB')
ON CONFLICT (server_key) DO NOTHING;

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY,
    input_text TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id BIGSERIAL PRIMARY KEY,
    incident_id UUID,
    server_key TEXT,
    agent_name TEXT,
    role TEXT,
    status TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id BIGSERIAL PRIMARY KEY,
    incident_id UUID,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY,
    incident_id UUID,
    title TEXT NOT NULL,
    markdown TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
