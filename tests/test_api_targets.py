"""API tests for targets endpoints."""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient


class TestTargetsAPI:
    @pytest.fixture
    async def sample_targets(self, client: AsyncClient, api_headers: dict) -> list:
        """Create sample targets for testing."""
        today = date.today()
        targets = [
            {
                "name": "calories",
                "value": 2000,
                "unit": "kcal",
                "effective_from": str(today - timedelta(days=30)),
            },
            {
                "name": "calories",
                "value": 2200,
                "unit": "kcal",
                "effective_from": str(today),
            },
            {
                "name": "protein_g",
                "value": 150,
                "unit": "g",
                "effective_from": str(today),
            },
            {
                "name": "sodium_mg",
                "value": 2300,
                "unit": "mg",
                "effective_from": str(today),
            },
        ]
        created = []
        for target in targets:
            response = await client.post("/api/v1/targets", json=target, headers=api_headers)
            created.append(response.json())
        return created

    async def test_create_target(self, client: AsyncClient, api_headers: dict):
        """Test creating a new target."""
        data = {
            "name": "fat_g",
            "value": 65,
            "unit": "g",
            "effective_from": str(date.today()),
        }
        response = await client.post("/api/v1/targets", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "fat_g"
        assert result["value"] == 65
        assert result["id"] is not None

    async def test_get_current_targets(
        self, client: AsyncClient, api_headers: dict, sample_targets: list
    ):
        """Test getting current targets (most recent for each name)."""
        response = await client.get("/api/v1/targets", headers=api_headers)

        assert response.status_code == 200
        result = response.json()
        # Should have 3 unique target names (calories, protein_g, sodium_mg)
        names = [t["name"] for t in result]
        assert "calories" in names
        assert "protein_g" in names
        assert "sodium_mg" in names

        # Calories should be the most recent value (2200)
        calorie_target = next(t for t in result if t["name"] == "calories")
        assert calorie_target["value"] == 2200

    async def test_get_target_history(
        self, client: AsyncClient, api_headers: dict, sample_targets: list
    ):
        """Test getting target change history."""
        response = await client.get("/api/v1/targets/calories/history", headers=api_headers)

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
        # Should be in descending order by effective_from
        assert result[0]["value"] == 2200  # Most recent
        assert result[1]["value"] == 2000  # Older

    async def test_get_target_history_not_found(
        self, client: AsyncClient, api_headers: dict
    ):
        """Test getting history for non-existent target."""
        response = await client.get("/api/v1/targets/nonexistent/history", headers=api_headers)

        assert response.status_code == 404

    async def test_future_target_not_current(
        self, client: AsyncClient, api_headers: dict
    ):
        """Test that future targets don't show as current."""
        # Create a future target
        future_date = str(date.today() + timedelta(days=30))
        data = {
            "name": "future_target",
            "value": 999,
            "unit": "units",
            "effective_from": future_date,
        }
        await client.post("/api/v1/targets", json=data, headers=api_headers)

        # Get current targets
        response = await client.get("/api/v1/targets", headers=api_headers)
        result = response.json()

        # Future target should not be in current targets
        names = [t["name"] for t in result]
        assert "future_target" not in names
