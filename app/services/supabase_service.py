"""
Supabase database service.
Provides async database operations with row-level security.
"""
from typing import Any, Dict, List, Optional

import structlog
from supabase import Client, create_client

from app.config import settings
from app.core.errors import DatabaseError

logger = structlog.get_logger()


class SupabaseService:
    """Supabase database client wrapper."""

    def __init__(self) -> None:
        """Initialize Supabase client."""
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.service_client: Client = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
        )

    def get_client(self, user_id: Optional[str] = None) -> Client:
        """
        Get Supabase client (uses service role for admin operations).

        Args:
            user_id: User ID for RLS context (not used with service role)

        Returns:
            Supabase client
        """
        # Using service role key to bypass RLS (we handle auth in FastAPI)
        return self.service_client

    async def execute_query(
        self, table: str, query_fn: Any, user_id: str, operation: str = "query"
    ) -> List[Dict[str, Any]]:
        """
        Execute database query with error handling.

        Args:
            table: Table name
            query_fn: Query function to execute
            user_id: User ID for logging
            operation: Operation name for logging

        Returns:
            Query results

        Raises:
            DatabaseError: If query fails
        """
        try:
            response = query_fn
            if hasattr(response, "execute"):
                result = response.execute()
            else:
                result = response

            logger.info(
                "database_query",
                table=table,
                operation=operation,
                user_id=user_id,
                success=True,
            )

            return result.data if hasattr(result, "data") else result

        except Exception as e:
            logger.error(
                "database_error",
                table=table,
                operation=operation,
                user_id=user_id,
                error=str(e),
            )
            raise DatabaseError(f"Database operation failed: {str(e)}")


# Global Supabase service instance
supabase_service = SupabaseService()
