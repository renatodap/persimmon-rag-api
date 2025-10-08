"""
Pydantic models for collection-related operations.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateCollectionRequest(BaseModel):
    """Request model for creating a collection."""

    name: str = Field(..., min_length=1, max_length=200, description="Collection name")
    description: Optional[str] = Field(None, max_length=1000, description="Collection description")
    is_public: bool = Field(False, description="Whether collection is public")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Machine Learning Resources",
                "description": "Articles and papers about ML",
                "is_public": False,
            }
        }


class UpdateCollectionRequest(BaseModel):
    """Request model for updating a collection."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None


class CollectionResponse(BaseModel):
    """Response model for collection data."""

    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    is_public: bool
    created_at: datetime
    updated_at: datetime
    source_count: int = 0

    class Config:
        from_attributes = True


class AddSourceToCollectionRequest(BaseModel):
    """Request model for adding source to collection."""

    source_id: str = Field(..., description="Source ID to add")

    class Config:
        json_schema_extra = {"example": {"source_id": "123e4567-e89b-12d3-a456-426614174000"}}


class CollectionsListResponse(BaseModel):
    """Response model for list of collections."""

    data: List[CollectionResponse]
    total: int


class CollectionWithSourcesResponse(BaseModel):
    """Response model for collection with its sources."""

    collection: CollectionResponse
    sources: List[dict]
