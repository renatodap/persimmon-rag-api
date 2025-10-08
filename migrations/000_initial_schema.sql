-- =====================================================
-- PERSIMMON RAG API - COMPLETE DATABASE SCHEMA
-- =====================================================
-- This migration creates the complete database schema for the Persimmon RAG API
-- Includes: tables, RLS policies, indexes, functions, and triggers
-- =====================================================

-- =====================================================
-- STEP 1: Enable Required Extensions
-- =====================================================

-- Enable pgvector for vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- STEP 2: Create Tables
-- =====================================================

-- Sources table: Stores knowledge sources (URLs, PDFs, text, notes)
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN ('url', 'pdf', 'text', 'note')),
    original_content TEXT NOT NULL,
    url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Summaries table: Stores AI-generated summaries with vector embeddings
CREATE TABLE IF NOT EXISTS summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    key_actions TEXT[] DEFAULT '{}',
    key_topics TEXT[] DEFAULT '{}',
    word_count INTEGER DEFAULT 0,
    embedding vector(768),  -- Google Gemini/OpenAI embedding dimension
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_id)  -- One summary per source
);

-- Collections table: Organizes sources into groups
CREATE TABLE IF NOT EXISTS collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, name)  -- Unique collection names per user
);

-- Collection_sources table: Many-to-many relationship between collections and sources
CREATE TABLE IF NOT EXISTS collection_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(collection_id, source_id)  -- Prevent duplicate entries
);

-- Tags table: Categorizes sources with topics/tags
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    tag_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_id, tag_name)  -- Prevent duplicate tags per source
);

-- Webhooks table: Stores webhook configurations for real-time event notifications
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,
    secret TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- STEP 3: Create Indexes for Performance
-- =====================================================

-- Sources indexes
CREATE INDEX IF NOT EXISTS idx_sources_user_id ON sources(user_id);
CREATE INDEX IF NOT EXISTS idx_sources_content_type ON sources(content_type);
CREATE INDEX IF NOT EXISTS idx_sources_created_at ON sources(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sources_title_search ON sources USING GIN(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_sources_content_search ON sources USING GIN(to_tsvector('english', original_content));

-- Summaries indexes
CREATE INDEX IF NOT EXISTS idx_summaries_source_id ON summaries(source_id);
CREATE INDEX IF NOT EXISTS idx_summaries_embedding_cosine ON summaries USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- Alternative index for better performance (requires data to train)
-- CREATE INDEX IF NOT EXISTS idx_summaries_embedding_hnsw ON summaries USING hnsw (embedding vector_cosine_ops);

-- Collections indexes
CREATE INDEX IF NOT EXISTS idx_collections_user_id ON collections(user_id);
CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(name);

-- Collection_sources indexes
CREATE INDEX IF NOT EXISTS idx_collection_sources_collection_id ON collection_sources(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_sources_source_id ON collection_sources(source_id);

-- Tags indexes
CREATE INDEX IF NOT EXISTS idx_tags_source_id ON tags(source_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag_name ON tags(tag_name);
CREATE INDEX IF NOT EXISTS idx_tags_name_search ON tags USING GIN(to_tsvector('english', tag_name));

-- Webhooks indexes
CREATE INDEX IF NOT EXISTS idx_webhooks_user_id ON webhooks(user_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_is_active ON webhooks(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_webhooks_events ON webhooks USING GIN(events);

-- =====================================================
-- STEP 4: Enable Row-Level Security (RLS)
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- STEP 5: Create RLS Policies
-- =====================================================

-- Sources policies
CREATE POLICY "Users can view own sources" ON sources
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sources" ON sources
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sources" ON sources
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sources" ON sources
    FOR DELETE USING (auth.uid() = user_id);

-- Summaries policies
CREATE POLICY "Users can view own summaries" ON summaries
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM sources
            WHERE sources.id = summaries.source_id
            AND sources.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own summaries" ON summaries
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM sources
            WHERE sources.id = summaries.source_id
            AND sources.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own summaries" ON summaries
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM sources
            WHERE sources.id = summaries.source_id
            AND sources.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own summaries" ON summaries
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM sources
            WHERE sources.id = summaries.source_id
            AND sources.user_id = auth.uid()
        )
    );

-- Collections policies
CREATE POLICY "Users can view own collections" ON collections
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own collections" ON collections
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own collections" ON collections
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own collections" ON collections
    FOR DELETE USING (auth.uid() = user_id);

-- Collection_sources policies
CREATE POLICY "Users can view own collection_sources" ON collection_sources
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM collections
            WHERE collections.id = collection_sources.collection_id
            AND collections.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own collection_sources" ON collection_sources
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM collections
            WHERE collections.id = collection_sources.collection_id
            AND collections.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own collection_sources" ON collection_sources
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM collections
            WHERE collections.id = collection_sources.collection_id
            AND collections.user_id = auth.uid()
        )
    );

-- Tags policies
CREATE POLICY "Users can view own tags" ON tags
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM sources
            WHERE sources.id = tags.source_id
            AND sources.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own tags" ON tags
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM sources
            WHERE sources.id = tags.source_id
            AND sources.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own tags" ON tags
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM sources
            WHERE sources.id = tags.source_id
            AND sources.user_id = auth.uid()
        )
    );

