from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.auth import verify_token
from app.models.ingredient import IngredientCreate, IngredientResponse, IngredientUpdate
from app.services import ingredient_service

router = APIRouter()


@router.post("", response_model=IngredientResponse, status_code=201)
async def create_ingredient(
    data: IngredientCreate,
    _: str = Depends(verify_token),
) -> IngredientResponse:
    """Create a new ingredient."""
    return await ingredient_service.create_ingredient(data)


@router.get("", response_model=list[IngredientResponse])
async def list_ingredients(_: str = Depends(verify_token)) -> list[IngredientResponse]:
    """List all ingredients."""
    return await ingredient_service.list_ingredients()


@router.get("/search", response_model=list[IngredientResponse])
async def search_ingredients(
    q: str = Query(..., description="Search query"),
    _: str = Depends(verify_token),
) -> list[IngredientResponse]:
    """Search ingredients by name."""
    return await ingredient_service.search_ingredients(q)


@router.get("/{ingredient_id}", response_model=IngredientResponse)
async def get_ingredient(
    ingredient_id: int,
    _: str = Depends(verify_token),
) -> IngredientResponse:
    """Get an ingredient by ID."""
    return await ingredient_service.get_ingredient(ingredient_id)


@router.put("/{ingredient_id}", response_model=IngredientResponse)
async def update_ingredient(
    ingredient_id: int,
    data: IngredientUpdate,
    _: str = Depends(verify_token),
) -> IngredientResponse:
    """Update an ingredient."""
    return await ingredient_service.update_ingredient(ingredient_id, data)


@router.delete("/{ingredient_id}", status_code=204)
async def delete_ingredient(
    ingredient_id: int,
    _: str = Depends(verify_token),
) -> None:
    """Delete an ingredient."""
    await ingredient_service.delete_ingredient(ingredient_id)
