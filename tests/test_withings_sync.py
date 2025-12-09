"""Tests for Withings data synchronization."""
import os
import time
import pytest
from datetime import datetime, date, timezone
from unittest.mock import patch, AsyncMock

from app.services import withings_sync
from app.database import get_db


class TestUnitConversions:
    """Tests for unit conversion functions."""

    def test_kg_to_lbs(self):
        assert abs(withings_sync.kg_to_lbs(1) - 2.20462) < 0.001
        assert abs(withings_sync.kg_to_lbs(100) - 220.462) < 0.01

    def test_meters_to_miles(self):
        assert abs(withings_sync.meters_to_miles(1609.344) - 1.0) < 0.001
        assert abs(withings_sync.meters_to_miles(5000) - 3.107) < 0.01

    def test_meters_to_feet(self):
        assert abs(withings_sync.meters_to_feet(1) - 3.28084) < 0.001
        assert abs(withings_sync.meters_to_feet(100) - 328.084) < 0.01

    def test_parse_withings_value(self):
        # Withings returns values with unit as exponent
        # e.g., weight 75.5kg = value 75500, unit -3
        assert withings_sync.parse_withings_value(75500, -3) == 75.5
        assert withings_sync.parse_withings_value(120, 0) == 120
        assert withings_sync.parse_withings_value(1, 3) == 1000


class TestSyncBodyMeasurements:
    """Tests for body measurement sync."""

    @pytest.mark.asyncio
    async def test_sync_body_measurements_empty(self, test_db):
        """Test syncing empty measurement list."""
        count = await withings_sync.sync_body_measurements([])
        assert count == 0

    @pytest.mark.asyncio
    async def test_sync_body_measurements(self, test_db):
        """Test syncing body measurements."""
        measure_groups = [
            {
                "grpid": 12345,
                "date": int(datetime(2024, 1, 15, 8, 30).timestamp()),
                "measures": [
                    {"type": 1, "value": 80000, "unit": -3},  # 80kg weight
                    {"type": 8, "value": 15000, "unit": -3},  # 15kg fat mass
                ],
            }
        ]

        count = await withings_sync.sync_body_measurements(measure_groups)
        assert count == 1

        # Verify data was stored correctly
        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM body_measurements WHERE withings_id = '12345'")
            row = await cursor.fetchone()

        assert row is not None
        assert abs(row["weight_lbs"] - 176.37) < 0.1  # 80kg in lbs
        assert abs(row["fat_mass_lbs"] - 33.07) < 0.1  # 15kg in lbs
        assert row["source"] == "withings"

    @pytest.mark.asyncio
    async def test_sync_body_measurements_deduplication(self, test_db):
        """Test that duplicate measurements are skipped."""
        measure_groups = [
            {
                "grpid": 12345,
                "date": int(datetime(2024, 1, 15, 8, 30).timestamp()),
                "measures": [{"type": 1, "value": 80000, "unit": -3}],
            }
        ]

        # Sync twice
        count1 = await withings_sync.sync_body_measurements(measure_groups)
        count2 = await withings_sync.sync_body_measurements(measure_groups)

        assert count1 == 1
        assert count2 == 0  # Duplicate skipped

    @pytest.mark.asyncio
    async def test_sync_body_measurements_uses_utc(self, test_db, monkeypatch):
        """Timestamps should be interpreted in UTC regardless of server timezone."""
        original_tz = os.environ.get("TZ")
        os.environ["TZ"] = "US/Pacific"
        try:
            time.tzset()
        except AttributeError:
            # Windows may not support tzset; skip if not available
            pytest.skip("tzset not available on this platform")

        try:
            ts = datetime(2024, 1, 15, 8, 0, tzinfo=timezone.utc).timestamp()
            measure_groups = [
                {
                    "grpid": 54321,
                    "date": int(ts),
                    "measures": [{"type": 1, "value": 80000, "unit": -3}],
                }
            ]

            await withings_sync.sync_body_measurements(measure_groups)
            async with get_db() as db:
                cursor = await db.execute("SELECT date, time FROM body_measurements WHERE withings_id = '54321'")
                row = await cursor.fetchone()

            assert row["date"] == "2024-01-15"
            assert row["time"] == "08:00:00"
        finally:
            if original_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = original_tz
            try:
                time.tzset()
            except AttributeError:
                pass


