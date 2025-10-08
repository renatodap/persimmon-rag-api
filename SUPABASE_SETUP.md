# 🗄️ Supabase Database Setup - Add RAG API Tables

**Add Persimmon RAG API tables to your EXISTING Supabase database.**

Your current database has business/brand kit tables. This migration will ADD the RAG API tables without affecting your existing schema.

---

## 📊 Schema Analysis

### ✅ Your Existing Tables (Will NOT be modified)
- `brand_kits`
- `business_access_requests`
- `business_collections`
- `business_invitations`
- `business_knowledge_cache`
- `business_members`
- `businesses`
- `recall_api_keys`
- `share_tokens`

### 🆕 Tables to be ADDED by Migration
- `sources` - Knowledge sources (URLs, PDFs, text, notes)
- `summaries` - AI-generated summaries with vector embeddings
- `collections` - Organize sources (RAG collections, different from business_collections)
- `collection_sources` - Link sources to collections
- `tags` - Tag/categorize sources
- `webhooks` - Real-time event notifications

**No conflicts!** All new tables have unique names and won't affect your existing schema.

---

## 🚀 Step-by-Step Migration

### Step 1: Access Supabase SQL Editor

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project: `ptdphysuhuqplisuhnqa`
3. Click **"SQL Editor"** in left sidebar
4. Click **"New Query"**

### Step 2: Enable pgvector Extension

**Run this FIRST** (required for vector embeddings):

```sql
-- Enable pgvector for semantic search
CREATE EXTENSION IF NOT EXISTS vector;
```

Click **"Run"** (bottom right corner)

Expected output: `Success. No rows returned`

### Step 3: Run the Complete Migration

1. Open the file: `migrations/000_initial_schema.sql` in this repository
2. Copy the **ENTIRE** SQL content (all ~600 lines)
3. In Supabase SQL Editor, click **"New Query"**
4. Paste the SQL content
5. Click **"Run"**

**This will take ~10-15 seconds.**

Expected output: Multiple success messages ending with:
```
NOTICE:  Persimmon RAG API Database Schema - Installation Complete!
NOTICE:  Tables created: sources, summaries, collections, collection_sources, tags, webhooks
...
```

### Step 4: Verify Installation

Run this query to verify all tables exist:

```sql
-- Verify RAG API tables exist
SELECT
    tablename,
    rowsecurity as "RLS Enabled"
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('sources', 'summaries', 'collections', 'collection_sources', 'tags', 'webhooks')
ORDER BY tablename;
```

**Expected result:** 6 rows with `RLS Enabled = true`

```
tablename          | RLS Enabled
-------------------+-------------
collection_sources | true
collections        | true
sources            | true
summaries          | true
tags               | true
webhooks           | true
```

### Step 5: Test Vector Search Function

Run this test query:

```sql
-- Test vector search function
SELECT * FROM match_summaries(
    query_embedding := array_fill(0, ARRAY[768])::vector(768),
    match_threshold := 0.5,
    match_count := 5
);
```

**Expected result:** Empty result set (no errors)

If you get an error about `vector` type not existing, go back to Step 2 and enable pgvector.

---

## ✅ Migration Complete Checklist

- [ ] pgvector extension enabled
- [ ] Migration script ran successfully
- [ ] All 6 RAG tables exist
- [ ] RLS is enabled on all tables
- [ ] Vector search function works
- [ ] No errors in Supabase logs

---

## 🔍 What Was Created?

### **Tables:**

**1. sources** - Main knowledge source table
- Stores URLs, PDFs, text, notes
- Links to auth.users (user_id)
- RLS: Users can only access their own sources

**2. summaries** - AI-generated summaries
- One summary per source (1:1 relationship)
- Contains vector embeddings (768 dimensions for Gemini/OpenAI)
- Stores key_actions and key_topics arrays
- RLS: Users access summaries through source ownership

**3. collections** - Organize sources into groups
- User-defined collections (e.g., "Machine Learning Papers", "Marketing Materials")
- Different from your `business_collections` table
- RLS: Users can only access their own collections

**4. collection_sources** - Many-to-many link
- Links sources to collections
- One source can be in multiple collections
- RLS: Users access through collection ownership

**5. tags** - Flexible tagging system
- Tag sources with topics/keywords
- Supports search and filtering
- RLS: Users access through source ownership

**6. webhooks** - Real-time event notifications
- Subscribe to events (source.created, source.updated, etc.)
- HMAC-SHA256 signature verification
- RLS: Users can only manage their own webhooks

### **Functions:**

**match_summaries()** - Vector similarity search
- Performs semantic search using cosine similarity
- Supports collection filtering
- Configurable similarity threshold
- Returns top N most relevant results

### **Indexes:**

- **Vector indexes:** IVFFLAT for fast similarity search
- **Text indexes:** GIN indexes for full-text search
- **Foreign key indexes:** For joins and relationships
- **Composite indexes:** For common query patterns

### **RLS Policies:**

