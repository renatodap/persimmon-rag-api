"""
Sources API endpoints.
Handles CRUD operations for sources with AI summarization.
"""
from typing import List

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.auth import CurrentUser
from app.core.errors import handle_api_error
from app.core.rate_limit import RATE_LIMITS, check_rate_limit
from app.models.source import (
    CreateSourceRequest,
    FetchURLRequest,
    FetchURLResponse,
    ProcessPDFResponse,
    SourcesListResponse,
    SourceWithSummaryResponse,
    SummarizeRequest,
    SummarizeResponse,
    UpdateSourceRequest,
    BatchCreateSourcesRequest,
    BatchCreateSourcesResponse,
)
from app.services.ai_service import ai_service
from app.services.content_processor import content_processor
from app.services.embedding_service import embedding_service
from app.services.supabase_service import supabase_service

router = APIRouter()
logger = structlog.get_logger()


@router.post("/sources", response_model=SourceWithSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    request: CreateSourceRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """
    Create a new source with AI summary and embedding.

    Args:
        request: Source creation request
        current_user: Authenticated user

    Returns:
        Created source with summary
    """
    try:
        user_id = current_user["user_id"]

        # Rate limiting
        await check_rate_limit(user_id, RATE_LIMITS["SOURCE_CREATION"])

        # Generate title if not provided
        title = request.title
        if not title or title.strip() == "" or title == "Untitled":
            title = await ai_service.generate_title(request.original_content, request.content_type)

        # Create source
        supabase = supabase_service.get_client()
        source_data = {
            "user_id": user_id,
            "title": title,
            "content_type": request.content_type,
            "original_content": request.original_content,
            "url": request.url,
        }

        source_result = supabase.table("sources").insert(source_data).execute()
        source = source_result.data[0]

        # Generate embedding
        text_to_embed = f"{request.summary_text} {' '.join(request.key_topics)}"
        embedding_result = await embedding_service.generate_embedding(text_to_embed, "summary")

        # Create summary with embedding
        summary_data = {
            "source_id": source["id"],
            "summary_text": request.summary_text,
            "key_actions": request.key_actions,
            "key_topics": request.key_topics,
            "word_count": request.word_count,
            "embedding": embedding_result["embedding"],
        }

        summary_result = supabase.table("summaries").insert(summary_data).execute()
        summary = summary_result.data[0]

        # Create tags
        if request.key_topics:
            tags_data = [
                {"source_id": source["id"], "tag_name": topic.lower()}
                for topic in request.key_topics
            ]
            supabase.table("tags").insert(tags_data).execute()

        logger.info("source_created", source_id=source["id"], user_id=user_id)

        return JSONResponse(
            content={"source": source, "summary": summary},
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error("create_source_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)


@router.get("/sources", response_model=SourcesListResponse)
async def list_sources(
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    content_type: str = Query(None),
    sort: str = Query("newest"),
    tags: str = Query(None),
    tag_logic: str = Query("OR"),
    collection_id: str = Query(None),
) -> JSONResponse:
    """
    List all sources for authenticated user with pagination and filtering.
    """
    try:
        user_id = current_user["user_id"]

        # Rate limiting
        await check_rate_limit(user_id, RATE_LIMITS["SEARCH"])

        supabase = supabase_service.get_client()

        # Build query
        query = supabase.table("sources").select(
            "*, summary:summaries(*), tags:tags(*)", count="exact"
        ).eq("user_id", user_id)

        # Apply filters
        if content_type:
            query = query.eq("content_type", content_type)

        # Apply sorting
        query = query.order("created_at", desc=(sort == "newest"))

        # Apply pagination
        from_idx = (page - 1) * limit
        to_idx = from_idx + limit - 1
        query = query.range(from_idx, to_idx)

        result = query.execute()

        return JSONResponse(
            content={
                "data": result.data,
                "total": result.count or 0,
                "page": page,
                "limit": limit,
                "has_more": (result.count or 0) > page * limit,
                "filters": {"content_type": content_type, "sort": sort},
            }
        )

    except Exception as e:
        logger.error("list_sources_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)


@router.get("/sources/{source_id}")
async def get_source(
    source_id: str,
    current_user: CurrentUser,
) -> JSONResponse:
    """Get a single source by ID."""
    try:
        user_id = current_user["user_id"]
        supabase = supabase_service.get_client()

        result = supabase.table("sources").select(
            "*, summary:summaries(*), tags:tags(*)"
        ).eq("id", source_id).eq("user_id", user_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

        return JSONResponse(content=result.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_source_error", error=str(e), source_id=source_id)
        return handle_api_error(e)


@router.patch("/sources/{source_id}")
async def update_source(
    source_id: str,
    request: UpdateSourceRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """Update a source."""
    try:
        user_id = current_user["user_id"]
        supabase = supabase_service.get_client()

        # Verify ownership
        check = supabase.table("sources").select("id").eq("id", source_id).eq(
            "user_id", user_id
        ).single().execute()

        if not check.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

        # Update
        update_data = request.model_dump(exclude_unset=True)
        update_data["updated_at"] = "now()"

        result = supabase.table("sources").update(update_data).eq("id", source_id).execute()

        logger.info("source_updated", source_id=source_id, user_id=user_id)

        return JSONResponse(content=result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_source_error", error=str(e), source_id=source_id)
        return handle_api_error(e)


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: str,
    current_user: CurrentUser,
) -> None:
    """Delete a source."""
    try:
        user_id = current_user["user_id"]
        supabase = supabase_service.get_client()

        # Delete (cascade will handle summaries and tags)
        result = supabase.table("sources").delete().eq("id", source_id).eq(
            "user_id", user_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

        logger.info("source_deleted", source_id=source_id, user_id=user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_source_error", error=str(e), source_id=source_id)
        raise


@router.post("/fetch-url", response_model=FetchURLResponse)
async def fetch_url(
    request: FetchURLRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """Fetch content from URL."""
    try:
        user_id = current_user["user_id"]
        result = await content_processor.fetch_url(request.url)

        logger.info("url_fetched", url=request.url, user_id=user_id)

        return JSONResponse(content=result)

    except Exception as e:
        logger.error("fetch_url_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)


@router.post("/process-pdf", response_model=ProcessPDFResponse)
async def process_pdf(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> JSONResponse:
    """Process PDF file and extract text."""
    try:
        user_id = current_user["user_id"]

        # Read file content
        file_content = await file.read()

        result = await content_processor.process_pdf(file_content, file.filename or "document.pdf")

        logger.info("pdf_processed", filename=file.filename, user_id=user_id)

        return JSONResponse(content=result)

    except Exception as e:
        logger.error("process_pdf_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_content(
    request: SummarizeRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """Generate AI summary for content."""
    try:
        user_id = current_user["user_id"]

        # Rate limiting
        await check_rate_limit(user_id, RATE_LIMITS["AI_SUMMARY"])

        result = await ai_service.generate_summary(request.content, request.content_type)

        logger.info("content_summarized", user_id=user_id, word_count=result["wordCount"])

        return JSONResponse(
            content={
                "summary": result["summary"],
                "key_actions": result["keyActions"],
                "topics": result["topics"],
                "word_count": result["wordCount"],
            }
        )

    except Exception as e:
        logger.error("summarize_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)


@router.post("/sources/batch", response_model=BatchCreateSourcesResponse, status_code=status.HTTP_201_CREATED)
async def create_batch_sources(
    request: BatchCreateSourcesRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """
    Create multiple sources in batch.

    Processes up to 50 sources sequentially with individual error handling.
    Each source gets AI-generated title (if missing), embedding, and tags.

    Args:
        request: Batch of sources to create
        current_user: Authenticated user

    Returns:
        Batch results with success/failure per source
    """
    try:
        user_id = current_user["user_id"]

        # Rate limiting
        await check_rate_limit(user_id, RATE_LIMITS["SOURCE_CREATION"])

        logger.info("batch_source_creation_started", user_id=user_id, count=len(request.items))

        results = []
        supabase = supabase_service.get_client()

        # Process each source sequentially (could be parallel, but db constraints)
        for item in request.items:
            try:
                # Generate title if not provided
                title = item.title
                if not title or title.strip() == "" or title == "Untitled":
                    title = await ai_service.generate_title(item.original_content, item.content_type)

                # Create source
                source_data = {
                    "user_id": user_id,
                    "title": title,
                    "content_type": item.content_type,
                    "original_content": item.original_content,
                    "url": item.url,
                }

                source_result = supabase.table("sources").insert(source_data).execute()
                source = source_result.data[0]

                # Generate embedding
                text_to_embed = f"{item.summary_text} {' '.join(item.key_topics)}"
                embedding_result = await embedding_service.generate_embedding(text_to_embed, "summary")

                # Create summary with embedding
                summary_data = {
                    "source_id": source["id"],
                    "summary_text": item.summary_text,
                    "key_actions": item.key_actions,
                    "key_topics": item.key_topics,
                    "word_count": item.word_count,
                    "embedding": embedding_result["embedding"],
                }

                summary_result = supabase.table("summaries").insert(summary_data).execute()
                summary = summary_result.data[0]

                # Create tags
                if item.key_topics:
                    tags_data = [
                        {"source_id": source["id"], "tag_name": topic.lower()}
                        for topic in item.key_topics
                    ]
                    supabase.table("tags").insert(tags_data).execute()

                # Success result
                results.append({
                    "index": item.index,
                    "success": True,
                    "source_id": source["id"],
                    "error": None,
                    "source": {"source": source, "summary": summary},
                })

                logger.info("batch_source_created", source_id=source["id"], index=item.index)

            except Exception as item_error:
                # Failure result
                logger.warning("batch_source_failed", index=item.index, error=str(item_error))
                results.append({
                    "index": item.index,
                    "success": False,
                    "source_id": None,
                    "error": str(item_error),
                    "source": None,
                })

        # Calculate statistics
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful

        logger.info(
            "batch_source_creation_complete",
            user_id=user_id,
            total=len(results),
            successful=successful,
            failed=failed,
        )

        return JSONResponse(
            content={
                "results": results,
                "total": len(results),
                "successful": successful,
                "failed": failed,
            },
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error("create_batch_sources_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)