class TestSyncBloodPressure:
    """Tests for blood pressure sync."""

    @pytest.mark.asyncio
    async def test_sync_blood_pressure(self, test_db):
        """Test syncing blood pressure data."""
        measure_groups = [
            {
                "grpid": 67890,
                "date": int(datetime(2024, 1, 15, 9, 0).timestamp()),
                "measures": [
                    {"type": 10, "value": 120, "unit": 0},  # Systolic
                    {"type": 9, "value": 80, "unit": 0},   # Diastolic
                    {"type": 11, "value": 72, "unit": 0},  # Heart rate
                ],
            }
        ]

        count = await withings_sync.sync_blood_pressure(measure_groups)
        assert count == 1

        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM blood_pressure WHERE withings_id = '67890'")
            row = await cursor.fetchone()

        assert row is not None
        assert row["systolic"] == 120
        assert row["diastolic"] == 80
        assert row["heart_rate"] == 72
        assert row["source"] == "withings"

    @pytest.mark.asyncio
    async def test_sync_blood_pressure_no_hr(self, test_db):
        """Test syncing blood pressure without heart rate."""
        measure_groups = [
            {
                "grpid": 67891,
                "date": int(datetime(2024, 1, 15, 9, 0).timestamp()),
                "measures": [
                    {"type": 10, "value": 118, "unit": 0},
                    {"type": 9, "value": 78, "unit": 0},
                ],
            }
        ]

        count = await withings_sync.sync_blood_pressure(measure_groups)
        assert count == 1

        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM blood_pressure WHERE withings_id = '67891'")
            row = await cursor.fetchone()

        assert row["heart_rate"] is None


class TestSyncActivity:
    """Tests for activity sync."""

    @pytest.mark.asyncio
    async def test_sync_activity(self, test_db):
        """Test syncing activity data."""
        activities = [
            {
                "date": "2024-01-15",
                "steps": 10000,
                "distance": 8000,  # meters
                "calories": 400,
                "elevation": 50,   # meters
            }
        ]

        count = await withings_sync.sync_activity(activities)
        assert count == 1

        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM daily_activity WHERE date = '2024-01-15'")
            row = await cursor.fetchone()

        assert row is not None
        assert row["steps"] == 10000
        assert abs(row["distance_miles"] - 4.97) < 0.1  # 8000m in miles
        assert row["active_calories"] == 400
        assert abs(row["elevation_ft"] - 164.04) < 0.1  # 50m in feet

    @pytest.mark.asyncio
    async def test_sync_activity_upsert(self, test_db):
        """Test that activity data is upserted (updated on same date)."""
        activities1 = [{"date": "2024-01-15", "steps": 5000}]
        activities2 = [{"date": "2024-01-15", "steps": 10000}]

        await withings_sync.sync_activity(activities1)
        await withings_sync.sync_activity(activities2)

        async with get_db() as db:
            cursor = await db.execute("SELECT COUNT(*) as cnt FROM daily_activity WHERE date = '2024-01-15'")
            row = await cursor.fetchone()
            assert row["cnt"] == 1

            cursor = await db.execute("SELECT steps FROM daily_activity WHERE date = '2024-01-15'")
            row = await cursor.fetchone()
            assert row["steps"] == 10000  # Updated value


