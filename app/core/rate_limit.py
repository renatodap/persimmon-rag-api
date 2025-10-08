"""
Rate limiting using Redis.
Prevents abuse and ensures fair usage across all users.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import redis.asyncio as redis
import structlog

from app.config import settings
from app.core.errors import RateLimitError

logger = structlog.get_logger()


@dataclass
class RateLimit:
    """Rate limit configuration."""

    requests: int  # Maximum number of requests
    window: int  # Time window in seconds
    name: str  # Rate limit name for logging


# Rate limit configurations
RATE_LIMITS = {
    "SOURCE_CREATION": RateLimit(requests=100, window=3600, name="source_creation"),  # 100/hour
    "SEARCH": RateLimit(requests=1000, window=3600, name="search"),  # 1000/hour
    "EMBEDDINGS": RateLimit(requests=500, window=3600, name="embeddings"),  # 500/hour
    "AI_SUMMARY": RateLimit(requests=200, window=3600, name="ai_summary"),  # 200/hour
}


class RateLimiter:
    """Redis-based rate limiter."""

    def __init__(self) -> None:
        """Initialize Redis connection."""
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )

    async def check_rate_limit(
        self, user_id: str, rate_limit: RateLimit
    ) -> tuple[bool, int]:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User's unique identifier
            rate_limit: Rate limit configuration

        Returns:
            tuple: (is_limited, retry_after_seconds)
        """
        if not self.redis_client:
            await self.connect()

        key = f"rate_limit:{rate_limit.name}:{user_id}"
        now = datetime.utcnow()

        try:
            # Get current count
            count = await self.redis_client.get(key)

            if count is None:
                # First request in window
                await self.redis_client.setex(key, rate_limit.window, "1")
                logger.info(
                    "rate_limit_check",
                    user_id=user_id,
                    rate_limit=rate_limit.name,
                    count=1,
                    limit=rate_limit.requests,
                )
                return False, 0

            current_count = int(count)

            if current_count >= rate_limit.requests:
                # Rate limit exceeded
                ttl = await self.redis_client.ttl(key)
                logger.warning(
                    "rate_limit_exceeded",
                    user_id=user_id,
                    rate_limit=rate_limit.name,
                    count=current_count,
                    limit=rate_limit.requests,
                    retry_after=ttl,
                )
                return True, ttl

            # Increment counter
            await self.redis_client.incr(key)
            logger.info(
                "rate_limit_check",
                user_id=user_id,
                rate_limit=rate_limit.name,
                count=current_count + 1,
                limit=rate_limit.requests,
            )
            return False, 0

        except Exception as e:
            # If Redis fails, allow the request (fail open)
            logger.error("rate_limit_error", error=str(e), user_id=user_id)
            return False, 0

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(user_id: str, rate_limit: RateLimit) -> None:
    """
    Check rate limit and raise exception if exceeded.

    Args:
        user_id: User's unique identifier
        rate_limit: Rate limit configuration

    Raises:
        RateLimitError: If rate limit is exceeded
    """
    is_limited, retry_after = await rate_limiter.check_rate_limit(user_id, rate_limit)

    if is_limited:
        raise RateLimitError(
            f"Too many requests. Please try again in {retry_after} seconds.",
            retry_after=retry_after,
        )
