"""
Embedding service with dual-provider support (Gemini FREE + OpenAI fallback).
Cost-optimized: Uses Gemini's free tier (1500/day) with OpenAI as fallback.
"""
from typing import Dict, List, Literal

import structlog
from google import generativeai as genai
from openai import OpenAI

from app.config import settings
from app.core.errors import AIServiceError

logger = structlog.get_logger()

# Configure Google Gemini
genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)


class EmbeddingService:
    """Dual-provider embedding service (Gemini + OpenAI)."""

    def __init__(self) -> None:
        """Initialize embedding providers."""
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.gemini_model = "models/embedding-001"
        self.openai_model = "text-embedding-3-small"

    async def generate_embedding(
        self,
        text: str,
        embedding_type: Literal["summary", "query"] = "summary",
        normalize: bool = True,
    ) -> Dict[str, any]:
        """
        Generate embedding using Gemini (primary, FREE) with OpenAI fallback.

        Args:
            text: Text to embed
            embedding_type: Type of embedding (summary or query)
            normalize: Whether to normalize the embedding

        Returns:
            dict: {embedding, model, provider, tokens, cost, latency_ms}

        Raises:
            AIServiceError: If both providers fail
        """
        # Try Gemini first (FREE tier)
        try:
            logger.info("embedding_request", provider="gemini", type=embedding_type)

            # Gemini embedding
            result = genai.embed_content(
                model=self.gemini_model,
                content=text,
                task_type="retrieval_document" if embedding_type == "summary" else "retrieval_query",
            )

            embedding = result["embedding"]

            logger.info(
                "embedding_success",
                provider="gemini",
                model=self.gemini_model,
                dimension=len(embedding),
                cost=0.0,  # FREE!
            )

            return {
                "embedding": embedding,
                "model": self.gemini_model,
                "provider": "gemini",
                "tokens": len(text.split()),  # Approximate
                "cost": 0.0,  # FREE tier
                "dimension": len(embedding),
            }

        except Exception as gemini_error:
            logger.warning("gemini_embedding_failed", error=str(gemini_error))

            # Fallback to OpenAI
            try:
                logger.info("embedding_fallback", provider="openai")

                response = self.openai_client.embeddings.create(
                    model=self.openai_model, input=text
                )

                embedding = response.data[0].embedding
                tokens = response.usage.total_tokens
                cost = tokens / 1_000_000 * 0.02  # $0.02 per 1M tokens

                logger.info(
                    "embedding_success",
                    provider="openai",
                    model=self.openai_model,
                    dimension=len(embedding),
                    tokens=tokens,
                    cost=cost,
                )

                return {
                    "embedding": embedding,
                    "model": self.openai_model,
                    "provider": "openai",
                    "tokens": tokens,
                    "cost": cost,
                    "dimension": len(embedding),
                }

            except Exception as openai_error:
                logger.error("embedding_failed", gemini_error=str(gemini_error), openai_error=str(openai_error))
                raise AIServiceError("Failed to generate embedding with both providers")


# Global embedding service instance
embedding_service = EmbeddingService()
