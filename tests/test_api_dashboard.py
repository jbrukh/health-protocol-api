"""API tests for dashboard endpoint."""

import pytest
from datetime import date
from httpx import AsyncClient


class TestDashboardAPI:
    @pytest.fixture
    async def setup_dashboard_data(self, client: AsyncClient, api_headers: dict) -> dict:
        """Set up data for dashboard testing."""
        today = str(date.today())

        # Create ingredient
        ing_data = {
            "name": "Chicken Breast",
            "serving_size": 100,
            "serving_unit": "g",
            "protein_g": 31,
            "carbs_g": 0,
            "fat_g": 3.6,
            "sodium_mg": 74,
            "calories": 165,
        }
        ing_response = await client.post(
            "/api/v1/ingredients", json=ing_data, headers=api_headers
        )
        ingredient = ing_response.json()

        # Log food
        food_data = {
            "date": today,
            "ingredient_id": ingredient["id"],
            "quantity": 200,
            "unit": "g",
            "meal_label": "lunch",
        }
        await client.post("/api/v1/food", json=food_data, headers=api_headers)

        # Create targets
        targets = [
            {"name": "calories", "value": 2000, "unit": "kcal", "effective_from": today},
            {"name": "protein_g", "value": 150, "unit": "g", "effective_from": today},
        ]
        for target in targets:
            await client.post("/api/v1/targets", json=target, headers=api_headers)

        return {"ingredient": ingredient, "date": today}

    async def test_get_dashboard(
        self, client: AsyncClient, api_headers: dict, setup_dashboard_data: dict
    ):
        """Test getting dashboard data."""
        today = setup_dashboard_data["date"]
        response = await client.get(
            "/api/v1/dashboard", params={"date": today}, headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()

        # Check structure
        assert "date" in result
        assert "food_summary" in result
        assert "food_entries" in result
        assert "target_progress" in result

        # Check food summary
        assert result["food_summary"]["date"] == today
        assert result["food_summary"]["entry_count"] == 1
        # 200g chicken = 2x serving
        assert result["food_summary"]["total_protein_g"] == 62  # 31 * 2
        assert result["food_summary"]["total_calories"] == 330  # 165 * 2

        # Check food entries
        assert len(result["food_entries"]) == 1
        assert result["food_entries"][0]["meal_label"] == "lunch"

        # Check target progress
        assert len(result["target_progress"]) == 2

        # Find calorie target progress
        calorie_progress = next(
            tp for tp in result["target_progress"] if tp["target"]["name"] == "calories"
        )
        assert calorie_progress["current_value"] == 330
        assert calorie_progress["remaining"] == 1670  # 2000 - 330
        assert calorie_progress["percent_complete"] == 16.5  # 330/2000 * 100

    async def test_get_dashboard_default_today(
        self, client: AsyncClient, api_headers: dict, setup_dashboard_data: dict
    ):
        """Test that dashboard defaults to today."""
        response = await client.get("/api/v1/dashboard", headers=api_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["date"] == str(date.today())

    async def test_get_dashboard_empty_day(
        self, client: AsyncClient, api_headers: dict
    ):
        """Test dashboard for a day with no data."""
        response = await client.get(
            "/api/v1/dashboard",
            params={"date": "2020-01-01"},
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["food_summary"]["entry_count"] == 0
        assert result["food_summary"]["total_calories"] == 0
        assert len(result["food_entries"]) == 0
