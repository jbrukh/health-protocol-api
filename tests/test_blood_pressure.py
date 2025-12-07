"""Tests for blood pressure endpoints."""
import pytest
from datetime import date, datetime

from app.database import get_db


class TestBloodPressureEndpoints:
    """Tests for blood pressure API endpoints."""

    @pytest.mark.asyncio
    async def test_get_readings_empty(self, client, auth_headers):
        """Test getting readings when none exist."""
        response = await client.get("/blood-pressure", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["readings"] == []

    @pytest.mark.asyncio
    async def test_get_readings_by_date_range(self, client, auth_headers, test_db):
        """Test getting readings for a date range."""
        # Insert test data directly
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO blood_pressure (date, time, systolic, diastolic, heart_rate, source)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("2024-01-15", "08:30:00", 120, 80, 72, "manual"),
            )
            await db.commit()

        response = await client.get(
            "/blood-pressure",
            params={"start_date": "2024-01-15", "end_date": "2024-01-15"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["readings"]) == 1
        assert data["readings"][0]["systolic"] == 120
        assert data["readings"][0]["diastolic"] == 80

    @pytest.mark.asyncio
    async def test_get_latest_none(self, client, auth_headers):
        """Test getting latest when no readings exist."""
        response = await client.get("/blood-pressure/latest", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_latest(self, client, auth_headers, test_db):
        """Test getting the most recent reading."""
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO blood_pressure (date, time, systolic, diastolic, heart_rate, source)
                VALUES (?, ?, ?, ?, ?, ?), (?, ?, ?, ?, ?, ?)
                """,
                (
                    "2024-01-14", "08:00:00", 118, 78, 70, "manual",
                    "2024-01-15", "09:00:00", 122, 82, 74, "withings",
                ),
            )
            await db.commit()

        response = await client.get("/blood-pressure/latest", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == "2024-01-15"
        assert data["systolic"] == 122

    @pytest.mark.asyncio
    async def test_get_readings_requires_auth(self, client):
        """Test that auth is required."""
        response = await client.get("/blood-pressure")
        assert response.status_code == 401
