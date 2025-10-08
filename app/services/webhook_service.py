"""
Webhook service for delivering real-time event notifications.
Includes HMAC signature verification and retry logic.
"""
import asyncio
import hashlib
import hmac
import json
import time
from typing import Dict, List, Optional

import httpx
import structlog

from app.config import settings
from app.core.errors import WebhookError
from app.services.supabase_service import supabase_service

logger = structlog.get_logger()


class WebhookService:
    """Service for managing and delivering webhooks."""

    def __init__(self) -> None:
        """Initialize webhook service."""
        self.timeout = 5  # 5 second timeout
        self.max_retries = 3
        self.retry_delays = [1, 3, 5]  # Exponential backoff in seconds

    async def register_webhook(
        self, user_id: str, url: str, events: List[str], secret: Optional[str] = None
    ) -> Dict:
        """
        Register a new webhook for a user.

        Args:
            user_id: User's unique identifier
            url: Webhook delivery URL
            events: List of event types to subscribe to
            secret: Optional secret for HMAC signature

        Returns:
            dict: Created webhook data
        """
        supabase = supabase_service.get_client()

        webhook_data = {
            "user_id": user_id,
            "url": url,
            "events": events,
            "secret": secret,
            "is_active": True,
        }

        result = supabase.table("webhooks").insert(webhook_data).execute()

        logger.info(
            "webhook_registered",
            user_id=user_id,
            webhook_id=result.data[0]["id"],
            events=events,
        )

        return result.data[0]

    async def get_user_webhooks(self, user_id: str) -> List[Dict]:
        """
        Get all webhooks for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            list: User's webhooks
        """
        supabase = supabase_service.get_client()

        result = supabase.table("webhooks").select("*").eq("user_id", user_id).execute()

        return result.data

    async def delete_webhook(self, user_id: str, webhook_id: str) -> bool:
        """
        Delete a webhook.

        Args:
            user_id: User's unique identifier
            webhook_id: Webhook ID to delete

        Returns:
            bool: Success status
        """
        supabase = supabase_service.get_client()

        result = (
            supabase.table("webhooks")
            .delete()
            .eq("id", webhook_id)
            .eq("user_id", user_id)
            .execute()
        )

        if result.data:
            logger.info("webhook_deleted", user_id=user_id, webhook_id=webhook_id)
            return True

        return False

    async def trigger_webhook(
        self, user_id: str, event: str, data: Dict
    ) -> None:
        """
        Trigger webhooks for a specific event.

        Args:
            user_id: User ID who triggered the event
            event: Event type (e.g., "source.created")
            data: Event-specific data
        """
        # Get user's active webhooks for this event
        webhooks = await self._get_webhooks_for_event(user_id, event)

        if not webhooks:
            logger.debug("no_webhooks_found", user_id=user_id, event=event)
            return

        # Build payload
        payload = {
            "event": event,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "data": data,
            "user_id": user_id,
        }

        # Deliver to all webhooks concurrently
        tasks = [
            self._deliver_webhook(webhook, payload) for webhook in webhooks
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    async def test_webhook(self, user_id: str, webhook_id: str) -> Dict:
        """
        Test webhook delivery.

        Args:
            user_id: User's unique identifier
            webhook_id: Webhook ID to test

        Returns:
            dict: Test result with status and timing
        """
        supabase = supabase_service.get_client()

        # Get webhook
        webhook_result = (
            supabase.table("webhooks")
            .select("*")
            .eq("id", webhook_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not webhook_result.data:
            raise WebhookError("Webhook not found")

        webhook = webhook_result.data

        # Test payload
        payload = {
            "event": "webhook.test",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "data": {"message": "This is a test webhook delivery"},
            "user_id": user_id,
        }

        # Attempt delivery
        start_time = time.time()

        try:
            signature = self._generate_signature(
                payload, webhook.get("secret") or settings.WEBHOOK_SECRET
            )

            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": "webhook.test",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook["url"],
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )

            response_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "webhook_test_success",
                webhook_id=webhook_id,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
            )

            return {
                "success": True,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "error": None,
            }

        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)

            logger.error(
                "webhook_test_failed",
                webhook_id=webhook_id,
                error=str(e),
                response_time_ms=response_time_ms,
            )

            return {
                "success": False,
                "status_code": None,
                "response_time_ms": response_time_ms,
                "error": str(e),
            }

    async def _get_webhooks_for_event(
        self, user_id: str, event: str
    ) -> List[Dict]:
        """Get active webhooks subscribed to an event."""
        supabase = supabase_service.get_client()

        result = (
            supabase.table("webhooks")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .contains("events", [event])
            .execute()
        )

        return result.data

    async def _deliver_webhook(self, webhook: Dict, payload: Dict) -> None:
        """
        Deliver webhook with retry logic.

        Args:
            webhook: Webhook configuration
            payload: Event payload to deliver
        """
        webhook_id = webhook["id"]
        url = webhook["url"]
        secret = webhook.get("secret") or settings.WEBHOOK_SECRET

        # Generate HMAC signature
        signature = self._generate_signature(payload, secret)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": payload["event"],
        }

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout,
                    )

                if response.status_code < 300:
                    logger.info(
                        "webhook_delivered",
                        webhook_id=webhook_id,
                        event=payload["event"],
                        status_code=response.status_code,
                        attempt=attempt + 1,
                    )
                    return

                logger.warning(
                    "webhook_delivery_failed",
                    webhook_id=webhook_id,
                    status_code=response.status_code,
                    attempt=attempt + 1,
                )

            except Exception as e:
                logger.warning(
                    "webhook_delivery_error",
                    webhook_id=webhook_id,
                    error=str(e),
                    attempt=attempt + 1,
                )

            # Exponential backoff (except on last attempt)
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delays[attempt])

        # All retries failed
        logger.error(
            "webhook_delivery_exhausted",
            webhook_id=webhook_id,
            event=payload["event"],
            attempts=self.max_retries,
        )

    def _generate_signature(self, payload: Dict, secret: str) -> str:
        """
        Generate HMAC-SHA256 signature for payload.

        Args:
            payload: Webhook payload
            secret: Secret key for signing

        Returns:
            str: Hexadecimal signature
        """
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return f"sha256={signature}"

    @staticmethod
    def verify_signature(payload: Dict, signature: str, secret: str) -> bool:
        """
        Verify HMAC signature from incoming webhook.

        Args:
            payload: Webhook payload
            signature: Signature from X-Webhook-Signature header
            secret: Secret key for verification

        Returns:
            bool: True if signature is valid
        """
        payload_str = json.dumps(payload, sort_keys=True)
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        expected = f"sha256={expected_signature}"

        return hmac.compare_digest(signature, expected)


# Global webhook service instance
webhook_service = WebhookService()
