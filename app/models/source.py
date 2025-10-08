"""
Pydantic models for source-related operations.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CreateSourceRequest(BaseModel):
    """Request model for creating a source."""

    title: Optional[str] = Field(None, max_length=500, description="Source title")
    content_type: str = Field(..., description="Content type: text, url, pdf, image")
    original_content: str = Field(..., min_length=1, description="Original content text")
    url: Optional[str] = Field(None, description="Source URL if applicable")
    summary_text: str = Field(..., min_length=1, description="AI-generated summary")
    key_actions: List[str] = Field(default_factory=list, description="Key actions extracted")
    key_topics: List[str] = Field(default_factory=list, description="Key topics/tags")
    word_count: int = Field(..., ge=0, description="Word count of original content")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content type."""
        allowed = ["text", "url", "pdf", "image"]
        if v not in allowed:
            raise ValueError(f"content_type must be one of {allowed}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introduction to Machine Learning",
                "content_type": "url",
                "original_content": "Machine learning is a subset of AI...",
                "url": "https://example.com/ml-intro",
                "summary_text": "This article introduces core ML concepts...",
                "key_actions": ["Learn Python", "Study algorithms", "Practice with datasets"],
                "key_topics": ["machine learning", "AI", "python"],
                "word_count": 1500,
            }
        }


class UpdateSourceRequest(BaseModel):
    """Request model for updating a source."""

    title: Optional[str] = Field(None, max_length=500)
    original_content: Optional[str] = None
    url: Optional[str] = None

    class Config:
        json_schema_extra = {"example": {"title": "Updated Title"}}


class SourceResponse(BaseModel):
    """Response model for source data."""

    id: str
    user_id: str
    title: str
    content_type: str
    original_content: str
    url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    """Response model for summary data."""

    id: str
    source_id: str
    summary_text: str
    key_actions: List[str]
    key_topics: List[str]
    word_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SourceWithSummaryResponse(BaseModel):
    """Response model for source with summary."""

    source: SourceResponse
    summary: SummaryResponse


class GetSourcesQueryParams(BaseModel):
    """Query parameters for listing sources."""

    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    content_type: Optional[str] = Field(None, description="Filter by content type")
    sort: str = Field("newest", description="Sort order: newest, oldest")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    tag_logic: str = Field("OR", description="Tag filter logic: AND, OR")
    collection_id: Optional[str] = Field(None, description="Filter by collection ID")

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v: str) -> str:
        """Validate sort parameter."""
        if v not in ["newest", "oldest"]:
            raise ValueError("sort must be 'newest' or 'oldest'")
        return v

    @field_validator("tag_logic")
    @classmethod
    def validate_tag_logic(cls, v: str) -> str:
        """Validate tag logic."""
        if v not in ["AND", "OR"]:
            raise ValueError("tag_logic must be 'AND' or 'OR'")
        return v


class SourcesListResponse(BaseModel):
    """Response model for paginated sources list."""

    data: List[dict]
    total: int
    page: int
    limit: int
    has_more: bool
    filters: dict = Field(default_factory=dict)


class FetchURLRequest(BaseModel):
    """Request model for fetching URL content."""

    url: str = Field(..., description="URL to fetch")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    class Config:
        json_schema_extra = {"example": {"url": "https://example.com/article"}}


class FetchURLResponse(BaseModel):
    """Response model for fetched URL content."""

    url: str
    title: str
    content: str
    word_count: int
    content_type: str = "url"


class ProcessPDFRequest(BaseModel):
    """Request model for PDF processing."""

    # File will be uploaded as multipart/form-data
    # No Pydantic model needed for file itself


class ProcessPDFResponse(BaseModel):
    """Response model for processed PDF."""

    filename: str
    content: str
    word_count: int
    page_count: int
    content_type: str = "pdf"


class SummarizeRequest(BaseModel):
    """Request model for AI summarization."""

    content: str = Field(..., min_length=50, max_length=50000, description="Content to summarize")
    content_type: str = Field("text", description="Content type for context")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """Validate content type."""
        allowed = ["text", "url", "pdf", "image"]
        if v not in allowed:
            raise ValueError(f"content_type must be one of {allowed}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "content": "This is a long article about machine learning...",
                "content_type": "text",
            }
        }


class SummarizeResponse(BaseModel):
    """Response model for AI summary."""

    summary: str
    key_actions: List[str]
    topics: List[str]
    word_count: int