-- Webhooks policies
CREATE POLICY "Users can view own webhooks" ON webhooks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own webhooks" ON webhooks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own webhooks" ON webhooks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own webhooks" ON webhooks
    FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- STEP 6: Create Functions
-- =====================================================

-- Function: Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function: Vector similarity search for summaries
CREATE OR REPLACE FUNCTION match_summaries(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10,
    p_user_id uuid DEFAULT NULL,
    p_collection_id uuid DEFAULT NULL
)
RETURNS TABLE (
    source_id uuid,
    summary_id uuid,
    user_id uuid,
    title text,
    content_type text,
    original_content text,
    url text,
    summary_text text,
    key_actions text[],
    key_topics text[],
    word_count integer,
    similarity float,
    created_at timestamptz,
    updated_at timestamptz,
    summary_created_at timestamptz
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id AS source_id,
        sm.id AS summary_id,
        s.user_id,
        s.title,
        s.content_type,
        s.original_content,
        s.url,
        sm.summary_text,
        sm.key_actions,
        sm.key_topics,
        sm.word_count,
        1 - (sm.embedding <=> query_embedding) AS similarity,
        s.created_at,
        s.updated_at,
        sm.created_at AS summary_created_at
    FROM summaries sm
    JOIN sources s ON sm.source_id = s.id
    LEFT JOIN collection_sources cs ON s.id = cs.source_id
    WHERE
        (p_user_id IS NULL OR s.user_id = p_user_id)
        AND (p_collection_id IS NULL OR cs.collection_id = p_collection_id)
        AND (1 - (sm.embedding <=> query_embedding)) > match_threshold
    ORDER BY sm.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- =====================================================
-- STEP 7: Create Triggers
-- =====================================================

-- Trigger: Auto-update updated_at on sources
CREATE TRIGGER update_sources_updated_at
    BEFORE UPDATE ON sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto-update updated_at on summaries
CREATE TRIGGER update_summaries_updated_at
    BEFORE UPDATE ON summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto-update updated_at on collections
CREATE TRIGGER update_collections_updated_at
    BEFORE UPDATE ON collections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto-update updated_at on webhooks
CREATE TRIGGER update_webhooks_updated_at
    BEFORE UPDATE ON webhooks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- STEP 8: Add Table Comments
-- =====================================================

COMMENT ON TABLE sources IS 'Stores knowledge sources (URLs, PDFs, text, notes) with metadata';
COMMENT ON TABLE summaries IS 'Stores AI-generated summaries with vector embeddings for semantic search';
COMMENT ON TABLE collections IS 'Organizes sources into named collections for categorization';
COMMENT ON TABLE collection_sources IS 'Many-to-many relationship between collections and sources';
COMMENT ON TABLE tags IS 'Stores tags/topics for source categorization';
COMMENT ON TABLE webhooks IS 'Stores webhook configurations for real-time event notifications';

COMMENT ON COLUMN sources.content_type IS 'Type of content: url, pdf, text, or note';
COMMENT ON COLUMN summaries.embedding IS 'Vector embedding (768 dimensions) for semantic search';
COMMENT ON COLUMN summaries.key_actions IS 'Array of actionable items extracted from content';
COMMENT ON COLUMN summaries.key_topics IS 'Array of key topics/themes from content';
COMMENT ON COLUMN webhooks.events IS 'Array of subscribed event types (e.g., source.created)';
COMMENT ON COLUMN webhooks.secret IS 'Optional secret for HMAC signature verification';
COMMENT ON COLUMN webhooks.is_active IS 'Whether webhook is active (can be disabled without deletion)';

-- =====================================================
-- STEP 9: Grant Permissions (if needed)
-- =====================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO anon;

-- Grant access to tables for authenticated users
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

-- Verify installation
DO $$
BEGIN
    RAISE NOTICE 'Persimmon RAG API Database Schema - Installation Complete!';
    RAISE NOTICE 'Tables created: sources, summaries, collections, collection_sources, tags, webhooks';
    RAISE NOTICE 'RLS policies: Enabled on all tables';
    RAISE NOTICE 'Indexes: Created for performance optimization';
    RAISE NOTICE 'Functions: match_summaries() for vector search';
    RAISE NOTICE 'Extensions: pgvector enabled';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Verify pgvector extension is enabled';
    RAISE NOTICE '2. Test vector search with match_summaries()';
    RAISE NOTICE '3. Configure API with SUPABASE_URL and keys';
    RAISE NOTICE '4. Deploy API to Railway';
END $$;
