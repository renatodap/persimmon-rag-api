"""
Pydantic models for embedding generation.
"""
from typing import List, Literal

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
