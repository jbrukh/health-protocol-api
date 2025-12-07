"""Tests for sleep endpoints."""
import pytest

from app.database import get_db


class TestSleepEndpoints:
    """Tests for sleep API endpoints."""

    @pytest.mark.asyncio
    async def test_get_sleep_not_found(self, client, auth_headers):
        """Test getting sleep when none exists for date."""
        response = await client.get(
            "/sleep",
            params={"date": "2024-01-15"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_sleep_by_date(self, client, auth_headers, test_db):
        """Test getting sleep for a specific date."""
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO sleep (date, duration_minutes, deep_minutes, light_minutes, rem_minutes, awake_minutes, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("2024-01-15", 420, 90, 240, 60, 30, "manual"),
            )
            await db.commit()

        response = await client.get(
            "/sleep",
            params={"date": "2024-01-15"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["duration_minutes"] == 420
        assert data["deep_minutes"] == 90
        assert data["light_minutes"] == 240

    @pytest.mark.asyncio
    async def test_get_latest_none(self, client, auth_headers):
        """Test getting latest when no sleep exists."""
        response = await client.get("/sleep/latest", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_latest(self, client, auth_headers, test_db):
        """Test getting the most recent sleep."""
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO sleep (date, duration_minutes, source)
                VALUES (?, ?, ?), (?, ?, ?)
                """,
                (
                    "2024-01-14", 380, "manual",
                    "2024-01-15", 450, "withings",
                ),
            )
            await db.commit()

        response = await client.get("/sleep/latest", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2024-01-15"
        assert data["duration_minutes"] == 450

    @pytest.mark.asyncio
    async def test_get_sleep_with_timestamps(self, client, auth_headers, test_db):
        """Test getting sleep with start/end timestamps."""
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO sleep (date, sleep_start, sleep_end, duration_minutes, source)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("2024-01-15", "2024-01-14T23:00:00", "2024-01-15T07:00:00", 480, "withings"),
            )
            await db.commit()

        response = await client.get(
            "/sleep",
            params={"date": "2024-01-15"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sleep_start"] is not None
        assert data["sleep_end"] is not None

    @pytest.mark.asyncio
    async def test_get_sleep_requires_auth(self, client):
        """Test that auth is required."""
        response = await client.get("/sleep")
        assert response.status_code == 401
