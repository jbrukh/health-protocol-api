import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint (no auth required)."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_protected_endpoint_no_token(client):
    """Test protected endpoint returns 401 without token."""
    response = await client.get("/profile")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_wrong_token(client):
    """Test protected endpoint returns 401 with wrong token."""
    response = await client.get("/profile", headers={"Authorization": "Bearer wrong-token"})
    assert response.status_code == 401
