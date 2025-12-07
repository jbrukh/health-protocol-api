"""
Tests to improve coverage for previously untested code paths.

Covers:
- Food update operations
- Recipe update operations
- Body measurement update operations
- Input validation edge cases
- Snapshot generation
- HTTP error handling in Withings sync
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch, AsyncMock

import httpx

from app.services import food_service, recipe_service, body_service, snapshot_service
from app.services import withings_sync
from app.database import get_db


class TestFoodUpdateOperations:
    """Tests for food update functionality."""

    @pytest.mark.asyncio
    async def test_update_food(self, client, auth_headers, test_db):
        """Test updating a food entry."""
        # Create a food first
        create_response = await client.post(
            "/foods",
            json={
                "date": "2024-01-15",
                "marker": "breakfast",
                "name": "Original Food",
                "amount": 1.0,
                "unit": "serving",
                "calories": 100,
                "protein_g": 10.0,
                "carbs_g": 10.0,
                "fats_g": 5.0,
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        food_id = create_response.json()["id"]

        # Update it
        update_response = await client.put(
            f"/foods/{food_id}",
            json={"name": "Updated Food", "calories": 200},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Food"
        assert update_response.json()["calories"] == 200


class TestRecipeUpdateOperations:
    """Tests for recipe update functionality."""

    @pytest.mark.asyncio
    async def test_update_recipe_name(self, client, auth_headers, test_db):
        """Test updating a recipe name."""
        # Create ingredient first
        ing_response = await client.post(
            "/ingredients",
            json={
                "name": "Test Ingredient",
                "default_amount": 100,
                "default_unit": "g",
                "calories": 50,
                "protein_g": 5.0,
                "carbs_g": 10.0,
                "fats_g": 1.0,
            },
            headers=auth_headers,
        )
        ingredient_id = ing_response.json()["id"]

        # Create recipe
        recipe_response = await client.post(
            "/recipes",
            json={
                "name": "Original Recipe",
                "items": [{"ingredient_id": ingredient_id, "amount": 100, "unit": "g"}],
            },
            headers=auth_headers,
        )
        recipe_id = recipe_response.json()["id"]

        # Update recipe name
        update_response = await client.put(
            f"/recipes/{recipe_id}",
            json={"name": "Updated Recipe"},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Recipe"

    @pytest.mark.asyncio
    async def test_update_recipe_item(self, client, auth_headers, test_db):
        """Test updating a recipe item."""
        # Create ingredient
        ing_response = await client.post(
            "/ingredients",
            json={
                "name": "Update Test Ingredient",
                "default_amount": 100,
                "default_unit": "g",
                "calories": 50,
                "protein_g": 5.0,
                "carbs_g": 10.0,
                "fats_g": 1.0,
            },
            headers=auth_headers,
        )
        ingredient_id = ing_response.json()["id"]

        # Create recipe with item
        recipe_response = await client.post(
            "/recipes",
            json={
                "name": "Recipe With Item",
                "items": [{"ingredient_id": ingredient_id, "amount": 100, "unit": "g"}],
            },
            headers=auth_headers,
        )
        recipe_id = recipe_response.json()["id"]
        item_id = recipe_response.json()["items"][0]["id"]

        # Update the item
        update_response = await client.put(
            f"/recipes/{recipe_id}/items/{item_id}",
            json={"amount": 200, "unit": "ml"},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["items"][0]["amount"] == 200
        assert update_response.json()["items"][0]["unit"] == "ml"


class TestBodyMeasurementUpdate:
    """Tests for body measurement update functionality."""

    @pytest.mark.asyncio
    async def test_update_body_measurement(self, client, auth_headers, test_db):
        """Test updating a body measurement."""
        # Create measurement
        create_response = await client.post(
            "/body",
            json={
                "date": "2024-01-15",
                "time": "08:00:00",
                "weight_lbs": 180.0,
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        measurement_id = create_response.json()["id"]

        # Update it
        update_response = await client.put(
            f"/body/{measurement_id}",
            json={"weight_lbs": 175.0, "waist_cm": 85.0},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["weight_lbs"] == 175.0
        assert update_response.json()["waist_cm"] == 85.0


class TestInputValidation:
    """Tests for input validation constraints."""

    @pytest.mark.asyncio
    async def test_food_negative_calories_rejected(self, client, auth_headers, test_db):
        """Test that negative calories are rejected."""
        response = await client.post(
            "/foods",
            json={
                "date": "2024-01-15",
                "marker": "test",
                "name": "Bad Food",
                "amount": 1.0,
                "unit": "serving",
                "calories": -100,  # Invalid
                "protein_g": 10.0,
                "carbs_g": 10.0,
                "fats_g": 5.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_food_empty_name_rejected(self, client, auth_headers, test_db):
        """Test that empty name is rejected."""
        response = await client.post(
            "/foods",
            json={
                "date": "2024-01-15",
                "marker": "test",
                "name": "",  # Invalid
                "amount": 1.0,
                "unit": "serving",
                "calories": 100,
                "protein_g": 10.0,
                "carbs_g": 10.0,
                "fats_g": 5.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_food_zero_amount_rejected(self, client, auth_headers, test_db):
        """Test that zero amount is rejected."""
        response = await client.post(
            "/foods",
            json={
                "date": "2024-01-15",
                "marker": "test",
                "name": "Test Food",
                "amount": 0,  # Invalid - must be > 0
                "unit": "serving",
                "calories": 100,
                "protein_g": 10.0,
                "carbs_g": 10.0,
                "fats_g": 5.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_exercise_zero_duration_rejected(self, client, auth_headers, test_db):
        """Test that zero duration is rejected."""
        response = await client.post(
            "/exercises",
            json={
                "date": "2024-01-15",
                "exercise_type": "walk",
                "duration_minutes": 0,  # Invalid
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_supplement_negative_dosage_rejected(self, client, auth_headers, test_db):
        """Test that negative dosage is rejected."""
        response = await client.post(
            "/supplements",
            json={
                "name": "Bad Supplement",
                "dosage_amount": -100,  # Invalid
                "dosage_unit": "mg",
                "purpose": "Testing",
                "time_of_day": "morning",
                "start_date": "2024-01-01",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_body_measurement_extreme_weight_rejected(self, client, auth_headers, test_db):
        """Test that extreme weight values are rejected."""
        response = await client.post(
            "/body",
            json={
                "date": "2024-01-15",
                "time": "08:00:00",
                "weight_lbs": 2000.0,  # Invalid - > 1500
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestSnapshotService:
    """Tests for snapshot service."""

    @pytest.mark.asyncio
    async def test_generate_missing_snapshots(self, test_db):
        """Test generating snapshots for a date range."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 5)

        snapshots = await snapshot_service.generate_missing_snapshots(start, end)

        # Should have 5 days of snapshots
        assert len(snapshots) == 5
        assert start in snapshots
        assert end in snapshots

    @pytest.mark.asyncio
    async def test_get_or_create_snapshot_creates_new(self, test_db):
        """Test that get_or_create creates a new snapshot."""
        test_date = date(2024, 6, 15)

        snapshot = await snapshot_service.get_or_create_snapshot(test_date)

        assert snapshot is not None
        assert snapshot.calories == 0  # No foods for this date

    @pytest.mark.asyncio
    async def test_get_or_create_snapshot_returns_existing(self, test_db):
        """Test that get_or_create returns existing snapshot."""
        test_date = date(2024, 6, 16)

        # Create first
        snapshot1 = await snapshot_service.get_or_create_snapshot(test_date)

        # Get again - should return same
        snapshot2 = await snapshot_service.get_or_create_snapshot(test_date)

        assert snapshot1.calories == snapshot2.calories


