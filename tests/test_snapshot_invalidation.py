"""Tests for snapshot cache invalidation."""

from datetime import date

import pytest

from app.database import get_db, init_db
from app.models.food import FoodCreate, FoodUpdate
from app.services import food_service
from app.services.snapshot_service import get_or_create_snapshot, compute_snapshot


@pytest.fixture
async def test_db(tmp_path):
    """Create a temporary test database."""
    db_path = str(tmp_path / "test.db")
    await init_db(db_path)
    yield db_path


def make_food(
    food_date: date,
    name: str = "Test Food",
    marker: str = "lunch",
    calories: int = 100,
    protein_g: float = 10,
    carbs_g: float = 10,
    fats_g: float = 5,
    sodium_mg: int = 50,
) -> FoodCreate:
    """Helper to create FoodCreate with all required fields."""
    return FoodCreate(
        date=food_date,
        marker=marker,
        name=name,
        amount=1.0,
        unit="serving",
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fats_g=fats_g,
        sodium_mg=sodium_mg,
    )


class TestSnapshotInvalidationOnCreate:
    """Test that creating food invalidates cached snapshots."""

    async def test_create_food_invalidates_snapshot(self, test_db):
        """Creating food should invalidate any cached snapshot for that date."""
        test_date = date(2025, 1, 15)

        # First, create a cached snapshot (will be 0 since no food)
        snapshot1 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot1.calories == 0

        # Verify it's cached
        async with get_db(test_db) as db:
            cursor = await db.execute(
                "SELECT * FROM daily_snapshots WHERE date = ?",
                (test_date.isoformat(),)
            )
            cached = await cursor.fetchone()
            assert cached is not None

        # Create a food entry
        food = make_food(test_date, calories=500, protein_g=30, carbs_g=40, fats_g=20, sodium_mg=100)
        await food_service.create_food(food, test_db)

        # Verify the cache was invalidated
        async with get_db(test_db) as db:
            cursor = await db.execute(
                "SELECT * FROM daily_snapshots WHERE date = ?",
                (test_date.isoformat(),)
            )
            cached = await cursor.fetchone()
            assert cached is None, "Snapshot cache should be invalidated after creating food"

        # Get snapshot again - should now show the food
        snapshot2 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot2.calories == 500
        assert snapshot2.protein_g == 30

    async def test_create_food_only_invalidates_its_date(self, test_db):
        """Creating food should only invalidate the snapshot for that specific date."""
        date1 = date(2025, 1, 15)
        date2 = date(2025, 1, 16)

        # Create cached snapshots for both dates
        await get_or_create_snapshot(date1, test_db)
        await get_or_create_snapshot(date2, test_db)

        # Create food for date1 only
        food = make_food(date1, calories=500)
        await food_service.create_food(food, test_db)

        # date1 cache should be invalidated
        async with get_db(test_db) as db:
            cursor = await db.execute(
                "SELECT * FROM daily_snapshots WHERE date = ?",
                (date1.isoformat(),)
            )
            assert await cursor.fetchone() is None

            # date2 cache should still exist
            cursor = await db.execute(
                "SELECT * FROM daily_snapshots WHERE date = ?",
                (date2.isoformat(),)
            )
            assert await cursor.fetchone() is not None


class TestSnapshotInvalidationOnUpdate:
    """Test that updating food invalidates cached snapshots."""

    async def test_update_food_invalidates_snapshot(self, test_db):
        """Updating food should invalidate the cached snapshot."""
        test_date = date(2025, 1, 15)

        # Create food
        food = make_food(test_date, calories=500)
        created = await food_service.create_food(food, test_db)

        # Create cached snapshot
        snapshot1 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot1.calories == 500

        # Update the food
        update = FoodUpdate(calories=800)
        await food_service.update_food(created.id, update, test_db)

        # Cache should be invalidated
        async with get_db(test_db) as db:
            cursor = await db.execute(
                "SELECT * FROM daily_snapshots WHERE date = ?",
                (test_date.isoformat(),)
            )
            assert await cursor.fetchone() is None

        # New snapshot should reflect the update
        snapshot2 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot2.calories == 800


