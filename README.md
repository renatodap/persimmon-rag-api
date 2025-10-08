# Recall Notebook API

**FastAPI backend for AI-powered knowledge management and RAG (Retrieval-Augmented Generation)**

This is a production-ready knowledge API designed specifically for RAG agents and AI applications. It provides:
- 🆓 **FREE embeddings** (Google Gemini with OpenAI fallback)
- 🔍 **Hybrid search** (semantic + keyword with pgvector)
- 📦 **Batch operations** (process 100 embeddings or 50 sources at once)
- 🔔 **Real-time webhooks** (get notified when events occur)
- 🔐 **Built-in auth** (JWT via Supabase)
- 📊 **Production-ready** (rate limiting, logging, error handling)

**Perfect for:**
- Building RAG chatbots
- Knowledge management systems
- Research assistants
- Document processing pipelines
- Multi-agent systems

> **Note**: This repository contains only the backend API. For the web UI client, see [recall-notebook](https://github.com/yourusername/recall-notebook).

## 🚀 Quick Start for Agent Developers

See the [**Agent API Guide**](docs/AGENT_API_GUIDE.md) (150+ pages) for complete integration instructions, examples in Python/TypeScript, and RAG patterns.

**Live Demo API**: https://your-app.railway.app (replace with your Railway URL)

## Features

- **Sources CRUD** - Create, read, update, delete sources with AI summaries
- **Collections** - Organize sources into collections
- **Semantic Search** - Vector search using Gemini embeddings
- **Content Processing** - URL fetching, PDF processing
- **Batch Operations** - Process up to 100 embeddings or 50 sources in parallel
- **Webhooks** - Real-time event notifications with HMAC signatures
- **Authentication** - JWT-based auth via Supabase
- **Rate Limiting** - Redis-based rate limiting
- **Production-Ready** - Structured logging, error handling, testing

## Tech Stack

- **FastAPI** - Modern async web framework
- **Pydantic** - Data validation
- **Supabase** - PostgreSQL database with pgvector
- **Anthropic Claude** - AI summaries
- **Google Gemini** - FREE embeddings (1500/day)
- **OpenAI** - Embeddings fallback
- **Redis** - Rate limiting
- **Structlog** - Structured logging
- **Pytest** - Testing framework

## Prerequisites

- Python 3.11+
- Poetry
- Redis (for rate limiting)
- Supabase account
- API keys: Anthropic, Google Gemini, OpenAI

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/recall-notebook-api.git
cd recall-notebook-api
poetry install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and credentials
```

**Required environment variables:**
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_GEMINI_API_KEY=your_google_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_jwt_secret_32+_chars
WEBHOOK_SECRET=your_webhook_secret
```

### 3. Run Development Server

```bash
poetry run uvicorn app.main:app --reload
```

Server starts at: http://localhost:8000

### 4. Access API Documentation

- 📘 **Swagger UI**: http://localhost:8000/docs (interactive API testing)
- 📕 **ReDoc**: http://localhost:8000/redoc (beautiful documentation)
- ✅ **Health Check**: http://localhost:8000/health

## 🤖 For AI Agent Developers

This API is designed as a **knowledge backend** for RAG (Retrieval-Augmented Generation) agents. It handles:
- ✅ Embeddings generation (FREE Gemini + OpenAI fallback)
- ✅ Semantic search (pgvector with hybrid search)
- ✅ Content storage and processing (URLs, PDFs, text)
- ✅ Collection-based organization

**Your agent service** (separate repo) should handle:
- Chat/streaming responses
- Conversation history
- Tool calling orchestration
- Agent memory

### 📚 Complete Agent Documentation

- **[Agent API Guide](docs/AGENT_API_GUIDE.md)** - Complete guide for RAG agent developers (150+ pages)
- **[Python LangChain Example](docs/examples/python_langchain_agent.py)** - Full LangChain integration with tools
- **[Python Custom Agent](docs/examples/python_custom_agent.py)** - Custom agent without frameworks
- **[TypeScript Agent](docs/examples/typescript_agent.ts)** - Node.js/TypeScript implementation
- **[curl Examples](docs/examples/curl_examples.sh)** - Complete API examples with RAG workflow

### Quick RAG Example

```python
import httpx
from anthropic import Anthropic

# 1. Search knowledge base
response = httpx.post("http://localhost:8000/api/v1/search", json={
    "query": "machine learning transformers",
    "mode": "hybrid",
    "limit": 5
}, headers={"Authorization": f"Bearer {token}"})

results = response.json()["results"]

# 2. Build context from results
context = "\n\n".join([
    f"[{r['source']['title']}]\n{r['summary']['summary_text']}"
    for r in results
])

# 3. Use with Claude
claude = Anthropic()
response = claude.messages.create(
    model="claude-3-5-sonnet-20241022",
    system=f"Context from knowledge base:\n{context}",
    messages=[{"role": "user", "content": "Explain transformers"}]
)
```

## API Endpoints

### Sources (8 endpoints)
- `POST /api/v1/sources` - Create source with AI summary
- `GET /api/v1/sources` - List sources (paginated)
- `GET /api/v1/sources/{id}` - Get single source
- `PATCH /api/v1/sources/{id}` - Update source
- `DELETE /api/v1/sources/{id}` - Delete source
- `POST /api/v1/fetch-url` - Fetch URL content
- `POST /api/v1/process-pdf` - Process PDF file
- `POST /api/v1/summarize` - Generate AI summary

### Collections (5 endpoints)
- `POST /api/v1/collections` - Create collection
- `GET /api/v1/collections` - List collections
- `GET /api/v1/collections/{id}` - Get collection
- `DELETE /api/v1/collections/{id}` - Delete collection
- `POST /api/v1/collections/{id}/sources` - Add source to collection

### Search (1 endpoint)
- `POST /api/v1/search` - Semantic/keyword/hybrid search

### Embeddings (2 endpoints)
- `POST /api/v1/embeddings/generate` - Generate single embedding
- `POST /api/v1/embeddings/batch` - Generate embeddings for up to 100 texts in parallel

### Webhooks (4 endpoints)
- `POST /api/v1/webhooks` - Register webhook for real-time events
- `GET /api/v1/webhooks` - List user's webhooks
- `DELETE /api/v1/webhooks/{id}` - Delete webhook
- `POST /api/v1/webhooks/test` - Test webhook delivery

## Batch Operations

### Batch Embeddings

Process up to 100 texts in a single request:

```bash
curl -X POST http://localhost:8000/api/v1/embeddings/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"text": "First document", "type": "summary", "index": 0},
      {"text": "Second document", "type": "summary", "index": 1}
    ]
  }'
```

### Batch Sources

Create up to 50 sources in a single request:

```bash
curl -X POST http://localhost:8000/api/v1/sources/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "title": "Article 1",
        "content_type": "url",
        "original_content": "Content...",
        "summary_text": "Summary...",
        "key_actions": ["Action 1"],
        "key_topics": ["AI"],
        "word_count": 500,
        "index": 0
      }
    ]
  }'
```

## Webhooks

Receive real-time notifications when events occur (source created, updated, deleted, etc.).

### Register Webhook

```bash
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://myapp.com/webhooks/recall",
    "events": ["source.created", "source.updated"],
    "secret": "my-webhook-secret"
  }'
```

### Webhook Payload Format

```json
{
  "event": "source.created",
  "timestamp": "2025-01-10T12:00:00Z",
  "data": {
    "source_id": "uuid-here",
    "title": "New Article",
    "content_type": "url"
  },
  "user_id": "user-uuid"
}
```

### Verify Webhook Signature

Webhooks are signed with HMAC-SHA256:

```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    payload_str = json.dumps(payload, sort_keys=True)
    expected = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, f"sha256={expected}")
```

## Development

### Run Tests

```bash
# Run all tests with coverage
poetry run pytest

# Run with coverage report
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_sources.py -v
```

### Code Quality

```bash
# Format code with black
poetry run black app tests

# Lint with ruff
poetry run ruff check app tests

# Type checking with mypy
poetry run mypy app
```

## Deployment to Railway

### 1. Create Railway Project

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and create project
railway login
railway init
```

### 2. Set Environment Variables

In Railway dashboard, add:
```
SUPABASE_URL=xxx
SUPABASE_KEY=xxx
SUPABASE_SERVICE_KEY=xxx
ANTHROPIC_API_KEY=xxx
GOOGLE_GEMINI_API_KEY=xxx
OPENAI_API_KEY=xxx
JWT_SECRET=xxx
WEBHOOK_SECRET=xxx (for signing webhook payloads)
REDIS_URL=xxx (Railway Redis addon)
ENVIRONMENT=production
```

### 3. Deploy

```bash
railway up
```

### 4. Verify Deployment

- Health check: https://your-app.railway.app/health
- API docs: https://your-app.railway.app/docs

## Project Structure

```
recall-notebook-api/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment configuration
│   ├── api/
│   │   └── v1/              # API v1 routes
│   │       ├── sources.py   # Sources CRUD
│   │       ├── collections.py
│   │       ├── search.py    # Hybrid search
│   │       ├── embeddings.py # Batch embeddings
│   │       └── webhooks.py  # Real-time events
│   ├── core/                # Core utilities
│   │   ├── auth.py          # JWT authentication
│   │   ├── errors.py        # Error handling
│   │   ├── rate_limit.py    # Rate limiting
│   │   └── logging_config.py
│   ├── models/              # Pydantic models
│   │   ├── source.py
│   │   ├── embedding.py
│   │   └── webhook.py
│   ├── services/            # Business logic
│   │   ├── ai_service.py    # Claude integration
│   │   ├── embedding_service.py # Gemini/OpenAI
│   │   ├── webhook_service.py
│   │   └── supabase_service.py
│   └── utils/               # Helpers
├── migrations/              # SQL migrations
│   └── 001_webhooks.sql
├── docs/                    # Documentation
│   ├── AGENT_API_GUIDE.md   # Primary documentation (150+ pages)
│   ├── CHANGELOG.md         # Version history
│   └── examples/            # Code examples
│       ├── python_langchain_agent.py
│       ├── python_custom_agent.py
│       ├── typescript_agent.ts
│       └── curl_examples.sh
├── tests/                   # Test suite
│   ├── unit/
│   └── integration/
├── pyproject.toml           # Poetry dependencies
├── Procfile                 # Railway deployment
├── railway.toml             # Railway config
├── .env.example             # Environment template
└── README.md                # This file
```

## Environment Variables

See `.env.example` for all required variables.

## API Version

**Current Version:** 1.1.0

See [CHANGELOG.md](docs/CHANGELOG.md) for version history and release notes.

## Related Repositories

- **[recall-notebook](https://github.com/yourusername/recall-notebook)** - Web UI client for this API (Next.js)
- **[Your RAG agent](https://github.com/yourusername/your-agent)** - Example agent using this API

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

- 📖 **Documentation**: [Agent API Guide](docs/AGENT_API_GUIDE.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/recall-notebook-api/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/recall-notebook-api/discussions)

## License

MIT
