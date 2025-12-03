from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import verify_token
from app.models.food import FoodCreate, FoodResponse, FoodFromRecipe, FoodUpdate
from app.services import food_service

router = APIRouter()


@router.post("", response_model=FoodResponse, status_code=201)
async def create_food(
    data: FoodCreate,
    _: str = Depends(verify_token),
) -> FoodResponse:
    """Log a food entry directly."""
    return await food_service.create_food(data)


@router.post("/from-recipe", response_model=list[FoodResponse], status_code=201)
async def create_foods_from_recipe(
    data: FoodFromRecipe,
    _: str = Depends(verify_token),
) -> list[FoodResponse]:
    """Log foods from a recipe (expands to individual entries)."""
    return await food_service.create_foods_from_recipe(data)


@router.get("", response_model=list[FoodResponse])
async def get_foods(
    date: date = Query(..., description="Date to get foods for (YYYY-MM-DD)"),
    marker: Optional[str] = Query(None, description="Optional marker to filter by"),
    _: str = Depends(verify_token),
) -> list[FoodResponse]:
    """Get food entries for a date, optionally filtered by marker."""
    return await food_service.get_foods(date, marker)


# Note: These routes must come BEFORE /{food_id} to avoid being matched as an ID
@router.delete("/by-marker", status_code=200)
async def delete_foods_by_marker(
    date: date = Query(..., description="Date (YYYY-MM-DD)"),
    marker: str = Query(..., description="Marker to delete"),
    _: str = Depends(verify_token),
) -> dict:
    """Delete all food entries with a specific marker on a date."""
    count = await food_service.delete_foods_by_marker(date, marker)
    return {"deleted": count}


@router.delete("/clear", status_code=200)
async def clear_foods(
    date: date = Query(..., description="Date to clear (YYYY-MM-DD)"),
    _: str = Depends(verify_token),
) -> dict:
    """Clear all food entries for a date."""
    count = await food_service.clear_foods_by_date(date)
    return {"deleted": count}


@router.get("/{food_id}", response_model=FoodResponse)
async def get_food(
    food_id: int,
    _: str = Depends(verify_token),
) -> FoodResponse:
    """Get a food entry by ID."""
    return await food_service.get_food(food_id)


@router.put("/{food_id}", response_model=FoodResponse)
async def update_food(
    food_id: int,
    data: FoodUpdate,
    _: str = Depends(verify_token),
) -> FoodResponse:
    """Update a food entry."""
    return await food_service.update_food(food_id, data)


@router.delete("/{food_id}", status_code=204)
async def delete_food(
    food_id: int,
    _: str = Depends(verify_token),
) -> None:
    """Delete a food entry."""
    await food_service.delete_food(food_id)
