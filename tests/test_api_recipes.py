"""API tests for recipes endpoints."""

import pytest
from datetime import date
from httpx import AsyncClient


class TestRecipesAPI:
    @pytest.fixture
    async def sample_ingredients(self, client: AsyncClient, api_headers: dict) -> list:
        """Create sample ingredients for recipe testing."""
        ingredients = [
            {
                "name": "Banana",
                "serving_size": 100,
                "serving_unit": "g",
                "protein_g": 1,
                "carbs_g": 23,
                "fat_g": 0,
                "sodium_mg": 1,
                "calories": 89,
            },
            {
                "name": "Protein Powder",
                "serving_size": 30,
                "serving_unit": "g",
                "protein_g": 25,
                "carbs_g": 3,
                "fat_g": 1,
                "sodium_mg": 150,
                "calories": 120,
            },
            {
                "name": "Almond Milk",
                "serving_size": 240,
                "serving_unit": "ml",
                "protein_g": 1,
                "carbs_g": 1,
                "fat_g": 3,
                "sodium_mg": 170,
                "calories": 30,
            },
        ]
        created = []
        for ing in ingredients:
            response = await client.post("/api/v1/ingredients", json=ing, headers=api_headers)
            created.append(response.json())
        return created

    @pytest.fixture
    async def sample_recipe(
        self, client: AsyncClient, api_headers: dict, sample_ingredients: list
    ) -> dict:
        """Create a sample recipe."""
        data = {
            "name": "Protein Shake",
            "description": "Post-workout shake",
            "ingredients": [
                {"ingredient_id": sample_ingredients[0]["id"], "quantity": 100, "unit": "g"},
                {"ingredient_id": sample_ingredients[1]["id"], "quantity": 30, "unit": "g"},
                {"ingredient_id": sample_ingredients[2]["id"], "quantity": 240, "unit": "ml"},
            ],
        }
        response = await client.post("/api/v1/recipes", json=data, headers=api_headers)
        return response.json()

    async def test_create_recipe(
        self, client: AsyncClient, api_headers: dict, sample_ingredients: list
    ):
        """Test creating a new recipe."""
        data = {
            "name": "Simple Smoothie",
            "ingredients": [
                {"ingredient_id": sample_ingredients[0]["id"], "quantity": 100, "unit": "g"},
            ],
        }
        response = await client.post("/api/v1/recipes", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Simple Smoothie"
        assert len(result["ingredients"]) == 1
        assert result["total_protein_g"] == 1
        assert result["total_calories"] == 89

    async def test_create_recipe_with_computed_nutrition(
        self, client: AsyncClient, api_headers: dict, sample_ingredients: list
    ):
        """Test that recipe nutrition is computed correctly."""
        data = {
            "name": "Full Shake",
            "ingredients": [
                {"ingredient_id": sample_ingredients[0]["id"], "quantity": 100, "unit": "g"},
                {"ingredient_id": sample_ingredients[1]["id"], "quantity": 30, "unit": "g"},
                {"ingredient_id": sample_ingredients[2]["id"], "quantity": 240, "unit": "ml"},
            ],
        }
        response = await client.post("/api/v1/recipes", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        # Banana: 1g protein, Protein powder: 25g, Almond milk: 1g = 27g total
        assert result["total_protein_g"] == 27
        # 89 + 120 + 30 = 239
        assert result["total_calories"] == 239

    async def test_create_recipe_invalid_ingredient(self, client: AsyncClient, api_headers: dict):
        """Test creating recipe with non-existent ingredient."""
        data = {
            "name": "Invalid Recipe",
            "ingredients": [
                {"ingredient_id": 99999, "quantity": 100, "unit": "g"},
            ],
        }
        response = await client.post("/api/v1/recipes", json=data, headers=api_headers)

        assert response.status_code == 400

    async def test_list_recipes(
        self, client: AsyncClient, api_headers: dict, sample_recipe: dict
    ):
        """Test listing all recipes."""
        response = await client.get("/api/v1/recipes", headers=api_headers)

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) >= 1
        assert any(r["id"] == sample_recipe["id"] for r in result)

    async def test_get_recipe(
        self, client: AsyncClient, api_headers: dict, sample_recipe: dict
    ):
        """Test getting a specific recipe."""
        response = await client.get(
            f"/api/v1/recipes/{sample_recipe['id']}", headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == sample_recipe["id"]
        assert result["name"] == "Protein Shake"
        assert len(result["ingredients"]) == 3

    async def test_update_recipe(
        self, client: AsyncClient, api_headers: dict, sample_recipe: dict
    ):
        """Test updating a recipe."""
        update_data = {
            "name": "Updated Protein Shake",
            "description": "Better version",
        }
        response = await client.patch(
            f"/api/v1/recipes/{sample_recipe['id']}",
            json=update_data,
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated Protein Shake"
        assert result["description"] == "Better version"

    async def test_delete_recipe(
        self, client: AsyncClient, api_headers: dict, sample_recipe: dict
    ):
        """Test deleting a recipe."""
        response = await client.delete(
            f"/api/v1/recipes/{sample_recipe['id']}", headers=api_headers
        )
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            f"/api/v1/recipes/{sample_recipe['id']}", headers=api_headers
        )
        assert get_response.status_code == 404

    async def test_log_recipe(
        self, client: AsyncClient, api_headers: dict, sample_recipe: dict
    ):
        """Test logging a recipe as food entries."""
        today = str(date.today())
        response = await client.post(
            f"/api/v1/recipes/{sample_recipe['id']}/log",
            params={"date": today, "meal_label": "breakfast"},
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == 3  # 3 ingredients in recipe
        assert all(e["meal_label"] == "breakfast" for e in result)

    async def test_log_recipe_with_servings(
        self, client: AsyncClient, api_headers: dict, sample_recipe: dict
    ):
        """Test logging a recipe with multiple servings."""
        today = str(date.today())
        response = await client.post(
            f"/api/v1/recipes/{sample_recipe['id']}/log",
            params={"date": today, "servings": 2},
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        # Quantities should be doubled
        assert result[0]["quantity"] == 200  # Banana was 100g
