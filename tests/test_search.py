"""
Tests for Search API endpoint.
"""
import pytest


class TestSearchAPI:
    """Test suite for search endpoint."""

    @pytest.mark.asyncio
    async def test_search_unauthenticated(self, client):
        """Test search without authentication."""
        response = client.post(
            "/api/v1/search",
            json={
                "query": "machine learning",
                "mode": "hybrid",
            },
        )
        assert response.status_code == 401

    # Add more tests:
    # - test_semantic_search
    # - test_keyword_search
    # - test_hybrid_search
    # - test_search_with_collection_filter
