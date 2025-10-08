# Recall Notebook Backend

FastAPI backend for Recall Notebook - AI-powered knowledge management system.

**🤖 Perfect for RAG Agents**: This API is designed as a **knowledge backend** for AI agents. It provides embeddings generation, semantic search, and content storage - everything you need for Retrieval-Augmented Generation (RAG). See the [Agent API Guide](docs/AGENT_API_GUIDE.md) to get started.

## Features

- **Sources CRUD** - Create, read, update, delete sources with AI summaries
- **Collections** - Organize sources into collections
- **Semantic Search** - Vector search using Gemini embeddings
- **Content Processing** - URL fetching, PDF processing
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

### 1. Install Dependencies

```bash
cd backend
poetry install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run Development Server

```bash
poetry run python -m app.main
# OR
poetry run uvicorn app.main:app --reload
```

### 4. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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

### Embeddings (1 endpoint)
- `POST /api/v1/embeddings/generate` - Generate embedding

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
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── api/
│   │   └── v1/              # API routes
│   ├── core/                # Auth, errors, logging
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   └── utils/               # Helpers
├── tests/                   # Tests
├── pyproject.toml           # Dependencies
├── Procfile                # Railway
└── railway.toml            # Railway config
```

## Environment Variables

See `.env.example` for all required variables.

## License

MIT