class TestSnapshotInvalidationOnDelete:
    """Test that deleting food invalidates cached snapshots."""

    async def test_delete_food_invalidates_snapshot(self, test_db):
        """Deleting food should invalidate the cached snapshot."""
        test_date = date(2025, 1, 15)

        # Create food
        food = make_food(test_date, calories=500)
        created = await food_service.create_food(food, test_db)

        # Create cached snapshot
        snapshot1 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot1.calories == 500

        # Delete the food
        await food_service.delete_food(created.id, test_db)

        # Cache should be invalidated
        async with get_db(test_db) as db:
            cursor = await db.execute(
                "SELECT * FROM daily_snapshots WHERE date = ?",
                (test_date.isoformat(),)
            )
            assert await cursor.fetchone() is None

        # New snapshot should show 0
        snapshot2 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot2.calories == 0

    async def test_delete_by_marker_invalidates_snapshot(self, test_db):
        """Deleting foods by marker should invalidate the cached snapshot."""
        test_date = date(2025, 1, 15)

        # Create foods with marker
        for i in range(3):
            food = make_food(test_date, name=f"Test Food {i}", marker="lunch", calories=100)
            await food_service.create_food(food, test_db)

        # Create cached snapshot
        snapshot1 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot1.calories == 300

        # Delete by marker
        await food_service.delete_foods_by_marker(test_date, "lunch", test_db)

        # Cache should be invalidated
        async with get_db(test_db) as db:
            cursor = await db.execute(
                "SELECT * FROM daily_snapshots WHERE date = ?",
                (test_date.isoformat(),)
            )
            assert await cursor.fetchone() is None

        # New snapshot should show 0
        snapshot2 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot2.calories == 0

    async def test_clear_foods_by_date_invalidates_snapshot(self, test_db):
        """Clearing all foods for a date should invalidate the cached snapshot."""
        test_date = date(2025, 1, 15)

        # Create multiple foods
        for i in range(3):
            food = make_food(test_date, name=f"Test Food {i}", calories=100)
            await food_service.create_food(food, test_db)

        # Create cached snapshot
        snapshot1 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot1.calories == 300

        # Clear all foods for date
        await food_service.clear_foods_by_date(test_date, test_db)

        # Cache should be invalidated
        async with get_db(test_db) as db:
            cursor = await db.execute(
                "SELECT * FROM daily_snapshots WHERE date = ?",
                (test_date.isoformat(),)
            )
            assert await cursor.fetchone() is None

        # New snapshot should show 0
        snapshot2 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot2.calories == 0


class TestSnapshotInvalidationNoOp:
    """Test that operations that don't change data don't unnecessarily invalidate."""

    async def test_delete_by_marker_no_matches_no_invalidation(self, test_db):
        """Deleting by marker with no matches should not invalidate cache."""
        test_date = date(2025, 1, 15)

        # Create food with different marker
        food = make_food(test_date, marker="breakfast", calories=500)
        await food_service.create_food(food, test_db)

        # Create cached snapshot
        await get_or_create_snapshot(test_date, test_db)

        # Try to delete by non-existent marker
        await food_service.delete_foods_by_marker(test_date, "nonexistent", test_db)

        # Cache should still exist (no actual deletion occurred)
        async with get_db(test_db) as db:
            cursor = await db.execute(
                "SELECT * FROM daily_snapshots WHERE date = ?",
                (test_date.isoformat(),)
            )
            assert await cursor.fetchone() is not None

    async def test_clear_empty_date_no_invalidation(self, test_db):
        """Clearing a date with no foods should not invalidate cache."""
        test_date = date(2025, 1, 15)

        # Create cached snapshot (no food)
        await get_or_create_snapshot(test_date, test_db)

        # Clear (nothing to clear)
        await food_service.clear_foods_by_date(test_date, test_db)

        # Cache should still exist
        async with get_db(test_db) as db:
            cursor = await db.execute(
                "SELECT * FROM daily_snapshots WHERE date = ?",
                (test_date.isoformat(),)
            )
            assert await cursor.fetchone() is not None


class TestSnapshotCorrectness:
    """Test that snapshots are computed correctly after invalidation."""

    async def test_multiple_foods_aggregated_correctly(self, test_db):
        """Multiple foods should be aggregated correctly in snapshot."""
        test_date = date(2025, 1, 15)

        # Create multiple foods
        foods_data = [
            {"calories": 300, "protein_g": 25, "carbs_g": 30, "fats_g": 10, "sodium_mg": 200},
            {"calories": 450, "protein_g": 35, "carbs_g": 20, "fats_g": 25, "sodium_mg": 350},
            {"calories": 250, "protein_g": 20, "carbs_g": 35, "fats_g": 8, "sodium_mg": 150},
        ]

        for i, data in enumerate(foods_data):
            food = make_food(test_date, name=f"Food {i}", **data)
            await food_service.create_food(food, test_db)

        # Get snapshot
        snapshot = await get_or_create_snapshot(test_date, test_db)

        assert snapshot.calories == 1000  # 300 + 450 + 250
        assert snapshot.protein_g == 80  # 25 + 35 + 20
        assert snapshot.carbs_g == 85  # 30 + 20 + 35
        assert snapshot.fats_g == 43  # 10 + 25 + 8
        assert snapshot.sodium_mg == 700  # 200 + 350 + 150

    async def test_snapshot_updates_after_partial_delete(self, test_db):
        """Snapshot should update correctly after deleting some foods."""
        test_date = date(2025, 1, 15)

        # Create foods
        food1 = await food_service.create_food(
            make_food(test_date, name="Food 1", calories=300, protein_g=20, carbs_g=30, fats_g=10, sodium_mg=100),
            test_db
        )
        await food_service.create_food(
            make_food(test_date, name="Food 2", calories=200, protein_g=15, carbs_g=20, fats_g=8, sodium_mg=80),
            test_db
        )

        # Initial snapshot
        snapshot1 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot1.calories == 500

        # Delete one food
        await food_service.delete_food(food1.id, test_db)

        # New snapshot should reflect deletion
        snapshot2 = await get_or_create_snapshot(test_date, test_db)
        assert snapshot2.calories == 200
        assert snapshot2.protein_g == 15
