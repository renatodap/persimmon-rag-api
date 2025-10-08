#!/bin/bash
# Recall Notebook API - Complete curl Examples
# For AI RAG agents and testing

# Configuration
API_URL="${RECALL_API_URL:-https://your-app.railway.app}"
TOKEN="${RECALL_API_TOKEN:-your-jwt-token-here}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Recall Notebook API - curl Examples${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "API URL: $API_URL"
echo ""

# ============================================================================
# 1. HEALTH CHECK
# ============================================================================

echo -e "${YELLOW}1. Health Check${NC}"
echo "GET /health"
echo ""

curl -s "$API_URL/health" | jq '.'

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 2. SEARCH KNOWLEDGE BASE
# ============================================================================

echo -e "${YELLOW}2. Search Knowledge Base (Hybrid Mode)${NC}"
echo "POST /api/v1/search"
echo ""

curl -s -X POST "$API_URL/api/v1/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "mode": "hybrid",
    "limit": 5,
    "threshold": 0.7
  }' | jq '.results[] | {
    title: .source.title,
    relevance: .relevance_score,
    match_type: .match_type,
    topics: .summary.key_topics
  }'

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 3. SEMANTIC SEARCH
# ============================================================================

echo -e "${YELLOW}3. Semantic Search Only${NC}"
echo "POST /api/v1/search (mode: semantic)"
echo ""

curl -s -X POST "$API_URL/api/v1/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural network training techniques",
    "mode": "semantic",
    "limit": 3,
    "threshold": 0.75
  }' | jq '{
    total: .total,
    mode: .search_mode,
    top_results: .results[0:3] | map({
      title: .source.title,
      score: .relevance_score
    })
  }'

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 4. GENERATE EMBEDDING
# ============================================================================

echo -e "${YELLOW}4. Generate Embedding (FREE Gemini)${NC}"
echo "POST /api/v1/embeddings/generate"
echo ""

curl -s -X POST "$API_URL/api/v1/embeddings/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is text to embed for semantic search",
    "type": "query"
  }' | jq '{
    model: .model,
    tokens: .tokens,
    dimension: (.embedding | length),
    first_values: .embedding[0:5]
  }'

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 5. SUMMARIZE CONTENT
# ============================================================================

echo -e "${YELLOW}5. Generate AI Summary${NC}"
echo "POST /api/v1/summarize"
echo ""

curl -s -X POST "$API_URL/api/v1/summarize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Deep learning is a subset of machine learning that uses neural networks with multiple layers. These networks can learn hierarchical representations of data, making them particularly effective for tasks like image recognition, natural language processing, and speech recognition. The success of deep learning is largely due to the availability of large datasets and powerful GPUs for training.",
    "content_type": "text"
  }' | jq '{
    summary: .summary,
    key_actions: .key_actions,
    topics: .topics,
    word_count: .word_count
  }'

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 6. CREATE SOURCE
# ============================================================================

echo -e "${YELLOW}6. Create Source with Summary${NC}"
echo "POST /api/v1/sources"
echo ""

curl -s -X POST "$API_URL/api/v1/sources" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deep Learning Fundamentals",
    "content_type": "text",
    "original_content": "Deep learning uses neural networks with multiple layers to learn hierarchical data representations...",
    "summary_text": "Introduction to deep learning and neural networks",
    "key_actions": ["Study neural networks", "Practice with datasets"],
    "key_topics": ["deep learning", "neural networks", "AI"],
    "word_count": 150
  }' | jq '{
    source_id: .source.id,
    title: .source.title,
    summary_id: .summary.id,
    topics: .summary.key_topics
  }'

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 7. LIST SOURCES (PAGINATED)
# ============================================================================

echo -e "${YELLOW}7. List Sources (Paginated)${NC}"
echo "GET /api/v1/sources?page=1&limit=5"
echo ""

curl -s "$API_URL/api/v1/sources?page=1&limit=5&sort=newest" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    total: .total,
    page: .page,
    limit: .limit,
    has_more: .has_more,
    sources: .data[0:3] | map({
      id: .id,
      title: .title,
      type: .content_type,
      created: .created_at
    })
  }'

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 8. GET SINGLE SOURCE
# ============================================================================

echo -e "${YELLOW}8. Get Single Source (replace SOURCE_ID)${NC}"
echo "GET /api/v1/sources/{source_id}"
echo ""

