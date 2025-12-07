"""Tests for admin endpoints."""
import pytest

from app.database import get_db


class TestAdminEndpoints:
    """Tests for admin API endpoints."""

    @pytest.mark.asyncio
    async def test_clear_foods(self, client, auth_headers, test_db):
        """Test clearing foods."""
        # Add some foods first
        async with get_db() as db:
            await db.execute(
                "INSERT INTO foods (date, marker, name, amount, unit, calories, protein_g, carbs_g, fats_g) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("2024-01-15", "test", "Test Food", 1, "serving", 100, 10, 10, 5),
            )
            await db.commit()

        response = await client.delete("/admin/clear-foods", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["deleted"] >= 1

    @pytest.mark.asyncio
    async def test_clear_exercises(self, client, auth_headers, test_db):
        """Test clearing exercises."""
        async with get_db() as db:
            await db.execute(
                "INSERT INTO exercises (date, exercise_type, duration_minutes) VALUES (?, ?, ?)",
                ("2024-01-15", "walk", 30),
            )
            await db.commit()

        response = await client.delete("/admin/clear-exercises", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_clear_snapshots(self, client, auth_headers, test_db):
        """Test clearing snapshots."""
        async with get_db() as db:
            await db.execute(
                "INSERT INTO daily_snapshots (date, calories, protein_g, carbs_g, fats_g, sodium_mg) VALUES (?, ?, ?, ?, ?, ?)",
                ("2024-01-15", 1500, 100, 150, 50, 2000),
            )
            await db.commit()

        response = await client.delete("/admin/clear-snapshots", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_clear_body(self, client, auth_headers, test_db):
        """Test clearing body measurements."""
        async with get_db() as db:
            await db.execute(
                "INSERT INTO body_measurements (date, time, weight_lbs) VALUES (?, ?, ?)",
                ("2024-01-15", "08:00:00", 180),
            )
            await db.commit()

        response = await client.delete("/admin/clear-body", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_clear_supplements(self, client, auth_headers, test_db):
        """Test clearing supplements."""
        async with get_db() as db:
            await db.execute(
                "INSERT INTO supplements (name, dosage_amount, dosage_unit, purpose, time_of_day, start_date) VALUES (?, ?, ?, ?, ?, ?)",
                ("Vitamin D", 5000, "IU", "Bone health", "morning", "2024-01-01"),
            )
            await db.commit()

        response = await client.delete("/admin/clear-supplements", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_clear_phases(self, client, auth_headers, test_db):
        """Test clearing phases."""
        async with get_db() as db:
            await db.execute(
                "INSERT INTO phases (name, description, start_date, end_date) VALUES (?, ?, ?, ?)",
                ("Test Phase", "Description", "2024-01-01", "2024-01-31"),
            )
            await db.commit()

        response = await client.delete("/admin/clear-phases", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_clear_blood_pressure(self, client, auth_headers, test_db):
        """Test clearing blood pressure."""
        async with get_db() as db:
            await db.execute(
                "INSERT INTO blood_pressure (date, time, systolic, diastolic, source) VALUES (?, ?, ?, ?, ?)",
                ("2024-01-15", "08:00:00", 120, 80, "manual"),
            )
            await db.commit()

        response = await client.delete("/admin/clear-blood-pressure", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_clear_activity(self, client, auth_headers, test_db):
        """Test clearing activity."""
        async with get_db() as db:
            await db.execute(
                "INSERT INTO daily_activity (date, steps, source) VALUES (?, ?, ?)",
                ("2024-01-15", 10000, "manual"),
            )
            await db.commit()

        response = await client.delete("/admin/clear-activity", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_clear_sleep(self, client, auth_headers, test_db):
        """Test clearing sleep."""
        async with get_db() as db:
            await db.execute(
                "INSERT INTO sleep (date, duration_minutes, source) VALUES (?, ?, ?)",
                ("2024-01-15", 420, "manual"),
            )
            await db.commit()

        response = await client.delete("/admin/clear-sleep", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_clear_all(self, client, auth_headers, test_db):
        """Test clearing all data."""
        async with get_db() as db:
            await db.execute(
                "INSERT INTO foods (date, marker, name, amount, unit, calories, protein_g, carbs_g, fats_g) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("2024-01-15", "test", "Test Food", 1, "serving", 100, 10, 10, 5),
            )
            await db.execute(
                "INSERT INTO blood_pressure (date, time, systolic, diastolic, source) VALUES (?, ?, ?, ?, ?)",
                ("2024-01-15", "08:00:00", 120, 80, "manual"),
            )
            await db.commit()

        response = await client.delete("/admin/clear-all", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["deleted"] >= 2

    @pytest.mark.asyncio
    async def test_admin_requires_auth(self, client):
        """Test that admin endpoints require auth."""
        response = await client.delete("/admin/clear-all")
        assert response.status_code == 401
