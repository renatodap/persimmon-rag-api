"""
Pydantic models for search operations.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    mode: Literal["semantic", "keyword", "hybrid"] = Field(
        "hybrid", description="Search mode"
    )
    limit: int = Field(20, ge=1, le=100, description="Maximum results")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")
    collection_id: Optional[str] = Field(None, description="Filter by collection")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning algorithms",
                "mode": "hybrid",
                "limit": 20,
                "threshold": 0.7,
            }
        }


class SearchResultItem(BaseModel):
    """Individual search result."""

    source: dict
    summary: dict
    relevance_score: float
    match_type: Literal["semantic", "keyword", "hybrid"]
    matched_content: str


class SearchResponse(BaseModel):
    """Response model for search results."""

    results: List[SearchResultItem]
    total: int
    search_mode: Literal["semantic", "keyword", "hybrid"]