All tables have Row-Level Security enabled:
- SELECT: Users can view their own data
- INSERT: Users can create their own data
- UPDATE: Users can modify their own data
- DELETE: Users can delete their own data

Service role key bypasses RLS (used by FastAPI backend).

---

## 🔗 Integration with Existing Schema

### **How RAG API Integrates with Your Business Schema:**

**Option 1: Separate per-user knowledge base**
- Each user has their own sources/collections
- Business members share knowledge through business_collections
- Use business_collections to link to RAG collections

**Option 2: Business-level knowledge base**
- Store business_id in sources table (requires schema modification)
- Share knowledge across business members
- Requires custom RLS policies

**Current setup:** Option 1 (per-user, recommended for start)

**To upgrade to business-level sharing later:**
```sql
-- Add business_id to sources (optional future enhancement)
ALTER TABLE sources ADD COLUMN business_id uuid REFERENCES businesses(id);
CREATE INDEX idx_sources_business_id ON sources(business_id);

-- Update RLS to allow business members access
CREATE POLICY "Business members can view business sources" ON sources
FOR SELECT USING (
    business_id IS NOT NULL AND
    EXISTS (
        SELECT 1 FROM business_members
        WHERE business_members.business_id = sources.business_id
        AND business_members.user_id = auth.uid()
    )
);
```

---

## 🧪 Test the Migration

### Test 1: Create a Test Source

```sql
-- Insert test source (replace user_id with real user from auth.users)
INSERT INTO sources (user_id, title, content_type, original_content)
VALUES (
    'YOUR_USER_ID_HERE',  -- Get from auth.users table
    'Test Article',
    'text',
    'This is a test article about machine learning and AI.'
)
RETURNING *;
```

### Test 2: Create Test Summary with Embedding

```sql
-- Insert test summary (replace source_id with result from Test 1)
INSERT INTO summaries (
    source_id,
    summary_text,
    key_actions,
    key_topics,
    word_count,
    embedding
)
VALUES (
    'SOURCE_ID_FROM_TEST_1',
    'Test article about ML and AI',
    ARRAY['Learn ML', 'Explore AI'],
    ARRAY['machine learning', 'artificial intelligence'],
    10,
    array_fill(0.1, ARRAY[768])::vector(768)  -- Dummy embedding
)
RETURNING *;
```

### Test 3: Search with Vector Similarity

```sql
-- Search for similar content
SELECT
    s.title,
    sm.summary_text,
    sm.key_topics,
    1 - (sm.embedding <=> array_fill(0.1, ARRAY[768])::vector(768)) as similarity
FROM summaries sm
JOIN sources s ON sm.source_id = s.id
ORDER BY sm.embedding <=> array_fill(0.1, ARRAY[768])::vector(768)
LIMIT 5;
```

### Test 4: Verify RLS Works

```sql
-- This should return empty if querying as different user
SET request.jwt.claims.sub = 'different-user-id';
SELECT * FROM sources;  -- Should be empty or only show that user's sources
```

---

## 🚨 Troubleshooting

### Error: "type 'vector' does not exist"
**Solution:** Run Step 2 to enable pgvector extension

### Error: "permission denied"
**Solution:** Make sure you're using the SQL Editor in Supabase dashboard (auto-authenticated)

### Error: "relation 'auth.users' does not exist"
**Solution:** This shouldn't happen in Supabase. Verify you're in the correct project.

### Migration runs but tables don't appear
**Solution:** Refresh the Supabase dashboard, check "Table Editor" sidebar

### RLS policies blocking queries
**Solution:** Use service_role key in API (already configured in .env)

---

## 📝 Next Steps After Migration

1. **Test the API locally:**
   ```bash
   poetry run python scripts/validate_env.py  # Verify all keys are set
   poetry run uvicorn app.main:app --reload   # Start API
   curl http://localhost:8000/health          # Test health check
   ```

2. **Deploy to Railway:**
   ```bash
   railway up
   ```

3. **Verify production database:**
   - API will use same Supabase database
   - Test creating sources via API
   - Test semantic search

4. **Monitor API costs:**
   - Gemini embeddings: FREE (1500/day)
   - OpenAI fallback: ~$0.02/1M tokens
   - Claude summaries: ~$3-15/1M tokens

---

## 🎯 Summary

**What you did:**
1. ✅ Enabled pgvector extension
2. ✅ Added 6 new RAG API tables
3. ✅ Created vector search function
4. ✅ Set up RLS policies for security
5. ✅ Created indexes for performance

**What's next:**
1. Test API locally with new database
2. Deploy to Railway
3. Integrate with your business schema (optional)
4. Start using RAG features!

**Your database now supports:**
- ✅ Semantic search with vector embeddings
- ✅ AI-powered summarization
- ✅ Knowledge source management
- ✅ Real-time webhooks
- ✅ Multi-user with RLS

---

**Questions or issues?** Check the troubleshooting section or review Supabase logs in dashboard.
