"""API tests for supplements endpoints."""

import pytest
from httpx import AsyncClient


class TestSupplementsAPI:
    @pytest.fixture
    async def sample_supplement(self, client: AsyncClient, api_headers: dict) -> dict:
        """Create a sample supplement for testing."""
        data = {
            "name": "Vitamin D3",
            "dosage": 5000,
            "dosage_unit": "IU",
            "time_of_day": "morning",
            "with_food": True,
            "notes": "Take with breakfast",
        }
        response = await client.post("/api/v1/supplements", json=data, headers=api_headers)
        return response.json()

    async def test_create_supplement(self, client: AsyncClient, api_headers: dict):
        """Test creating a new supplement."""
        data = {
            "name": "Omega-3",
            "dosage": 1000,
            "dosage_unit": "mg",
            "time_of_day": "morning",
            "with_food": True,
        }
        response = await client.post("/api/v1/supplements", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Omega-3"
        assert result["dosage"] == 1000
        assert result["is_active"] is True

    async def test_list_active_supplements(
        self, client: AsyncClient, api_headers: dict, sample_supplement: dict
    ):
        """Test listing active supplements."""
        response = await client.get("/api/v1/supplements", headers=api_headers)

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert all(s["is_active"] for s in result)

    async def test_list_all_supplements(
        self, client: AsyncClient, api_headers: dict, sample_supplement: dict
    ):
        """Test listing all supplements including inactive."""
        # First deactivate the supplement
        await client.delete(
            f"/api/v1/supplements/{sample_supplement['id']}", headers=api_headers
        )

        response = await client.get("/api/v1/supplements/all", headers=api_headers)

        assert response.status_code == 200
        result = response.json()
        assert any(not s["is_active"] for s in result)

    async def test_get_supplement(
        self, client: AsyncClient, api_headers: dict, sample_supplement: dict
    ):
        """Test getting a specific supplement."""
        response = await client.get(
            f"/api/v1/supplements/{sample_supplement['id']}", headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == sample_supplement["id"]
        assert result["name"] == "Vitamin D3"

    async def test_update_supplement(
        self, client: AsyncClient, api_headers: dict, sample_supplement: dict
    ):
        """Test updating a supplement."""
        update_data = {"dosage": 10000, "notes": "Increased dosage"}
        response = await client.patch(
            f"/api/v1/supplements/{sample_supplement['id']}",
            json=update_data,
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["dosage"] == 10000
        assert result["notes"] == "Increased dosage"

    async def test_deactivate_supplement(
        self, client: AsyncClient, api_headers: dict, sample_supplement: dict
    ):
        """Test deactivating (soft delete) a supplement."""
        response = await client.delete(
            f"/api/v1/supplements/{sample_supplement['id']}", headers=api_headers
        )
        assert response.status_code == 204

        # Verify it's inactive but still exists
        get_response = await client.get(
            f"/api/v1/supplements/{sample_supplement['id']}", headers=api_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False

    async def test_reactivate_supplement(
        self, client: AsyncClient, api_headers: dict, sample_supplement: dict
    ):
        """Test reactivating a supplement."""
        # First deactivate
        await client.delete(
            f"/api/v1/supplements/{sample_supplement['id']}", headers=api_headers
        )

        # Then reactivate via update
        response = await client.patch(
            f"/api/v1/supplements/{sample_supplement['id']}",
            json={"is_active": True},
            headers=api_headers,
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is True
