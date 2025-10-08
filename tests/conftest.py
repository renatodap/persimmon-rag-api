"""
Pytest fixtures and configuration.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
    }


@pytest.fixture
def auth_headers(mock_user):
    """Mock authentication headers."""
    # In real tests, generate a proper JWT token
    return {"Authorization": "Bearer mock-jwt-token"}
