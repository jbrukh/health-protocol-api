"""API tests for food tracking endpoints."""

import pytest
from datetime import date
from httpx import AsyncClient


class TestFoodAPI:
    @pytest.fixture
    async def sample_ingredient(self, client: AsyncClient, api_headers: dict) -> dict:
        """Create a sample ingredient for testing."""
        data = {
            "name": "Eggs",
            "serving_size": 50,
            "serving_unit": "g",
            "protein_g": 6,
            "carbs_g": 0.5,
            "fat_g": 5,
            "sodium_mg": 70,
            "calories": 72,
        }
        response = await client.post("/api/v1/ingredients", json=data, headers=api_headers)
        return response.json()

    async def test_log_food_with_ingredient(
        self, client: AsyncClient, api_headers: dict, sample_ingredient: dict
    ):
        """Test logging food with an ingredient reference."""
        data = {
            "date": str(date.today()),
            "ingredient_id": sample_ingredient["id"],
            "quantity": 100,
            "unit": "g",
            "meal_label": "breakfast",
        }
        response = await client.post("/api/v1/food", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["ingredient_id"] == sample_ingredient["id"]
        assert result["quantity"] == 100
        # Should be 2x the serving (100g / 50g)
        assert result["protein_g"] == 12
        assert result["calories"] == 144

    async def test_log_food_with_manual_macros(self, client: AsyncClient, api_headers: dict):
        """Test logging food with manual macro entry."""
        data = {
            "date": str(date.today()),
            "quantity": 1,
            "unit": "serving",
            "description": "Restaurant meal",
            "protein_g": 30,
            "carbs_g": 50,
            "fat_g": 20,
            "sodium_mg": 800,
            "calories": 500,
            "meal_label": "lunch",
        }
        response = await client.post("/api/v1/food", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["description"] == "Restaurant meal"
        assert result["protein_g"] == 30
        assert result["calories"] == 500

    async def test_log_food_invalid_ingredient(self, client: AsyncClient, api_headers: dict):
        """Test logging food with non-existent ingredient."""
        data = {
            "date": str(date.today()),
            "ingredient_id": 99999,
            "quantity": 100,
            "unit": "g",
        }
        response = await client.post("/api/v1/food", json=data, headers=api_headers)

        assert response.status_code == 404

    async def test_get_food_entries(
        self, client: AsyncClient, api_headers: dict, sample_ingredient: dict
    ):
        """Test getting food entries for a date."""
        # First log some food
        today = str(date.today())
        data = {
            "date": today,
            "ingredient_id": sample_ingredient["id"],
            "quantity": 50,
            "unit": "g",
        }
        await client.post("/api/v1/food", json=data, headers=api_headers)

        # Get entries
        response = await client.get(
            "/api/v1/food", params={"date": today}, headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) >= 1

    async def test_get_daily_summary(
        self, client: AsyncClient, api_headers: dict, sample_ingredient: dict
    ):
        """Test getting daily macro summary."""
        today = str(date.today())

        # Log multiple foods
        for _ in range(2):
            data = {
                "date": today,
                "ingredient_id": sample_ingredient["id"],
                "quantity": 50,
                "unit": "g",
            }
            await client.post("/api/v1/food", json=data, headers=api_headers)

        response = await client.get(
            "/api/v1/food/summary", params={"date": today}, headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["date"] == today
        assert result["entry_count"] == 2
        # 2 entries x 1 serving each = 2x the nutrition
        assert result["total_protein_g"] == 12  # 6 * 2
        assert result["total_calories"] == 144  # 72 * 2

    async def test_get_calorie_history(
        self, client: AsyncClient, api_headers: dict, sample_ingredient: dict
    ):
        """Test getting calorie history for date range."""
        today = str(date.today())

        # Log food
        data = {
            "date": today,
            "ingredient_id": sample_ingredient["id"],
            "quantity": 50,
            "unit": "g",
        }
        await client.post("/api/v1/food", json=data, headers=api_headers)

        response = await client.get(
            "/api/v1/food/history",
            params={"start": today, "end": today},
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["date"] == today

    async def test_update_food_entry(
        self, client: AsyncClient, api_headers: dict, sample_ingredient: dict
    ):
        """Test updating a food entry."""
        # Create entry
        today = str(date.today())
        data = {
            "date": today,
            "ingredient_id": sample_ingredient["id"],
            "quantity": 50,
            "unit": "g",
        }
        create_response = await client.post("/api/v1/food", json=data, headers=api_headers)
        entry_id = create_response.json()["id"]

        # Update entry
        update_data = {"quantity": 100, "meal_label": "dinner"}
        response = await client.patch(
            f"/api/v1/food/{entry_id}", json=update_data, headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["quantity"] == 100
        assert result["meal_label"] == "dinner"
        # Nutrition should be recalculated
        assert result["protein_g"] == 12  # 2x

    async def test_delete_food_entry(
        self, client: AsyncClient, api_headers: dict, sample_ingredient: dict
    ):
        """Test deleting a food entry."""
        # Create entry
        today = str(date.today())
        data = {
            "date": today,
            "ingredient_id": sample_ingredient["id"],
            "quantity": 50,
            "unit": "g",
        }
        create_response = await client.post("/api/v1/food", json=data, headers=api_headers)
        entry_id = create_response.json()["id"]

        # Delete entry
        response = await client.delete(f"/api/v1/food/{entry_id}", headers=api_headers)
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            "/api/v1/food", params={"date": today}, headers=api_headers
        )
        entries = get_response.json()
        assert not any(e["id"] == entry_id for e in entries)
