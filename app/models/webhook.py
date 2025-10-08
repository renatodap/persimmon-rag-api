"""
Pydantic models for webhook operations.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class WebhookEvent(str, Enum):
    """Webhook event types."""

    SOURCE_CREATED = "source.created"
    SOURCE_UPDATED = "source.updated"
    SOURCE_DELETED = "source.deleted"
    SEARCH_COMPLETED = "search.completed"
    COLLECTION_CREATED = "collection.created"
    COLLECTION_UPDATED = "collection.updated"


class CreateWebhookRequest(BaseModel):
    """Request model for creating a webhook."""

    url: str = Field(..., description="Webhook delivery URL")
    events: List[WebhookEvent] = Field(
        ..., min_length=1, description="List of events to subscribe to"
    )
    secret: Optional[str] = Field(
        None,
        min_length=16,
        max_length=128,
        description="Optional secret for HMAC signature verification",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate webhook URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://myapp.com/webhooks/recall",
                "events": ["source.created", "source.updated"],
                "secret": "my-webhook-secret-key",
            }
        }


class WebhookResponse(BaseModel):
    """Response model for webhook data."""

    id: str
    user_id: str
    url: str
    events: List[str]
    secret: Optional[str] = None  # Never returned in responses
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """Response model for webhook list."""

    data: List[WebhookResponse]
    total: int


class WebhookPayload(BaseModel):
    """Payload structure sent to webhook URLs."""

    event: str = Field(..., description="Event type (e.g., source.created)")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    data: dict = Field(..., description="Event-specific data")
    user_id: str = Field(..., description="User ID who triggered the event")

    class Config:
        json_schema_extra = {
            "example": {
                "event": "source.created",
                "timestamp": "2025-01-10T12:00:00Z",
                "data": {
                    "source_id": "uuid-here",
                    "title": "New Article",
                    "content_type": "url",
                },
                "user_id": "user-uuid",
            }
        }


class TestWebhookRequest(BaseModel):
    """Request model for testing webhook delivery."""

    webhook_id: str = Field(..., description="Webhook ID to test")

    class Config:
        json_schema_extra = {"example": {"webhook_id": "webhook-uuid"}}


class TestWebhookResponse(BaseModel):
    """Response model for webhook test."""

    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status_code": 200,
                "response_time_ms": 145,
                "error": None,
            }
        }
