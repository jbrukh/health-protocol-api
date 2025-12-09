from fastapi import APIRouter, Depends

from app.auth import verify_token
from app.database import get_db

router = APIRouter()


@router.delete("/clear-foods", status_code=200)
async def clear_foods(_: str = Depends(verify_token)) -> dict:
    """Clear all food entries and their cached snapshots."""
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM foods")
        foods_deleted = cursor.rowcount
        # Also clear snapshots since they're now invalid
        await db.execute("DELETE FROM daily_snapshots")
        await db.commit()
        return {"deleted": foods_deleted}


@router.delete("/clear-exercises", status_code=200)
async def clear_exercises(_: str = Depends(verify_token)) -> dict:
    """Clear all exercise entries."""
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM exercises")
        await db.commit()
        return {"deleted": cursor.rowcount}


@router.delete("/clear-snapshots", status_code=200)
async def clear_snapshots(_: str = Depends(verify_token)) -> dict:
    """Clear all daily snapshots."""
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM daily_snapshots")
        await db.commit()
        return {"deleted": cursor.rowcount}


@router.delete("/clear-body", status_code=200)
async def clear_body(_: str = Depends(verify_token)) -> dict:
    """Clear all body measurements."""
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM body_measurements")
        await db.commit()
        return {"deleted": cursor.rowcount}


@router.delete("/clear-supplements", status_code=200)
async def clear_supplements(_: str = Depends(verify_token)) -> dict:
    """Clear all supplements."""
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM supplements")
        await db.commit()
        return {"deleted": cursor.rowcount}


@router.delete("/clear-phases", status_code=200)
async def clear_phases(_: str = Depends(verify_token)) -> dict:
    """Clear all phases."""
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM phases")
        await db.commit()
        return {"deleted": cursor.rowcount}


@router.delete("/clear-blood-pressure", status_code=200)
async def clear_blood_pressure(_: str = Depends(verify_token)) -> dict:
    """Clear all blood pressure readings."""
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM blood_pressure")
        await db.commit()
        return {"deleted": cursor.rowcount}


@router.delete("/clear-activity", status_code=200)
async def clear_activity(_: str = Depends(verify_token)) -> dict:
    """Clear all daily activity records."""
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM daily_activity")
        await db.commit()
        return {"deleted": cursor.rowcount}


@router.delete("/clear-sleep", status_code=200)
async def clear_sleep(_: str = Depends(verify_token)) -> dict:
    """Clear all sleep records."""
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM sleep")
        await db.commit()
        return {"deleted": cursor.rowcount}


ALLOWED_TABLES = frozenset([
    "foods", "exercises", "daily_snapshots", "body_measurements",
    "recipe_items", "recipes", "ingredients", "supplements", "phases",
    "blood_pressure", "daily_activity", "sleep"
])


@router.delete("/clear-all", status_code=200)
async def clear_all(_: str = Depends(verify_token)) -> dict:
    """Clear everything except profile and Withings tokens."""
    async with get_db() as db:
        total = 0
        for table in ALLOWED_TABLES:
            # Table name is from whitelist, safe to use in query
            cursor = await db.execute(f"DELETE FROM {table}")  # nosec B608
            total += cursor.rowcount
        await db.commit()
        return {"deleted": total}
