# Recall Notebook API - Guide for AI RAG Agents

**Version:** 1.0.0
**Last Updated:** 2025-10-08
**Base URL:** `https://your-app.railway.app` (or `http://localhost:8000` for local)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [API Reference](#api-reference)
5. [RAG Patterns](#rag-patterns)
6. [Framework Integration](#framework-integration)
7. [Best Practices](#best-practices)
8. [Complete Examples](#complete-examples)
9. [Troubleshooting](#troubleshooting)
10. [Reference](#reference)

---

## Introduction

### What This API Provides

Recall Notebook API is a **production-ready knowledge backend** designed specifically for AI RAG (Retrieval-Augmented Generation) agents. It handles:

- ✅ **Vector Embeddings** - FREE Gemini embeddings (1500/day) with OpenAI fallback
- ✅ **Semantic Search** - Hybrid semantic + keyword search with relevance scoring
- ✅ **Knowledge Storage** - Structured document storage with summaries
- ✅ **Content Processing** - URL fetching and PDF text extraction
- ✅ **Organization** - Collections for grouping related documents

### Architecture: Microservices Approach

```
┌────────────────────────────┐
│   Your Agent Service       │
│  (Separate deployment)     │
│                            │
│  • Chat with streaming     │
│  • Conversation history    │
│  • Tool orchestration      │
│  • Memory management       │
└────────────┬───────────────┘
             │ HTTP API calls
             ▼
┌────────────────────────────┐
│  Recall Notebook API       │
│  (This service)            │
│                            │
│  • Embeddings (FREE)       │
│  • Semantic search         │
│  • Knowledge storage       │
│  • Content processing      │
└────────────────────────────┘
```

**Benefits:**
- **Separation of concerns** - Knowledge layer vs agent layer
- **Independent scaling** - Scale search and chat independently
- **Cost optimization** - FREE embeddings, shared across agents
- **Reusability** - Multiple agents can use same knowledge base

### Authentication Setup

All requests require JWT authentication:

```bash
# Request header
Authorization: Bearer YOUR_JWT_TOKEN
```

JWT tokens are issued by Supabase Auth. Get one from:
1. User signup/login in your frontend
2. Supabase Auth API
3. Service account (for server-to-server)

---

## Quick Start

### Your First RAG Query (5 minutes)

**Step 1: Search the knowledge base**

```bash
curl -X POST "https://your-app.railway.app/api/v1/search" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "mode": "hybrid",
    "limit": 5,
    "threshold": 0.7
  }'
```

**Response:**

```json
{
  "results": [
    {
      "source": {
        "id": "uuid",
        "title": "Introduction to ML Algorithms",
        "content_type": "url",
        "url": "https://example.com/ml",
        "created_at": "2025-10-01T10:00:00Z"
      },
      "summary": {
        "summary_text": "Comprehensive overview of ML algorithms...",
        "key_actions": ["Study supervised learning", "Practice with datasets"],
        "key_topics": ["machine learning", "algorithms", "neural networks"]
      },
      "relevance_score": 0.89,
      "match_type": "semantic"
    }
  ],
  "total": 5,
  "search_mode": "hybrid"
}
```

**Step 2: Use results in your agent**

```python
import anthropic

# Search returned results
context = "\n\n".join([
    f"[{r['source']['title']}]\n{r['summary']['summary_text']}"
    for r in results
])

# Send to Claude with context
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": f"""Context from knowledge base:
{context}

User question: What are the main machine learning algorithms?

Answer based on the context provided."""
    }]
)

print(response.content[0].text)
```

**Step 3: Save new knowledge**

```bash
curl -X POST "https://your-app.railway.app/api/v1/sources" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deep Learning Basics",
    "content_type": "text",
    "original_content": "Deep learning uses neural networks with multiple layers...",
    "summary_text": "Introduction to deep learning and neural networks",
    "key_actions": ["Learn backpropagation", "Understand activation functions"],
    "key_topics": ["deep learning", "neural networks", "AI"],
    "word_count": 250
  }'
```

---

## Core Concepts

### 1. Sources

A **source** is any piece of knowledge (document, article, note, PDF).

**Properties:**
- `title` - Document title
- `content_type` - `text`, `url`, `pdf`, or `image`
- `original_content` - Full text content
- `url` - Original URL (if applicable)
- `summary` - AI-generated summary with key actions and topics
- `embedding` - Vector representation for semantic search

**Example:**

```json
{
  "id": "uuid",
  "user_id": "user-uuid",
  "title": "Transformer Architecture",
  "content_type": "url",
  "original_content": "The Transformer architecture revolutionized NLP...",
  "url": "https://arxiv.org/abs/1706.03762",
  "created_at": "2025-10-01T10:00:00Z"
}
```

### 2. Summaries

Every source has an **AI-generated summary** with:
- `summary_text` - Concise 2-3 sentence summary
- `key_actions` - Actionable takeaways (3-5)
- `key_topics` - Tags/keywords (3-5)
- `embedding` - Vector for semantic search (1536 dimensions)

**Example:**

```json
{
  "summary_text": "The Transformer uses self-attention mechanisms to process sequences in parallel, achieving state-of-the-art results in NLP tasks.",
  "key_actions": [
    "Study self-attention mechanism",
    "Understand positional encoding",
    "Practice implementing transformers"
  ],
  "key_topics": ["transformers", "attention", "NLP", "deep learning"]
}
```

### 3. Collections

**Collections** organize related sources together.

**Use cases:**
- Research projects (e.g., "Transformer Research")
- Topics (e.g., "Machine Learning Papers")
- Workflows (e.g., "Current Sprint Docs")

**Example:**

```json
{
  "id": "collection-uuid",
  "name": "Deep Learning Papers",
  "description": "Collection of important DL research papers",
  "is_public": false,
  "source_count": 15
}
```

### 4. Embeddings

**Embeddings** are vector representations of text for semantic search.

**Provider Strategy:**
1. **Primary**: Google Gemini (FREE, 1500/day, 768 dimensions)
2. **Fallback**: OpenAI text-embedding-3-small ($0.02/1M tokens, 1536 dims)

**When to use:**
- Automatic for all sources (handled by API)
- Manual for custom search queries
- Batch for multiple texts

### 5. Search Modes

**Three search modes** for different use cases:

| Mode | Description | Best For |
|------|-------------|----------|
| `semantic` | Vector similarity search | Conceptual matches, meaning-based |
| `keyword` | Traditional text matching | Exact terms, proper nouns |
| `hybrid` | Combines both (recommended) | Best of both worlds |

**Example comparison:**

Query: "neural network training"

- **Semantic**: Finds "backpropagation", "gradient descent" (concepts)
- **Keyword**: Finds exact phrase "neural network training"
- **Hybrid**: Combines both, ranks by relevance

### 6. Rate Limits

**Protect your API from runaway agents:**

| Endpoint | Limit | Window |
|----------|-------|--------|
| Search | 1000 requests | 1 hour |
| Source creation | 100 requests | 1 hour |
| Embeddings | 500 requests | 1 hour |
| AI Summary | 200 requests | 1 hour |

**Headers returned:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1696512000
```

---

## API Reference

### Search API

**Endpoint:** `POST /api/v1/search`

Search the knowledge base with semantic, keyword, or hybrid mode.

**Request:**

```json
{
  "query": "machine learning algorithms",
  "mode": "hybrid",              // "semantic" | "keyword" | "hybrid"
  "limit": 20,                   // 1-100
  "threshold": 0.7,              // 0.0-1.0 (semantic similarity threshold)
  "collection_id": "uuid"        // Optional: filter by collection
}
```

**Response:**

```json
{
  "results": [
    {
      "source": {
        "id": "source-uuid",
        "title": "...",
        "content_type": "url",
        "original_content": "...",
        "url": "...",
        "created_at": "..."
      },
      "summary": {
        "id": "summary-uuid",
        "summary_text": "...",
        "key_actions": ["...", "..."],
        "key_topics": ["...", "..."],
        "word_count": 1500
      },
      "relevance_score": 0.89,      // 0.0-1.0
      "match_type": "semantic",     // "semantic" | "keyword" | "hybrid"
      "matched_content": "..."      // Preview of matched text
    }
  ],
  "total": 15,
  "search_mode": "hybrid"
}
```

**Example (Python):**

```python
import httpx

async def search_knowledge(query: str, mode: str = "hybrid") -> list:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-app.railway.app/api/v1/search",
            json={
                "query": query,
                "mode": mode,
                "limit": 10,
                "threshold": 0.7
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()["results"]

# Usage in agent
results = await search_knowledge("transformers architecture")
context = "\n\n".join([r["summary"]["summary_text"] for r in results])
```

**Example (curl):**

```bash
curl -X POST "https://your-app.railway.app/api/v1/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural networks",
    "mode": "hybrid",
    "limit": 5
  }' | jq '.results[] | {title: .source.title, score: .relevance_score}'
```

---

### Embeddings API

**Endpoint:** `POST /api/v1/embeddings/generate`

Generate vector embeddings for text (uses FREE Gemini, falls back to OpenAI).

**Request:**

```json
{
  "text": "This is text to embed",
  "type": "query"               // "summary" | "query"
}
```

**Response:**

```json
{
  "embedding": [0.123, -0.456, ...],  // 768 or 1536 floats
  "model": "models/embedding-001",     // Gemini or OpenAI model
  "tokens": 42
}
```

**When to use:**
- Custom similarity comparisons
- External vector databases
- Pre-computing embeddings for caching

**Example (Python):**

```python
async def get_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-app.railway.app/api/v1/embeddings/generate",
            json={"text": text, "type": "query"},
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()["embedding"]

# Compare embeddings
query_emb = await get_embedding("machine learning")
doc_emb = await get_embedding("ML algorithms and techniques")

# Cosine similarity
import numpy as np
similarity = np.dot(query_emb, doc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb))
```

---

### Sources API

#### Create Source

**Endpoint:** `POST /api/v1/sources`

Create a new source with summary and embedding.

**Request:**

```json
{
  "title": "Transformers Paper",
  "content_type": "url",
  "original_content": "The Transformer architecture...",
  "url": "https://arxiv.org/abs/1706.03762",
  "summary_text": "Introduction to attention mechanism...",
  "key_actions": ["Study attention", "Implement transformer"],
  "key_topics": ["transformers", "attention", "NLP"],
  "word_count": 1500
}
```

**Response:**

```json
{
  "source": {
    "id": "source-uuid",
    "user_id": "user-uuid",
    "title": "Transformers Paper",
    "content_type": "url",
    "original_content": "...",
    "url": "...",
    "created_at": "2025-10-01T10:00:00Z",
    "updated_at": "2025-10-01T10:00:00Z"
  },
  "summary": {
    "id": "summary-uuid",
    "source_id": "source-uuid",
    "summary_text": "...",
    "key_actions": ["..."],
    "key_topics": ["..."],
    "word_count": 1500,
    "created_at": "2025-10-01T10:00:00Z"
  }
}
```

**Example (Python):**

```python
async def save_source(title: str, content: str, summary: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-app.railway.app/api/v1/sources",
            json={
                "title": title,
                "content_type": "text",
                "original_content": content,
                "summary_text": summary["summary"],
                "key_actions": summary["actions"],
                "key_topics": summary["topics"],
                "word_count": len(content.split())
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

# Agent saves research findings
summary = await claude_summarize(research_text)
source = await save_source("Research Findings", research_text, summary)
```

#### List Sources

**Endpoint:** `GET /api/v1/sources`

List all sources with pagination and filtering.

**Query Parameters:**

```
page=1                          # Page number (default: 1)
limit=20                        # Items per page (1-100, default: 20)
content_type=url                # Filter by type: text, url, pdf
sort=newest                     # newest | oldest
tags=ml,ai                      # Comma-separated tags
tag_logic=OR                    # AND | OR
collection_id=uuid              # Filter by collection
```

**Response:**

```json
{
  "data": [/* array of sources with summaries */],
  "total": 150,
  "page": 1,
  "limit": 20,
  "has_more": true,
  "filters": {
    "content_type": "url",
    "sort": "newest"
  }
}
```

**Example (Python):**

```python
# Get recent PDFs
async def get_recent_pdfs() -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://your-app.railway.app/api/v1/sources",
            params={
                "content_type": "pdf",
                "sort": "newest",
                "limit": 10
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()["data"]
```

#### Get Single Source

**Endpoint:** `GET /api/v1/sources/{source_id}`

**Response:**

```json
{
  "id": "uuid",
  "title": "...",
  "content_type": "url",
  "original_content": "...",
  "summary": [{
    "summary_text": "...",
    "key_actions": ["..."],
    "key_topics": ["..."]
  }],
  "tags": [
    {"tag_name": "machine learning"},
    {"tag_name": "AI"}
  ]
}
```

#### Update Source

**Endpoint:** `PATCH /api/v1/sources/{source_id}`

**Request:**

```json
{
  "title": "Updated Title",
  "original_content": "Updated content..."
}
```

#### Delete Source

**Endpoint:** `DELETE /api/v1/sources/{source_id}`

**Response:** `204 No Content`

---

### Helper Endpoints

#### Fetch URL Content

**Endpoint:** `POST /api/v1/fetch-url`

Fetch and extract content from URL (handles HTML cleaning).

**Request:**

```json
{
  "url": "https://example.com/article"
}
```

**Response:**

```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "content": "Extracted text content...",
  "word_count": 1200,
  "content_type": "url"
}
```

**Example (Python):**

```python
# Agent fetches URL before saving
async def ingest_url(url: str) -> dict:
    # 1. Fetch content
    content = await client.post(
        f"{API}/api/v1/fetch-url",
        json={"url": url}
    )

    # 2. Summarize with Claude
    summary = await claude_summarize(content["content"])

    # 3. Save to knowledge base
    return await client.post(
        f"{API}/api/v1/sources",
        json={
            "title": content["title"],
            "content_type": "url",
            "original_content": content["content"],
            "url": url,
            **summary
        }
    )
```

#### Process PDF

**Endpoint:** `POST /api/v1/process-pdf`

Extract text from PDF file.

**Request:**

```bash
curl -X POST "https://your-app.railway.app/api/v1/process-pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@research_paper.pdf"
```

**Response:**

```json
{
  "filename": "research_paper.pdf",
  "content": "Extracted text from PDF...",
  "word_count": 5000,
  "page_count": 12,
  "content_type": "pdf"
}
```

#### Generate Summary

**Endpoint:** `POST /api/v1/summarize`

Generate AI summary using Claude (useful if you want to summarize before saving).

**Request:**

```json
{
  "content": "Long text to summarize...",
  "content_type": "text"
}
```

**Response:**

```json
{
  "summary": "Concise summary of the content...",
  "key_actions": ["Action 1", "Action 2"],
  "topics": ["topic1", "topic2"],
  "word_count": 1500
}
```

---

### Collections API

#### Create Collection

**Endpoint:** `POST /api/v1/collections`

**Request:**

```json
{
  "name": "ML Research Papers",
  "description": "Collection of important ML papers",
  "is_public": false
}
```

#### List Collections

**Endpoint:** `GET /api/v1/collections`

**Response:**

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "ML Research",
      "description": "...",
      "is_public": false,
      "source_count": 15,
      "created_at": "..."
    }
  ],
  "total": 5
}
```

#### Get Collection with Sources

**Endpoint:** `GET /api/v1/collections/{collection_id}`

**Response:**

```json
{
  "collection": {
    "id": "uuid",
    "name": "ML Research",
    "description": "...",
    "source_count": 15
  },
  "sources": [/* array of sources */]
}
```

#### Add Source to Collection

**Endpoint:** `POST /api/v1/collections/{collection_id}/sources`

**Request:**

```json
{
  "source_id": "source-uuid"
}
```

---

## RAG Patterns

### Pattern 1: Simple RAG (Search + Context)

**Use case:** Basic question answering with context retrieval.

```python
async def simple_rag(query: str) -> str:
    """Simple RAG: search + context + answer."""

    # 1. Search knowledge base
    results = await search_knowledge(query, mode="hybrid", limit=5)

    # 2. Build context
    context = "\n\n".join([
        f"[{r['source']['title']}]\n{r['summary']['summary_text']}"
        for r in results
    ])

    # 3. Generate answer with Claude
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Context from knowledge base:
{context}

Question: {query}

Answer based on the context above."""
        }]
    )

    return response.content[0].text

# Usage
answer = await simple_rag("What are transformers in deep learning?")
```

### Pattern 2: Multi-Hop RAG (Iterative Search)

**Use case:** Complex questions requiring multiple searches.

```python
async def multi_hop_rag(query: str, max_hops: int = 3) -> str:
    """Multi-hop RAG: iterative search for complex queries."""

    context_parts = []
    current_query = query

    for hop in range(max_hops):
        # Search with current query
        results = await search_knowledge(current_query, limit=3)

        # Add to context
        for r in results:
            context_parts.append(f"[{r['source']['title']}]\n{r['summary']['summary_text']}")

        # Use Claude to determine if we need more info
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Context so far:
{chr(10).join(context_parts)}

Original question: {query}

Do you have enough information to answer? If not, what specific aspect should we search for next?
Reply with either:
1. "ANSWER: [your answer]" if you have enough info
2. "SEARCH: [refined query]" if you need more info"""
            }]
        )

        text = response.content[0].text

        if text.startswith("ANSWER:"):
            return text.replace("ANSWER:", "").strip()
        elif text.startswith("SEARCH:"):
            current_query = text.replace("SEARCH:", "").strip()
        else:
            break

    # Final answer with all collected context
    return await simple_rag(query)  # Fallback to simple RAG

# Usage
answer = await multi_hop_rag("How do transformers compare to RNNs for sequence modeling?")
```

### Pattern 3: Agentic RAG (Tool Calling)

**Use case:** Agent decides when to search knowledge base.

```python
from anthropic import Anthropic

# Define tool for Claude
tools = [
    {
        "name": "search_knowledge",
        "description": "Search the knowledge base for relevant information. Returns summaries of matching documents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (natural language)"
                },
                "mode": {
                    "type": "string",
                    "enum": ["semantic", "keyword", "hybrid"],
                    "description": "Search mode",
                    "default": "hybrid"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_to_knowledge",
        "description": "Save new information to the knowledge base",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "key_topics": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["title", "content"]
        }
    }
]

async def agentic_rag(user_message: str) -> str:
    """Agentic RAG: Claude decides when to use tools."""

    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        # Check if Claude wants to use a tool
        if response.stop_reason == "tool_use":
            tool_use = next(
                block for block in response.content
                if block.type == "tool_use"
            )

            # Execute tool
            if tool_use.name == "search_knowledge":
                results = await search_knowledge(
                    tool_use.input["query"],
                    mode=tool_use.input.get("mode", "hybrid")
                )
                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps([
                        {
                            "title": r["source"]["title"],
                            "summary": r["summary"]["summary_text"],
                            "relevance": r["relevance_score"]
                        }
                        for r in results[:5]
                    ])
                }

            elif tool_use.name == "save_to_knowledge":
                # Summarize and save
                summary = await generate_summary(tool_use.input["content"])
                source = await save_source(
                    tool_use.input["title"],
                    tool_use.input["content"],
                    summary
                )
                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": f"Saved to knowledge base: {source['source']['id']}"
                }

            # Continue conversation with tool result
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": [tool_result]})

        else:
            # Claude has final answer
            return response.content[0].text

# Usage
answer = await agentic_rag("Research transformers and save key findings to knowledge base")
```

### Pattern 4: Collection-Based Context

**Use case:** Focus search on specific topics/projects.

```python
async def collection_scoped_rag(query: str, collection_name: str) -> str:
    """RAG with context filtered by collection."""

    # 1. Find collection
    collections = await client.get(f"{API}/api/v1/collections")
    collection = next(
        (c for c in collections["data"] if c["name"] == collection_name),
        None
    )

    if not collection:
        return "Collection not found"

    # 2. Search within collection
    results = await client.post(
        f"{API}/api/v1/search",
        json={
            "query": query,
            "mode": "hybrid",
            "collection_id": collection["id"],
            "limit": 10
        }
    )

    # 3. Generate answer
    context = "\n\n".join([
        r["summary"]["summary_text"]
        for r in results["results"]
    ])

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{
            "role": "user",
            "content": f"Context from '{collection_name}' collection:\n{context}\n\nQuestion: {query}"
        }]
    )

    return response.content[0].text

# Usage - only search within specific research project
answer = await collection_scoped_rag(
    "What are the key findings?",
    collection_name="Transformer Research"
)
```

---

## Framework Integration

### LangChain Integration

**Complete example with LangChain tools:**

```python
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import Tool
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import httpx

# Recall API client
API_URL = "https://your-app.railway.app"
TOKEN = "your-jwt-token"

# Tool 1: Search knowledge base
def search_tool_func(query: str) -> str:
    """Search the knowledge base."""
    response = httpx.post(
        f"{API_URL}/api/v1/search",
        json={"query": query, "mode": "hybrid", "limit": 5},
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    results = response.json()["results"]

    return "\n\n".join([
        f"[{r['source']['title']}]\n"
        f"Summary: {r['summary']['summary_text']}\n"
        f"Relevance: {r['relevance_score']:.2f}"
        for r in results
    ])

search_tool = Tool(
    name="search_knowledge_base",
    func=search_tool_func,
    description="Search the knowledge base for relevant information. Input should be a natural language query."
)

# Tool 2: Save to knowledge base
def save_tool_func(input_str: str) -> str:
    """Save information to knowledge base."""
    import json
    data = json.loads(input_str)

    # Generate summary
    summary_response = httpx.post(
        f"{API_URL}/api/v1/summarize",
        json={"content": data["content"], "content_type": "text"},
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    summary = summary_response.json()

    # Save source
    source_response = httpx.post(
        f"{API_URL}/api/v1/sources",
        json={
            "title": data["title"],
            "content_type": "text",
            "original_content": data["content"],
            "summary_text": summary["summary"],
            "key_actions": summary["key_actions"],
            "key_topics": summary["topics"],
            "word_count": summary["word_count"]
        },
        headers={"Authorization": f"Bearer {TOKEN}"}
    )

    return f"Saved to knowledge base: {source_response.json()['source']['id']}"

save_tool = Tool(
    name="save_to_knowledge_base",
    func=save_tool_func,
    description='Save new information to knowledge base. Input should be JSON: {"title": "...", "content": "..."}'
)

# Create agent
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a research assistant with access to a knowledge base. Use the tools to search for information and save new findings."),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_functions_agent(llm, [search_tool, save_tool], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[search_tool, save_tool], verbose=True)

# Run agent
result = agent_executor.invoke({
    "input": "Research transformers in deep learning and save key findings"
})
print(result["output"])
```

### LlamaIndex Integration

```python
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
import httpx

API_URL = "https://your-app.railway.app"
TOKEN = "your-jwt-token"

class RecallRetriever(BaseRetriever):
    """Custom retriever using Recall Notebook API."""

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """Retrieve nodes using Recall API."""
        response = httpx.post(
            f"{API_URL}/api/v1/search",
            json={
                "query": query_bundle.query_str,
                "mode": "hybrid",
                "limit": 10
            },
            headers={"Authorization": f"Bearer {TOKEN}"}
        )

        results = response.json()["results"]

        # Convert to LlamaIndex nodes
        nodes = []
        for r in results:
            doc = Document(
                text=r["summary"]["summary_text"],
                metadata={
                    "title": r["source"]["title"],
                    "url": r["source"].get("url"),
                    "topics": r["summary"]["key_topics"]
                }
            )
            nodes.append(NodeWithScore(node=doc, score=r["relevance_score"]))

        return nodes

# Use with query engine
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.anthropic import Anthropic

retriever = RecallRetriever()
llm = Anthropic(model="claude-3-5-sonnet-20241022")
query_engine = RetrieverQueryEngine.from_args(retriever=retriever, llm=llm)

# Query
response = query_engine.query("What are transformers?")
print(response)
```

---

## Best Practices

### 1. Query Optimization

**Good queries:**
- ✅ "transformer architecture self-attention mechanism"
- ✅ "deep learning optimization techniques Adam SGD"
- ✅ "natural language processing BERT GPT comparison"

**Poor queries:**
- ❌ "how does it work" (too vague)
- ❌ "the" (too short)
- ❌ "asdfasdf" (gibberish)

**Tips:**
- Use specific terms and concepts
- Include key technical terms
- Be descriptive but concise (3-10 words ideal)
- For hybrid mode, include both concepts AND exact terms

### 2. Caching Strategies

**Cache search results:**

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
async def cached_search(query: str, mode: str = "hybrid") -> str:
    """Cache search results to reduce API calls."""
    results = await search_knowledge(query, mode)
    return json.dumps(results)

# Use cached version
results = json.loads(await cached_search("transformers"))
```

**Cache embeddings:**

```python
embedding_cache = {}

async def get_embedding_cached(text: str) -> list[float]:
    """Cache embeddings for frequently used texts."""
    cache_key = hashlib.md5(text.encode()).hexdigest()

    if cache_key in embedding_cache:
        return embedding_cache[cache_key]

    embedding = await get_embedding(text)
    embedding_cache[cache_key] = embedding
    return embedding
```

### 3. Error Handling & Retries

**Robust error handling:**

```python
import asyncio
from typing import Optional

async def search_with_retry(
    query: str,
    max_retries: int = 3,
    backoff: float = 1.0
) -> Optional[list]:
    """Search with exponential backoff retry."""

    for attempt in range(max_retries):
        try:
            return await search_knowledge(query)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit
                retry_after = int(e.response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
            elif e.response.status_code >= 500:  # Server error
                wait_time = backoff * (2 ** attempt)
                logger.warning(f"Server error, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                raise  # Don't retry client errors (4xx)

        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(backoff * (2 ** attempt))
            else:
                raise

    return None
```

### 4. Cost Management

**Monitor API usage:**

```python
import structlog

logger = structlog.get_logger()

async def search_with_logging(query: str) -> list:
    """Log all API calls for cost tracking."""

    logger.info("api_call", endpoint="search", query=query)

    results = await search_knowledge(query)

    logger.info(
        "api_response",
        endpoint="search",
        results_count=len(results),
        cost=0.0  # Embeddings are FREE with Gemini!
    )

    return results
```

**Use FREE tier wisely:**
- Gemini: 1500 embeddings/day FREE
- After limit: Falls back to OpenAI ($0.02/1M tokens)
- Batch requests when possible
- Cache aggressively

### 5. Performance Tuning

**Parallel requests:**

```python
import asyncio

async def multi_search(queries: list[str]) -> dict[str, list]:
    """Search multiple queries in parallel."""

    tasks = [search_knowledge(q) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        query: result if not isinstance(result, Exception) else []
        for query, result in zip(queries, results)
    }

# Usage
results = await multi_search([
    "transformers architecture",
    "BERT pretraining",
    "GPT fine-tuning"
])
```

**Timeout management:**

```python
async def search_with_timeout(query: str, timeout: float = 10.0) -> list:
    """Search with timeout to prevent hanging."""

    try:
        return await asyncio.wait_for(
            search_knowledge(query),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Search timed out after {timeout}s: {query}")
        return []
```

---

## Complete Examples

### Example 1: Research Agent (Python)

Full implementation of research agent that searches and saves findings.

```python
# research_agent.py
import asyncio
import httpx
from anthropic import Anthropic
from typing import List, Dict
import structlog

logger = structlog.get_logger()

class ResearchAgent:
    """AI research agent using Recall Notebook API."""

    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.token = token
        self.client = httpx.AsyncClient()
        self.claude = Anthropic()

    async def search(self, query: str, mode: str = "hybrid") -> List[Dict]:
        """Search knowledge base."""
        response = await self.client.post(
            f"{self.api_url}/api/v1/search",
            json={"query": query, "mode": mode, "limit": 10},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.json()["results"]

    async def summarize(self, content: str) -> Dict:
        """Summarize content with Claude."""
        response = await self.client.post(
            f"{self.api_url}/api/v1/summarize",
            json={"content": content, "content_type": "text"},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.json()

    async def save_source(self, title: str, content: str, summary: Dict) -> Dict:
        """Save to knowledge base."""
        response = await self.client.post(
            f"{self.api_url}/api/v1/sources",
            json={
                "title": title,
                "content_type": "text",
                "original_content": content,
                "summary_text": summary["summary"],
                "key_actions": summary["key_actions"],
                "key_topics": summary["topics"],
                "word_count": summary["word_count"]
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.json()

    async def research(self, topic: str) -> str:
        """Conduct research on topic."""

        # 1. Search existing knowledge
        logger.info("searching_knowledge", topic=topic)
        results = await self.search(topic)

        # 2. Build context
        context = "\n\n".join([
            f"[{r['source']['title']}]\n{r['summary']['summary_text']}"
            for r in results[:5]
        ])

        # 3. Generate new insights with Claude
        logger.info("generating_insights", topic=topic)
        response = self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": f"""Based on this research context:

{context}

Topic: {topic}

Please:
1. Summarize key findings
2. Identify gaps in current knowledge
3. Suggest areas for further research

Provide a comprehensive research summary."""
            }]
        )

        research_summary = response.content[0].text

        # 4. Save research summary
        logger.info("saving_research", topic=topic)
        summary = await self.summarize(research_summary)
        source = await self.save_source(
            f"Research Summary: {topic}",
            research_summary,
            summary
        )

        logger.info("research_complete", source_id=source["source"]["id"])

        return research_summary

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

# Usage
async def main():
    agent = ResearchAgent(
        api_url="https://your-app.railway.app",
        token="your-jwt-token"
    )

    try:
        summary = await agent.research("transformer architecture in deep learning")
        print(summary)
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Troubleshooting

### Common Errors

**401 Unauthorized**
```json
{"error": "Authorization header missing. Please sign in."}
```
**Solution:** Include JWT token in Authorization header.

**429 Too Many Requests**
```json
{"error": "Too many requests. Please try again in 60 seconds."}
```
**Solution:** Respect rate limits. Check `Retry-After` header.

**400 Bad Request**
```json
{"error": "query must be at least 1 character"}
```
**Solution:** Validate input before sending. Check Pydantic models.

**503 Service Unavailable**
```json
{"error": "AI service temporarily unavailable. Please try again."}
```
**Solution:** Retry with exponential backoff. Check service status.

### Debugging Tips

**Enable request logging:**

```python
import httpx

# Log all requests
async with httpx.AsyncClient(event_hooks={
    "request": [lambda req: print(f"→ {req.method} {req.url}")],
    "response": [lambda res: print(f"← {res.status_code}")]
}) as client:
    response = await client.post(...)
```

**Validate responses:**

```python
def validate_search_response(response: dict) -> bool:
    """Validate search response structure."""
    required_keys = {"results", "total", "search_mode"}
    if not all(k in response for k in required_keys):
        logger.error("invalid_response", response=response)
        return False
    return True
```

### Performance Issues

**Slow searches (>2s):**
- Lower threshold (0.6 instead of 0.7)
- Reduce limit (5 instead of 20)
- Use keyword mode instead of semantic
- Check database indexes in Supabase

**Rate limit exceeded:**
- Implement caching
- Batch requests when possible
- Use webhook/polling for async operations
- Consider upgrading plan

---

## Reference

### Complete API Specification

| Endpoint | Method | Purpose | Rate Limit |
|----------|--------|---------|------------|
| `/api/v1/search` | POST | Search knowledge base | 1000/hour |
| `/api/v1/embeddings/generate` | POST | Generate embedding | 500/hour |
| `/api/v1/sources` | POST | Create source | 100/hour |
| `/api/v1/sources` | GET | List sources | 1000/hour |
| `/api/v1/sources/{id}` | GET | Get source | 1000/hour |
| `/api/v1/sources/{id}` | PATCH | Update source | 100/hour |
| `/api/v1/sources/{id}` | DELETE | Delete source | 100/hour |
| `/api/v1/fetch-url` | POST | Fetch URL content | 100/hour |
| `/api/v1/process-pdf` | POST | Process PDF | 100/hour |
| `/api/v1/summarize` | POST | Generate summary | 200/hour |
| `/api/v1/collections` | POST | Create collection | 100/hour |
| `/api/v1/collections` | GET | List collections | 1000/hour |
| `/api/v1/collections/{id}` | GET | Get collection | 1000/hour |
| `/api/v1/collections/{id}` | DELETE | Delete collection | 100/hour |
| `/api/v1/collections/{id}/sources` | POST | Add to collection | 100/hour |

### Embedding Models

| Provider | Model | Dimensions | Cost | Limit |
|----------|-------|------------|------|-------|
| Gemini (primary) | embedding-001 | 768 | FREE | 1500/day |
| OpenAI (fallback) | text-embedding-3-small | 1536 | $0.02/1M | Unlimited |

### Error Codes

| Code | Error | Meaning |
|------|-------|---------|
| 400 | Bad Request | Invalid input (check validation) |
| 401 | Unauthorized | Missing/invalid JWT token |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error (retry) |
| 503 | Service Unavailable | AI service down (retry) |

### Support

- **Documentation:** [https://github.com/your-repo](https://github.com/your-repo)
- **API Status:** [https://status.railway.app](https://status.railway.app)
- **Issues:** [https://github.com/your-repo/issues](https://github.com/your-repo/issues)

---

## What's Next?

1. **Test the API** - Try the Quick Start examples
2. **Build your agent** - Use the RAG patterns
3. **Integrate frameworks** - LangChain or LlamaIndex
4. **Deploy** - Ship your agent service
5. **Monitor** - Track costs and performance

**Happy building! 🚀**
