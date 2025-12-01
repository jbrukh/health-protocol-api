"""API tests for exercises endpoints."""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient


class TestExercisesAPI:
    @pytest.fixture
    async def sample_exercise(self, client: AsyncClient, api_headers: dict) -> dict:
        """Create a sample exercise for testing."""
        data = {
            "date": str(date.today()),
            "exercise_type": "running",
            "duration_minutes": 30,
            "metadata_json": {"distance_km": 5, "avg_pace": "6:00"},
            "notes": "Morning run",
        }
        response = await client.post("/api/v1/exercises", json=data, headers=api_headers)
        return response.json()

    async def test_create_exercise(self, client: AsyncClient, api_headers: dict):
        """Test creating a new exercise."""
        data = {
            "date": str(date.today()),
            "exercise_type": "weight_training",
            "duration_minutes": 45,
            "metadata_json": {"exercises": ["squats", "deadlifts", "bench press"]},
            "notes": "Leg day",
        }
        response = await client.post("/api/v1/exercises", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["exercise_type"] == "weight_training"
        assert result["duration_minutes"] == 45
        assert "squats" in result["metadata_json"]["exercises"]

    async def test_create_exercise_minimal(self, client: AsyncClient, api_headers: dict):
        """Test creating exercise with minimal data."""
        data = {
            "date": str(date.today()),
            "exercise_type": "walking",
        }
        response = await client.post("/api/v1/exercises", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["exercise_type"] == "walking"
        assert result["duration_minutes"] is None

    async def test_get_exercises_by_date(
        self, client: AsyncClient, api_headers: dict, sample_exercise: dict
    ):
        """Test getting exercises for a specific date."""
        today = str(date.today())
        response = await client.get(
            "/api/v1/exercises", params={"date": today}, headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) >= 1
        assert any(e["id"] == sample_exercise["id"] for e in result)

    async def test_get_exercises_by_range(
        self, client: AsyncClient, api_headers: dict, sample_exercise: dict
    ):
        """Test getting exercises for a date range."""
        today = date.today()
        start = str(today - timedelta(days=7))
        end = str(today)

        response = await client.get(
            "/api/v1/exercises",
            params={"start": start, "end": end},
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    async def test_get_exercises_default_range(
        self, client: AsyncClient, api_headers: dict, sample_exercise: dict
    ):
        """Test that exercises default to last 30 days."""
        response = await client.get("/api/v1/exercises", headers=api_headers)

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    async def test_get_exercise(
        self, client: AsyncClient, api_headers: dict, sample_exercise: dict
    ):
        """Test getting a specific exercise."""
        response = await client.get(
            f"/api/v1/exercises/{sample_exercise['id']}", headers=api_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == sample_exercise["id"]
        assert result["exercise_type"] == "running"

    async def test_update_exercise(
        self, client: AsyncClient, api_headers: dict, sample_exercise: dict
    ):
        """Test updating an exercise."""
        update_data = {
            "duration_minutes": 45,
            "notes": "Extended run",
        }
        response = await client.patch(
            f"/api/v1/exercises/{sample_exercise['id']}",
            json=update_data,
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["duration_minutes"] == 45
        assert result["notes"] == "Extended run"

    async def test_delete_exercise(
        self, client: AsyncClient, api_headers: dict, sample_exercise: dict
    ):
        """Test deleting an exercise."""
        response = await client.delete(
            f"/api/v1/exercises/{sample_exercise['id']}", headers=api_headers
        )
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(
            f"/api/v1/exercises/{sample_exercise['id']}", headers=api_headers
        )
        assert get_response.status_code == 404
