"""
Webhooks API endpoints.
Manage real-time event notifications.
"""
import structlog
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.auth import CurrentUser
from app.core.errors import handle_api_error
from app.models.webhook import (
    CreateWebhookRequest,
    TestWebhookRequest,
    TestWebhookResponse,
    WebhookListResponse,
    WebhookResponse,
)
from app.services.webhook_service import webhook_service

router = APIRouter()
logger = structlog.get_logger()


@router.post("/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    request: CreateWebhookRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """
    Register a new webhook for real-time event notifications.

    Webhooks deliver events like source.created, source.updated, etc.
    Payloads are signed with HMAC-SHA256 for verification.

    Args:
        request: Webhook configuration (URL, events, optional secret)
        current_user: Authenticated user

    Returns:
        Created webhook data
    """
    try:
        user_id = current_user["user_id"]

        webhook = await webhook_service.register_webhook(
            user_id=user_id,
            url=request.url,
            events=[e.value for e in request.events],
            secret=request.secret,
        )

        logger.info(
            "webhook_created",
            user_id=user_id,
            webhook_id=webhook["id"],
            events=[e.value for e in request.events],
        )

        return JSONResponse(
            content={
                "id": webhook["id"],
                "user_id": webhook["user_id"],
                "url": webhook["url"],
                "events": webhook["events"],
                "is_active": webhook["is_active"],
                "created_at": webhook["created_at"],
            },
            status_code=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error("create_webhook_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)


@router.get("/webhooks", response_model=WebhookListResponse)
async def list_webhooks(
    current_user: CurrentUser,
) -> JSONResponse:
    """
    List all webhooks for authenticated user.

    Args:
        current_user: Authenticated user

    Returns:
        List of user's webhooks
    """
    try:
        user_id = current_user["user_id"]

        webhooks = await webhook_service.get_user_webhooks(user_id)

        return JSONResponse(
            content={
                "data": [
                    {
                        "id": w["id"],
                        "user_id": w["user_id"],
                        "url": w["url"],
                        "events": w["events"],
                        "is_active": w["is_active"],
                        "created_at": w["created_at"],
                    }
                    for w in webhooks
                ],
                "total": len(webhooks),
            }
        )

    except Exception as e:
        logger.error("list_webhooks_error", error=str(e), user_id=current_user["user_id"])
        return handle_api_error(e)


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    current_user: CurrentUser,
) -> None:
    """
    Delete a webhook.

    Args:
        webhook_id: Webhook ID to delete
        current_user: Authenticated user
    """
    try:
        user_id = current_user["user_id"]

        success = await webhook_service.delete_webhook(user_id, webhook_id)

        if not success:
            return JSONResponse(
                content={"error": "Webhook not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        logger.info("webhook_deleted", user_id=user_id, webhook_id=webhook_id)

    except Exception as e:
        logger.error("delete_webhook_error", error=str(e), webhook_id=webhook_id)
        raise


@router.post("/webhooks/test", response_model=TestWebhookResponse)
async def test_webhook(
    request: TestWebhookRequest,
    current_user: CurrentUser,
) -> JSONResponse:
    """
    Test webhook delivery with a test payload.

    Sends a webhook.test event to verify endpoint connectivity.
    Returns delivery status and response time.

    Args:
        request: Webhook ID to test
        current_user: Authenticated user

    Returns:
        Test result with status and timing
    """
    try:
        user_id = current_user["user_id"]

        result = await webhook_service.test_webhook(user_id, request.webhook_id)

        logger.info(
            "webhook_tested",
            user_id=user_id,
            webhook_id=request.webhook_id,
            success=result["success"],
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(
            "test_webhook_error",
            error=str(e),
            user_id=current_user["user_id"],
            webhook_id=request.webhook_id,
        )
        return handle_api_error(e)
