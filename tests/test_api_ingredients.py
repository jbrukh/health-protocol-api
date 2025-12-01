"""API tests for ingredients endpoints."""

import pytest
from httpx import AsyncClient


class TestIngredientsAPI:
    @pytest.fixture
    async def sample_ingredient(self, client: AsyncClient, api_headers: dict) -> dict:
        """Create a sample ingredient for testing."""
        data = {
            "name": "Protein Powder",
            "brand": "SunWarrior",
            "serving_size": 30,
            "serving_unit": "g",
            "protein_g": 25,
            "carbs_g": 3,
            "fat_g": 1,
            "sodium_mg": 150,
            "calories": 120,
        }
        response = await client.post("/api/v1/ingredients", json=data, headers=api_headers)
        return response.json()

    async def test_create_ingredient(self, client: AsyncClient, api_headers: dict):
        """Test creating a new ingredient."""
        data = {
            "name": "Oatmeal",
            "serving_size": 40,
            "serving_unit": "g",
            "protein_g": 5,
            "carbs_g": 27,
            "fat_g": 3,
            "sodium_mg": 0,
            "calories": 150,
        }
        response = await client.post("/api/v1/ingredients", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Oatmeal"
        assert result["serving_size"] == 40
        assert result["protein_g"] == 5
        assert result["id"] is not None
        assert result["is_default"] is False

    async def test_create_ingredient_with_brand(self, client: AsyncClient, api_headers: dict):
        """Test creating ingredient with brand."""
        data = {
            "name": "Whey Protein",
            "brand": "Optimum Nutrition",
            "serving_size": 31,
            "serving_unit": "g",
            "protein_g": 24,
            "carbs_g": 3,
            "fat_g": 1,
            "sodium_mg": 130,
            "calories": 120,
        }
        response = await client.post("/api/v1/ingredients", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["brand"] == "Optimum Nutrition"

    async def test_list_ingredients(self, client: AsyncClient, api_headers: dict, sample_ingredient: dict):
        """Test listing all ingredients."""
        response = await client.get("/api/v1/ingredients", headers=api_headers)

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) >= 1
        assert any(i["id"] == sample_ingredient["id"] for i in result)

    async def test_get_ingredient(self, client: AsyncClient, api_headers: dict, sample_ingredient: dict):
        """Test getting a specific ingredient."""
        response = await client.get(
            f"/api/v1/ingredients/{sample_ingredient['id']}", headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == sample_ingredient["id"]
        assert result["name"] == "Protein Powder"

    async def test_get_ingredient_not_found(self, client: AsyncClient, api_headers: dict):
        """Test getting non-existent ingredient."""
        response = await client.get("/api/v1/ingredients/99999", headers=api_headers)

        assert response.status_code == 404

    async def test_update_ingredient(self, client: AsyncClient, api_headers: dict, sample_ingredient: dict):
        """Test updating an ingredient."""
        update_data = {"protein_g": 30, "calories": 130}
        response = await client.patch(
            f"/api/v1/ingredients/{sample_ingredient['id']}",
            json=update_data,
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["protein_g"] == 30
        assert result["calories"] == 130
        # Unchanged fields should remain
        assert result["name"] == "Protein Powder"

    async def test_search_ingredients(self, client: AsyncClient, api_headers: dict, sample_ingredient: dict):
        """Test searching ingredients by name."""
        response = await client.get(
            "/api/v1/ingredients/search", params={"q": "Protein"}, headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert len(result) >= 1
        assert any("Protein" in i["name"] for i in result)

    async def test_search_ingredients_case_insensitive(
        self, client: AsyncClient, api_headers: dict, sample_ingredient: dict
    ):
        """Test that search is case insensitive."""
        response = await client.get(
            "/api/v1/ingredients/search", params={"q": "protein"}, headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert len(result) >= 1

    async def test_set_default_ingredient(
        self, client: AsyncClient, api_headers: dict, sample_ingredient: dict
    ):
        """Test setting an ingredient as default."""
        response = await client.post(
            f"/api/v1/ingredients/{sample_ingredient['id']}/set-default",
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["is_default"] is True

    async def test_unauthorized_access(self, client_no_auth: AsyncClient):
        """Test that unauthorized requests are rejected."""
        response = await client_no_auth.get("/api/v1/ingredients")
        assert response.status_code == 401  # No auth header
