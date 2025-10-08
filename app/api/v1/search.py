"""
Search API endpoint.
Supports semantic, keyword, and hybrid search modes.
"""
from typing import List

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.auth import CurrentUser
from app.core.errors import handle_api_error
from app.core.rate_limit import RATE_LIMITS, check_rate_limit
from app.models.search import SearchRequest, SearchResponse, SearchResultItem
from app.services.embedding_service import embedding_service
from app.services.supabase_service import supabase_service

router = APIRouter()
logger = structlog.get_logger()


@router.post("/search", response_model=SearchResponse)
async def search_sources(
    request: SearchRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """
    Search sources using semantic, keyword, or hybrid mode.

    Args:
        request: Search request with query and parameters
        current_user: Authenticated user

    Returns:
        Search results with relevance scores
    """
    try:
        user_id = current_user["user_id"]

        # Rate limiting
        await check_rate_limit(user_id, RATE_LIMITS["SEARCH"])

        results: List[dict] = []
        supabase = supabase_service.get_client()

        # Semantic or Hybrid Search
        if request.mode in ["semantic", "hybrid"]:
            try:
                # Generate query embedding
                logger.info("search_embedding_request", query=request.query, mode=request.mode)

                embedding_result = await embedding_service.generate_embedding(
                    request.query, "query"
                )

                # Vector search using database function
                semantic_result = supabase.rpc(
                    "match_summaries",
                    {
                        "query_embedding": embedding_result["embedding"],
                        "match_threshold": request.threshold,
                        "match_count": request.limit,
                        "p_user_id": user_id,
                        "p_collection_id": request.collection_id,
                    },
                ).execute()

                if semantic_result.data:
                    results = [
                        {
                            "source": {
                                "id": item["source_id"],
                                "user_id": item["user_id"],
                                "title": item["title"],
                                "content_type": item["content_type"],
                                "original_content": item["original_content"],
                                "url": item.get("url"),
                                "created_at": item["created_at"],
                                "updated_at": item["updated_at"],
                            },
                            "summary": {
                                "id": item["summary_id"],
                                "source_id": item["source_id"],
                                "summary_text": item["summary_text"],
                                "key_actions": item.get("key_actions", []),
                                "key_topics": item.get("key_topics", []),
                                "word_count": item.get("word_count", 0),
                                "created_at": item.get("summary_created_at"),
                            },
                            "relevance_score": item.get("similarity", 0),
                            "match_type": "semantic",
                            "matched_content": item["summary_text"][:200] if item["summary_text"] else "",
                        }
                        for item in semantic_result.data
                    ]

            except Exception as e:
                logger.warning("semantic_search_failed", error=str(e))
                if request.mode == "semantic":
                    # Fall back to keyword search
                    pass

        # Keyword or Hybrid Search
        if request.mode == "keyword" or (request.mode == "hybrid" and len(results) < request.limit):
            search_pattern = f"%{request.query}%"

            keyword_query = (
                supabase.table("sources")
                .select("*, summary:summaries(*)")
                .eq("user_id", user_id)
                .or_(f"title.ilike.{search_pattern},original_content.ilike.{search_pattern}")
                .limit(request.limit)
            )

            keyword_result = keyword_query.execute()

            if keyword_result.data:
                keyword_results = []
                for item in keyword_result.data:
                    # Calculate simple keyword relevance
                    score = 0.0
                    query_lower = request.query.lower()
                    if item.get("title") and query_lower in item["title"].lower():
                        score += 0.3
                    if item.get("original_content") and query_lower in item["original_content"].lower():
                        score += 0.4

                    summary_data = item.get("summary", [{}])[0] if item.get("summary") else {}

                    keyword_results.append(
                        {
                            "source": {
                                "id": item["id"],
                                "user_id": item["user_id"],
                                "title": item["title"],
                                "content_type": item["content_type"],
                                "original_content": item["original_content"],
                                "url": item.get("url"),
                                "created_at": item["created_at"],
                                "updated_at": item["updated_at"],
                            },
                            "summary": summary_data,
                            "relevance_score": score,
                            "match_type": "keyword",
                            "matched_content": item["title"] or "",
                        }
                    )

                # Merge results if hybrid
                if request.mode == "hybrid":
                    # Combine and deduplicate by source ID
                    seen_ids = {r["source"]["id"] for r in results}
                    for kr in keyword_results:
                        if kr["source"]["id"] not in seen_ids:
                            kr["match_type"] = "hybrid"
                            results.append(kr)
                else:
                    results = keyword_results

        # Sort by relevance
        results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)[: request.limit]

        logger.info("search_complete", user_id=user_id, results_count=len(results), mode=request.mode)

        return JSONResponse(
            content={
                "results": results,
                "total": len(results),
                "search_mode": request.mode,
            }
        )

    except Exception as e:
        logger.error("search_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)
