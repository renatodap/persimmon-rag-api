"""
Custom exception classes and error handlers.
Provides user-friendly error messages and proper HTTP status codes.
"""
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class RecallNotebookException(Exception):
    """Base exception for Recall Notebook backend."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(RecallNotebookException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed. Please sign in."):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ValidationError(RecallNotebookException):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class DatabaseError(RecallNotebookException):
    """Raised when database operation fails."""

    def __init__(self, message: str = "Database operation failed. Please try again."):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class RateLimitError(RecallNotebookException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)
        self.retry_after = retry_after


class NotFoundError(RecallNotebookException):
    """Raised when resource is not found."""

    def __init__(self, message: str = "Resource not found."):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class AIServiceError(RecallNotebookException):
    """Raised when AI service call fails."""

    def __init__(self, message: str = "AI service temporarily unavailable. Please try again."):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE)


async def recall_notebook_exception_handler(
    request: Request, exc: RecallNotebookException
) -> JSONResponse:
    """Handle custom RecallNotebook exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
        headers={"Retry-After": str(exc.retry_after)} if isinstance(exc, RateLimitError) else {},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPExceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected error occurred. Please try again."},
    )


def handle_api_error(error: Exception) -> JSONResponse:
    """
    Utility function to handle errors in route handlers.
    Converts exceptions to user-friendly JSON responses.
    """
    if isinstance(error, RecallNotebookException):
        return JSONResponse(
            status_code=error.status_code,
            content={"error": error.message},
        )
    elif isinstance(error, HTTPException):
        return JSONResponse(
            status_code=error.status_code,
            content={"error": error.detail},
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "An unexpected error occurred. Please try again."},
        )
