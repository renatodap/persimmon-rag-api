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
from app.models.embedding import GenerateEmbeddingRequest, GenerateEmbeddingResponse
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
