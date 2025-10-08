"""
Pydantic models for embedding generation.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class GenerateEmbeddingRequest(BaseModel):
    """Request model for embedding generation."""

    text: str = Field(..., min_length=1, max_length=8000, description="Text to embed")
    type: Literal["summary", "query"] = Field("summary", description="Embedding type")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is a summary of a machine learning article...",
                "type": "summary",
            }
        }


class GenerateEmbeddingResponse(BaseModel):
    """Response model for generated embedding."""

    embedding: List[float]
    model: str
    tokens: int


# Batch Embeddings Models


class BatchEmbeddingItem(BaseModel):
    """Single item in batch embedding request."""

    text: str = Field(..., min_length=1, max_length=8000, description="Text to embed")
    type: Literal["summary", "query"] = Field("summary", description="Embedding type")
    index: int = Field(..., ge=0, description="Index in batch for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Machine learning article summary",
                "type": "summary",
                "index": 0,
            }
        }


class BatchGenerateEmbeddingRequest(BaseModel):
    """Request model for batch embedding generation."""

    items: List[BatchEmbeddingItem] = Field(
        ..., min_length=1, max_length=100, description="List of texts to embed (max 100)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"text": "First document summary", "type": "summary", "index": 0},
                    {"text": "Second document summary", "type": "summary", "index": 1},
                ]
            }
        }


class BatchEmbeddingResult(BaseModel):
    """Result for a single item in batch."""

    index: int = Field(..., description="Original index from request")
    embedding: Optional[List[float]] = Field(None, description="Generated embedding vector")
    model: Optional[str] = Field(None, description="Model used for generation")
    tokens: Optional[int] = Field(None, description="Number of tokens processed")
    success: bool = Field(..., description="Whether embedding generation succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchGenerateEmbeddingResponse(BaseModel):
    """Response model for batch embedding generation."""

    results: List[BatchEmbeddingResult]
    total: int = Field(..., description="Total items in batch")
    successful: int = Field(..., description="Number of successful embeddings")
    failed: int = Field(..., description="Number of failed embeddings")
    provider: str = Field(..., description="Primary provider used (gemini/openai)")

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "index": 0,
                        "embedding": [0.1, 0.2, 0.3],
                        "model": "models/embedding-001",
                        "tokens": 10,
                        "success": True,
                        "error": None,
                    }
                ],
                "total": 1,
                "successful": 1,
                "failed": 0,
                "provider": "gemini",
            }
        }