class TestSyncSleep:
    """Tests for sleep sync."""

    @pytest.mark.asyncio
    async def test_sync_sleep(self, test_db):
        """Test syncing sleep data."""
        sleep_data = [
            {
                "id": 11111,
                "date": "2024-01-15",
                "startdate": int(datetime(2024, 1, 14, 23, 0).timestamp()),
                "enddate": int(datetime(2024, 1, 15, 7, 0).timestamp()),
                "data": {
                    "deepsleepduration": 5400,    # 90 min
                    "lightsleepduration": 14400,  # 240 min
                    "remsleepduration": 5400,     # 90 min
                    "wakeupduration": 1800,       # 30 min
                },
            }
        ]

        count = await withings_sync.sync_sleep(sleep_data)
        assert count == 1

        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM sleep WHERE withings_id = '11111'")
            row = await cursor.fetchone()

        assert row is not None
        assert row["deep_minutes"] == 90
        assert row["light_minutes"] == 240
        assert row["rem_minutes"] == 90
        assert row["awake_minutes"] == 30
        assert row["source"] == "withings"

    @pytest.mark.asyncio
    async def test_sync_sleep_deduplication(self, test_db):
        """Test that duplicate sleep records are skipped."""
        sleep_data = [
            {
                "id": 22222,
                "date": "2024-01-15",
                "startdate": int(datetime(2024, 1, 14, 23, 0).timestamp()),
                "enddate": int(datetime(2024, 1, 15, 7, 0).timestamp()),
                "data": {},
            }
        ]

        count1 = await withings_sync.sync_sleep(sleep_data)
        count2 = await withings_sync.sync_sleep(sleep_data)

        assert count1 == 1
        assert count2 == 0


class TestSyncByAppli:
    """Tests for sync_by_appli dispatcher."""

    @pytest.mark.asyncio
    async def test_sync_by_appli_weight(self, test_db, monkeypatch):
        """Test sync_by_appli for weight (appli 1)."""
        from unittest.mock import AsyncMock

        monkeypatch.setattr(withings_sync, 'fetch_measurements', AsyncMock(return_value=[]))
        count = await withings_sync.sync_by_appli(1)
        assert count == 0

    @pytest.mark.asyncio
    async def test_sync_by_appli_bp(self, test_db, monkeypatch):
        """Test sync_by_appli for blood pressure (appli 4)."""
        from unittest.mock import AsyncMock

        monkeypatch.setattr(withings_sync, 'fetch_measurements', AsyncMock(return_value=[]))
        count = await withings_sync.sync_by_appli(4)
        assert count == 0

    @pytest.mark.asyncio
    async def test_sync_by_appli_activity(self, test_db, monkeypatch):
        """Test sync_by_appli for activity (appli 16)."""
        from unittest.mock import AsyncMock

        monkeypatch.setattr(withings_sync, 'fetch_activity', AsyncMock(return_value=[]))
        count = await withings_sync.sync_by_appli(16)
        assert count == 0

    @pytest.mark.asyncio
    async def test_sync_by_appli_sleep(self, test_db, monkeypatch):
        """Test sync_by_appli for sleep (appli 44)."""
        from unittest.mock import AsyncMock

        monkeypatch.setattr(withings_sync, 'fetch_sleep', AsyncMock(return_value=[]))
        count = await withings_sync.sync_by_appli(44)
        assert count == 0

    @pytest.mark.asyncio
    async def test_sync_by_appli_unknown(self, test_db):
        """Test sync_by_appli with unknown appli code."""
        count = await withings_sync.sync_by_appli(999)
        assert count == 0

    @pytest.mark.asyncio
    async def test_sync_by_appli_with_timestamps(self, test_db, monkeypatch):
        """Test sync_by_appli with explicit start/end timestamps."""
        from unittest.mock import AsyncMock

        mock_fetch = AsyncMock(return_value=[])
        monkeypatch.setattr(withings_sync, 'fetch_measurements', mock_fetch)

        # Jan 15 2024
        start_ts = 1705276800
        end_ts = 1705363200

        await withings_sync.sync_by_appli(1, start_ts, end_ts)
        mock_fetch.assert_called_once()


