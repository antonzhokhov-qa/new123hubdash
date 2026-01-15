"""API endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_list_transactions_empty(client: AsyncClient):
    """Test listing transactions when empty."""
    response = await client.get("/api/v1/transactions")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_list_transactions_with_filters(client: AsyncClient):
    """Test listing transactions with filters."""
    response = await client.get(
        "/api/v1/transactions",
        params={
            "source": "vima",
            "status": "success",
            "page": 1,
            "limit": 10,
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_metrics_overview(client: AsyncClient):
    """Test metrics overview endpoint."""
    response = await client.get("/api/v1/metrics/overview")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert "conversion_rate" in data


@pytest.mark.asyncio
async def test_get_sync_status(client: AsyncClient):
    """Test sync status endpoint."""
    response = await client.get("/api/v1/sync/status")
    
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert "overall_status" in data
