"""
Authentication and authorization using JWT tokens from Supabase.
Validates JWT tokens and extracts user information.
"""
from typing import Annotated

import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.core.errors import AuthenticationError

security = HTTPBearer()


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """
    Extract and validate JWT token from Authorization header.
    Returns user information (user_id, email).

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        dict: User information with user_id and email

    Raises:
        AuthenticationError: If token is missing, invalid, or expired
    """
    if not authorization:
        raise AuthenticationError("Authorization header missing. Please sign in.")

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise AuthenticationError("Invalid authorization scheme. Use Bearer token.")
    except ValueError:
        raise AuthenticationError("Invalid authorization header format.")

    # Decode JWT token
    try:
        # Supabase uses HS256 algorithm
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},  # Supabase tokens don't have audience
        )

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id:
            raise AuthenticationError("Invalid token: missing user ID.")

        return {
            "user_id": user_id,
            "email": email or "",
        }

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired. Please sign in again.")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


# Dependency for routes that require authentication
CurrentUser = Annotated[dict[str, str], Depends(get_current_user)]