class TestWithingsHttpErrorHandling:
    """Tests for HTTP error handling in Withings sync."""

    @pytest.mark.asyncio
    async def test_fetch_measurements_timeout(self, test_db, monkeypatch):
        """Test handling of timeout during fetch."""
        from app.services import withings_service

        # Save a token so we have one to use
        await withings_service.save_tokens(
            access_token="test_token",
            refresh_token="refresh",
            expires_at=date.today() + timedelta(days=1),
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            result = await withings_sync.fetch_measurements(
                date(2024, 1, 1), date(2024, 1, 31)
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_activity_network_error(self, test_db, monkeypatch):
        """Test handling of network error during activity fetch."""
        from app.services import withings_service

        await withings_service.save_tokens(
            access_token="test_token",
            refresh_token="refresh",
            expires_at=date.today() + timedelta(days=1),
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.RequestError("Connection failed")

            result = await withings_sync.fetch_activity(
                date(2024, 1, 1), date(2024, 1, 31)
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_sleep_invalid_json(self, test_db, monkeypatch):
        """Test handling of invalid JSON response."""
        from app.services import withings_service
        from unittest.mock import MagicMock

        await withings_service.save_tokens(
            access_token="test_token",
            refresh_token="refresh",
            expires_at=date.today() + timedelta(days=1),
        )

        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await withings_sync.fetch_sleep(
                date(2024, 1, 1), date(2024, 1, 31)
            )

        assert result == []


class TestExerciseUpdate:
    """Tests for exercise update functionality."""

    @pytest.mark.asyncio
    async def test_update_exercise(self, client, auth_headers, test_db):
        """Test updating an exercise."""
        # Create exercise
        create_response = await client.post(
            "/exercises",
            json={
                "date": "2024-01-15",
                "exercise_type": "walk",
                "duration_minutes": 30,
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        exercise_id = create_response.json()["id"]

        # Update it
        update_response = await client.put(
            f"/exercises/{exercise_id}",
            json={"duration_minutes": 45, "exercise_type": "run"},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["duration_minutes"] == 45
        assert update_response.json()["exercise_type"] == "run"


class TestIngredientUpdate:
    """Tests for ingredient update functionality."""

    @pytest.mark.asyncio
    async def test_update_ingredient(self, client, auth_headers, test_db):
        """Test updating an ingredient."""
        # Create ingredient
        create_response = await client.post(
            "/ingredients",
            json={
                "name": "Original Ingredient",
                "default_amount": 100,
                "default_unit": "g",
                "calories": 50,
                "protein_g": 5.0,
                "carbs_g": 10.0,
                "fats_g": 1.0,
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        ingredient_id = create_response.json()["id"]

        # Update it
        update_response = await client.put(
            f"/ingredients/{ingredient_id}",
            json={"name": "Updated Ingredient", "calories": 75},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Ingredient"
        assert update_response.json()["calories"] == 75