# You'll need to replace SOURCE_ID with actual ID from previous step
# SOURCE_ID="your-source-id"
# curl -s "$API_URL/api/v1/sources/$SOURCE_ID" \
#   -H "Authorization: Bearer $TOKEN" | jq '.'

echo "# Replace SOURCE_ID with actual source ID:"
echo "curl -s $API_URL/api/v1/sources/SOURCE_ID \\"
echo "  -H 'Authorization: Bearer $TOKEN' | jq '.'"

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 9. FETCH URL CONTENT
# ============================================================================

echo -e "${YELLOW}9. Fetch URL Content${NC}"
echo "POST /api/v1/fetch-url"
echo ""

curl -s -X POST "$API_URL/api/v1/fetch-url" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://en.wikipedia.org/wiki/Machine_learning"
  }' | jq '{
    url: .url,
    title: .title,
    word_count: .word_count,
    content_preview: (.content | split(" ")[0:30] | join(" "))
  }'

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 10. CREATE COLLECTION
# ============================================================================

echo -e "${YELLOW}10. Create Collection${NC}"
echo "POST /api/v1/collections"
echo ""

curl -s -X POST "$API_URL/api/v1/collections" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ML Research Papers",
    "description": "Collection of important ML papers",
    "is_public": false
  }' | jq '{
    id: .id,
    name: .name,
    description: .description,
    created_at: .created_at
  }'

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 11. LIST COLLECTIONS
# ============================================================================

echo -e "${YELLOW}11. List Collections${NC}"
echo "GET /api/v1/collections"
echo ""

curl -s "$API_URL/api/v1/collections" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    total: .total,
    collections: .data | map({
      id: .id,
      name: .name,
      source_count: .source_count
    })
  }'

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# 12. SEARCH WITHIN COLLECTION
# ============================================================================

echo -e "${YELLOW}12. Search Within Collection (replace COLLECTION_ID)${NC}"
echo "POST /api/v1/search?collection_id=xxx"
echo ""

# You'll need to replace COLLECTION_ID with actual ID
# COLLECTION_ID="your-collection-id"
# curl -s -X POST "$API_URL/api/v1/search" \
#   -H "Authorization: Bearer $TOKEN" \
#   -H "Content-Type: application/json" \
#   -d "{
#     \"query\": \"transformers\",
#     \"mode\": \"hybrid\",
#     \"collection_id\": \"$COLLECTION_ID\"
#   }" | jq '.'

echo "# Replace COLLECTION_ID with actual collection ID:"
echo "curl -s -X POST $API_URL/api/v1/search \\"
echo "  -H 'Authorization: Bearer $TOKEN' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"transformers\", \"collection_id\": \"COLLECTION_ID\"}' | jq '.'"

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# ============================================================================
# COMPLETE RAG WORKFLOW EXAMPLE
# ============================================================================

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Complete RAG Workflow Example${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "# Step 1: Search knowledge base"
echo "RESULTS=\$(curl -s -X POST $API_URL/api/v1/search \\"
echo "  -H 'Authorization: Bearer $TOKEN' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"transformers deep learning\", \"mode\": \"hybrid\", \"limit\": 5}')"
echo ""
echo "# Step 2: Extract context"
echo "CONTEXT=\$(echo \$RESULTS | jq -r '.results[] | \"[\" + .source.title + \"]\\n\" + .summary.summary_text' | head -c 1000)"
echo ""
echo "# Step 3: Use with Claude (example with Claude API)"
echo "curl -s https://api.anthropic.com/v1/messages \\"
echo "  -H 'x-api-key: \$ANTHROPIC_API_KEY' \\"
echo "  -H 'anthropic-version: 2023-06-01' \\"
echo "  -H 'content-type: application/json' \\"
echo "  -d '{
    \"model\": \"claude-3-5-sonnet-20241022\",
    \"max_tokens\": 1024,
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"Context from knowledge base:\\n'\"'\$CONTEXT'\"'\\n\\nQuestion: What are transformers?\"
    }]
  }' | jq -r '.content[0].text'"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${GREEN}✅ Examples complete!${NC}"
echo ""
echo "To use these examples:"
echo "1. Set environment variables: RECALL_API_URL and RECALL_API_TOKEN"
echo "2. Run: ./curl_examples.sh"
echo "3. Or copy individual examples"
echo ""
echo "For agent integration, see:"
echo "  - python_langchain_agent.py"
echo "  - python_custom_agent.py"
echo "  - typescript_agent.ts"
echo ""
