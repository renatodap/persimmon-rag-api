"""
Embeddings API endpoint.
Generate embeddings for text using Gemini (FREE) + OpenAI fallback.
"""
import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.auth import CurrentUser
from app.core.errors import handle_api_error
from app.core.rate_limit import RATE_LIMITS, check_rate_limit
from app.models.embedding import (
    GenerateEmbeddingRequest,
    GenerateEmbeddingResponse,
    BatchGenerateEmbeddingRequest,
    BatchGenerateEmbeddingResponse,
)
from app.services.embedding_service import embedding_service

router = APIRouter()
logger = structlog.get_logger()


@router.post("/embeddings/generate", response_model=GenerateEmbeddingResponse)
async def generate_embedding(
    request: GenerateEmbeddingRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """
    Generate embedding for text.

    Uses Gemini (FREE tier, 1500/day) with OpenAI as fallback.

    Args:
        request: Text and embedding type
        current_user: Authenticated user

    Returns:
        Generated embedding vector
    """
    try:
        user_id = current_user["user_id"]

        # Rate limiting
        await check_rate_limit(user_id, RATE_LIMITS["EMBEDDINGS"])

        result = await embedding_service.generate_embedding(request.text, request.type)

        logger.info(
            "embedding_generated",
            user_id=user_id,
            provider=result["provider"],
            tokens=result["tokens"],
        )

        return JSONResponse(
            content={
                "embedding": result["embedding"],
                "model": result["model"],
                "tokens": result["tokens"],
            }
        )

    except Exception as e:
        logger.error("generate_embedding_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)


@router.post("/embeddings/batch", response_model=BatchGenerateEmbeddingResponse)
async def generate_batch_embeddings(
    request: BatchGenerateEmbeddingRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """
    Generate embeddings for multiple texts in parallel.

    Processes up to 100 texts in a single request using Gemini (FREE) + OpenAI fallback.
    Each item is processed independently - some may succeed while others fail.

    Args:
        request: Batch of texts to embed
        current_user: Authenticated user

    Returns:
        Batch results with success/failure per item
    """
    try:
        user_id = current_user["user_id"]

        # Rate limiting (higher limit for batch operations)
        await check_rate_limit(user_id, RATE_LIMITS["EMBEDDINGS"])

        # Convert Pydantic models to dicts for service
        items = [item.model_dump() for item in request.items]

        # Generate embeddings in parallel
        result = await embedding_service.generate_batch_embeddings(items)

        logger.info(
            "batch_embeddings_generated",
            user_id=user_id,
            total=result["total"],
            successful=result["successful"],
            failed=result["failed"],
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(
            "generate_batch_embeddings_error",
            error=str(e),
            user_id=current_user["user_id"],
        )
        return handle_api_error(e)
