"""Tests for activity endpoints."""
import pytest
from datetime import date

from app.database import get_db
from app.utils import timezone as tz_utils


class TestActivityEndpoints:
    """Tests for activity API endpoints."""

    @pytest.mark.asyncio
    async def test_get_activity_empty(self, client, auth_headers):
        """Test getting activity when none exists returns empty list."""
        response = await client.get(
            "/activity",
            params={"start_date": "2024-01-15", "end_date": "2024-01-15"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["activities"] == []
        assert data["total_in_range"] == 0

    @pytest.mark.asyncio
    async def test_get_activity_by_date_range(self, client, auth_headers, test_db):
        """Test getting activity for a date range."""
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO daily_activity (date, steps, distance_miles, active_calories, elevation_ft, source)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("2024-01-15", 10000, 4.5, 350, 100, "manual"),
            )
            await db.commit()

        response = await client.get(
            "/activity",
            params={"start_date": "2024-01-15", "end_date": "2024-01-15"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 1
        assert data["activities"][0]["steps"] == 10000
        assert data["activities"][0]["distance_miles"] == 4.5
        assert data["activities"][0]["active_calories"] == 350

    @pytest.mark.asyncio
    async def test_get_latest_none(self, client, auth_headers):
        """Test getting latest when no activity exists."""
        response = await client.get("/activity/latest", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_latest(self, client, auth_headers, test_db):
        """Test getting the most recent activity."""
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO daily_activity (date, steps, source)
                VALUES (?, ?, ?), (?, ?, ?)
                """,
                (
                    "2024-01-14", 8000, "manual",
                    "2024-01-15", 12000, "withings",
                ),
            )
            await db.commit()

        response = await client.get("/activity/latest", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2024-01-15"
        assert data["steps"] == 12000

    @pytest.mark.asyncio
    async def test_get_activity_requires_auth(self, client):
        """Test that auth is required."""
        response = await client.get("/activity")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_activity_defaults_use_profile_timezone(self, monkeypatch, client, auth_headers, test_db):
        """Default date range should be based on profile timezone-aware 'today'."""
        target_date = "2020-02-01"

        async with get_db() as db:
            await db.execute(
                "INSERT INTO daily_activity (date, steps, source) VALUES (?, ?, ?)",
                (target_date, 5000, "manual"),
            )
            await db.commit()

        from app.routers import activity as activity_router
        monkeypatch.setattr(activity_router, "current_date_in_timezone", lambda tz: date.fromisoformat(target_date))

        response = await client.get("/activity", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(a["date"] == target_date for a in data["activities"])