class TestFetchMeasurements:
    """Tests for fetch_measurements function."""

    @pytest.mark.asyncio
    async def test_fetch_measurements_no_token(self, test_db):
        """Test fetch_measurements with no valid token."""
        result = await withings_sync.fetch_measurements(date(2024, 1, 1), date(2024, 1, 31))
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_measurements_api_error(self, test_db, monkeypatch):
        """Test fetch_measurements handles API errors."""
        from unittest.mock import AsyncMock, MagicMock
        from app.services import withings_service

        # Set up valid token
        monkeypatch.setattr(withings_service, 'get_valid_token', AsyncMock(return_value="valid_token"))

        # Mock API error response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 401}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await withings_sync.fetch_measurements(date(2024, 1, 1), date(2024, 1, 31))

        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_measurements_success(self, test_db, monkeypatch):
        """Test fetch_measurements success."""
        from unittest.mock import AsyncMock, MagicMock
        from app.services import withings_service

        monkeypatch.setattr(withings_service, 'get_valid_token', AsyncMock(return_value="valid_token"))

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": 0,
            "body": {
                "measuregrps": [
                    {"grpid": 123, "date": 1705312800, "measures": []}
                ]
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await withings_sync.fetch_measurements(date(2024, 1, 1), date(2024, 1, 31))

        assert len(result) == 1


class TestFetchActivity:
    """Tests for fetch_activity function."""

    @pytest.mark.asyncio
    async def test_fetch_activity_no_token(self, test_db):
        """Test fetch_activity with no valid token."""
        result = await withings_sync.fetch_activity(date(2024, 1, 1), date(2024, 1, 31))
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_activity_success(self, test_db, monkeypatch):
        """Test fetch_activity success."""
        from unittest.mock import AsyncMock, MagicMock
        from app.services import withings_service

        monkeypatch.setattr(withings_service, 'get_valid_token', AsyncMock(return_value="valid_token"))

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": 0,
            "body": {
                "activities": [
                    {"date": "2024-01-15", "steps": 10000}
                ]
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await withings_sync.fetch_activity(date(2024, 1, 1), date(2024, 1, 31))

        assert len(result) == 1


class TestFetchSleep:
    """Tests for fetch_sleep function."""

    @pytest.mark.asyncio
    async def test_fetch_sleep_no_token(self, test_db):
        """Test fetch_sleep with no valid token."""
        result = await withings_sync.fetch_sleep(date(2024, 1, 1), date(2024, 1, 31))
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_sleep_success(self, test_db, monkeypatch):
        """Test fetch_sleep success."""
        from unittest.mock import AsyncMock, MagicMock
        from app.services import withings_service

        monkeypatch.setattr(withings_service, 'get_valid_token', AsyncMock(return_value="valid_token"))

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": 0,
            "body": {
                "series": [
                    {"id": 123, "date": "2024-01-15"}
                ]
            }
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await withings_sync.fetch_sleep(date(2024, 1, 1), date(2024, 1, 31))

        assert len(result) == 1


class TestBackfillAll:
    """Tests for backfill functionality."""

    @pytest.mark.asyncio
    async def test_backfill_all_no_data(self, test_db, monkeypatch):
        """Test backfill when APIs return no data."""
        from unittest.mock import AsyncMock

        # Mock all fetch functions to return empty lists
        monkeypatch.setattr(withings_sync, 'fetch_measurements', AsyncMock(return_value=[]))
        monkeypatch.setattr(withings_sync, 'fetch_activity', AsyncMock(return_value=[]))
        monkeypatch.setattr(withings_sync, 'fetch_sleep', AsyncMock(return_value=[]))

        counts = await withings_sync.backfill_all(
            date(2024, 1, 1),
            date(2024, 1, 31),
        )

        assert counts["body_measurements"] == 0
        assert counts["blood_pressure"] == 0
        assert counts["daily_activity"] == 0
        assert counts["sleep"] == 0

    @pytest.mark.asyncio
    async def test_backfill_full_history(self, test_db, monkeypatch):
        """Test backfill_full_history function."""
        from unittest.mock import AsyncMock

        monkeypatch.setattr(withings_sync, 'fetch_measurements', AsyncMock(return_value=[]))
        monkeypatch.setattr(withings_sync, 'fetch_activity', AsyncMock(return_value=[]))
        monkeypatch.setattr(withings_sync, 'fetch_sleep', AsyncMock(return_value=[]))

        counts = await withings_sync.backfill_full_history()

        assert "body_measurements" in counts
        assert "sleep" in counts
