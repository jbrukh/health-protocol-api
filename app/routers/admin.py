from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db

router = APIRouter(prefix="/admin", tags=["Admin"])

ALLOWED_TABLES = [
    "food_entries",
    "daily_logs",
    "ingredients",
    "recipes",
    "recipe_ingredients",
    "targets",
    "nutrition_labels",
]


@router.post("/clear", include_in_schema=False)
async def clear_data(
    table: Optional[str] = Query(None, description="Table to clear (omit to clear all)"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Clear data from a specific table or all tables."""
    if table:
        if table not in ALLOWED_TABLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid table. Allowed: {ALLOWED_TABLES}"
            )
        await db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        await db.commit()
        return {"message": f"Cleared table: {table}"}
    else:
        # Clear all tables in correct order (respecting foreign keys)
        clear_order = [
            "food_entries",
            "recipe_ingredients",
            "daily_logs",
            "recipes",
            "ingredients",
            "nutrition_labels",
            "targets",
        ]
        for tbl in clear_order:
            await db.execute(text(f"TRUNCATE TABLE {tbl} CASCADE"))
        await db.commit()
        return {"message": "Cleared all tables", "tables": clear_order}
