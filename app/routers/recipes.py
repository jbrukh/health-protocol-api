from fastapi import APIRouter, Depends

from app.auth import verify_token
from app.models.recipe import (
    RecipeCreate,
    RecipeResponse,
    RecipeListResponse,
    RecipeUpdate,
    RecipeItemCreate,
    RecipeItemUpdate,
)
from app.services import recipe_service

router = APIRouter()


@router.post("", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    data: RecipeCreate,
    _: str = Depends(verify_token),
) -> RecipeResponse:
    """Create a new recipe with items."""
    return await recipe_service.create_recipe(data)


@router.get("", response_model=list[RecipeListResponse])
async def list_recipes(_: str = Depends(verify_token)) -> list[RecipeListResponse]:
    """List all recipes with computed totals."""
    return await recipe_service.list_recipes()


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    _: str = Depends(verify_token),
) -> RecipeResponse:
    """Get a recipe by ID with items and totals."""
    return await recipe_service.get_recipe(recipe_id)


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    data: RecipeUpdate,
    _: str = Depends(verify_token),
) -> RecipeResponse:
    """Update a recipe's name."""
    return await recipe_service.update_recipe(recipe_id, data)


@router.post("/{recipe_id}/items", response_model=RecipeResponse)
async def add_recipe_item(
    recipe_id: int,
    data: RecipeItemCreate,
    _: str = Depends(verify_token),
) -> RecipeResponse:
    """Add an item to a recipe."""
    return await recipe_service.add_recipe_item(recipe_id, data)


@router.put("/{recipe_id}/items/{item_id}", response_model=RecipeResponse)
async def update_recipe_item(
    recipe_id: int,
    item_id: int,
    data: RecipeItemUpdate,
    _: str = Depends(verify_token),
) -> RecipeResponse:
    """Update an item in a recipe."""
    return await recipe_service.update_recipe_item(recipe_id, item_id, data)


@router.delete("/{recipe_id}/items/{item_id}", response_model=RecipeResponse)
async def delete_recipe_item(
    recipe_id: int,
    item_id: int,
    _: str = Depends(verify_token),
) -> RecipeResponse:
    """Remove an item from a recipe."""
    return await recipe_service.delete_recipe_item(recipe_id, item_id)


@router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(
    recipe_id: int,
    _: str = Depends(verify_token),
) -> None:
    """Delete a recipe."""
    await recipe_service.delete_recipe(recipe_id)
