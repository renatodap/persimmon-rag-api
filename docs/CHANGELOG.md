# Changelog

All notable changes to the Recall Notebook API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-10

### Added

**Batch Operations:**
- `POST /api/v1/embeddings/batch` - Generate embeddings for up to 100 texts in parallel
  - Processes items independently with individual success/failure tracking
  - Returns statistics: total, successful, failed counts
  - Uses FREE Gemini with OpenAI fallback for each item
- `POST /api/v1/sources/batch` - Create up to 50 sources in batch
  - Auto-generates titles where missing
  - Creates embeddings and tags for each source
  - Returns per-item success/failure results

**Webhooks:**
- `POST /api/v1/webhooks` - Register webhook for real-time event notifications
  - Events: source.created, source.updated, source.deleted, search.completed, collection.created, collection.updated
  - HMAC-SHA256 signature verification
  - Optional custom secret per webhook
- `GET /api/v1/webhooks` - List user's webhooks
- `DELETE /api/v1/webhooks/{id}` - Delete webhook
- `POST /api/v1/webhooks/test` - Test webhook delivery
  - Returns status code and response time
  - Validates endpoint connectivity

**Models:**
- `BatchEmbeddingItem` - Single item in batch embedding request
- `BatchGenerateEmbeddingRequest` - Batch embeddings input (max 100 items)
- `BatchGenerateEmbeddingResponse` - Batch results with statistics
- `BatchSourceItem` - Single item in batch source creation
- `BatchCreateSourcesRequest` - Batch sources input (max 50 items)
- `BatchCreateSourcesResponse` - Batch results with statistics
- `CreateWebhookRequest` - Webhook registration
- `WebhookResponse` - Webhook data
- `WebhookPayload` - Event payload structure
- `TestWebhookRequest/Response` - Webhook testing

**Configuration:**
- `WEBHOOK_SECRET` - Environment variable for signing webhook payloads
  - Default: "default-webhook-secret-change-in-production"
  - Should be set to secure random string in production

**Database:**
- `webhooks` table with RLS policies
  - Stores webhook configurations (URL, events, secret)
  - Indexed by user_id, is_active, and events (GIN index)
  - Auto-updates updated_at timestamp

**Services:**
- `EmbeddingService.generate_batch_embeddings()` - Parallel embedding generation
- `EmbeddingService._generate_single_with_error_handling()` - Error handling per item
- `WebhookService` - Complete webhook management
  - `register_webhook()` - Store webhook configuration
  - `trigger_webhook()` - Deliver event notifications
  - `test_webhook()` - Test endpoint connectivity
  - `_deliver_webhook()` - Retry logic with exponential backoff (3 attempts)
  - `_generate_signature()` - HMAC-SHA256 payload signing
  - `verify_signature()` - Signature verification for incoming webhooks

**Documentation:**
- `CHANGELOG.md` - API version history
- Updated `AGENT_API_GUIDE.md` with batch operations examples
- Updated `README.md` with new features

### Changed
- API version updated to 1.1.0
- Rate limiting applied to batch operations (same limits as individual operations)

### Fixed
- (none)

### Security
- Webhook payloads signed with HMAC-SHA256
- Webhook URLs validated (must start with http:// or https://)
- Webhook delivery timeout: 5 seconds
- Row-level security enforced on webhooks table

---

## [1.0.0] - 2025-01-08

### Added

**Initial API Release:**

**Core Features:**
- `POST /api/v1/sources` - Create source with AI summary
- `GET /api/v1/sources` - List sources (paginated, filtered)
- `GET /api/v1/sources/{id}` - Get single source
- `PATCH /api/v1/sources/{id}` - Update source
- `DELETE /api/v1/sources/{id}` - Delete source
- `POST /api/v1/fetch-url` - Fetch and extract URL content
- `POST /api/v1/process-pdf` - Extract text from PDF
- `POST /api/v1/summarize` - Generate AI summary

**Collections:**
- `POST /api/v1/collections` - Create collection
- `GET /api/v1/collections` - List collections
- `GET /api/v1/collections/{id}` - Get collection
- `DELETE /api/v1/collections/{id}` - Delete collection
- `POST /api/v1/collections/{id}/sources` - Add source to collection

**Search:**
- `POST /api/v1/search` - Semantic, keyword, and hybrid search
  - Vector search using pgvector
  - Keyword search with PostgreSQL full-text search
  - Hybrid mode combining both with score fusion
  - Collection-scoped search

**Embeddings:**
- `POST /api/v1/embeddings/generate` - Generate embedding
  - FREE Gemini (1500/day) as primary provider
  - OpenAI ($0.02/1M tokens) as fallback
  - Task-specific embeddings (summary vs query)

**Infrastructure:**
- FastAPI async framework
- JWT authentication via Supabase
- Redis-based rate limiting
  - 100 sources/hour
  - 1000 searches/hour
  - 500 embeddings/hour
  - 200 AI summaries/hour
- Structured logging with structlog
- Comprehensive error handling
- CORS configuration
- GZip compression

**AI Integration:**
- Anthropic Claude for summaries and title generation
- Google Gemini for FREE embeddings (primary)
- OpenAI for embeddings fallback
- Cost-optimized routing

**Database:**
- Supabase (PostgreSQL + pgvector)
- Row-level security (RLS) on all tables
- Tables: sources, summaries, collections, collection_sources, tags
- Vector similarity search with cosine distance

**Documentation:**
- Complete Agent API Guide (150+ pages)
- Python LangChain integration example
- Python custom agent example
- TypeScript agent example
- curl examples with RAG workflow
- Comprehensive README

**Deployment:**
- Railway-ready configuration
- Procfile and railway.toml
- Environment variables template (.env.example)
- Health check endpoint: `GET /health`
- Auto-generated API docs: `/docs` and `/redoc`

### Security
- JWT token validation
- Row-level security (RLS) on all data access
- Rate limiting per user
- Input validation with Pydantic
- Structured error messages (no internal details leaked)

---

## Legend

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
