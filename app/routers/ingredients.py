from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.models import Ingredient
from app.schemas import IngredientCreate, IngredientUpdate, IngredientResponse

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])


@router.post("", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
async def create_ingredient(
    data: IngredientCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Add a new ingredient with nutrition facts."""
    ingredient = Ingredient(**data.model_dump())
    db.add(ingredient)
    await db.flush()
    await db.refresh(ingredient)
    return ingredient


@router.get("", response_model=List[IngredientResponse])
async def list_ingredients(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List all ingredients."""
    result = await db.execute(select(Ingredient).order_by(Ingredient.name))
    return result.scalars().all()


@router.get("/search", response_model=List[IngredientResponse])
async def search_ingredients(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Search ingredients by name."""
    result = await db.execute(
        select(Ingredient)
        .where(Ingredient.name.ilike(f"%{q}%"))
        .order_by(Ingredient.is_default.desc(), Ingredient.name)
    )
    return result.scalars().all()


@router.get("/{ingredient_id}", response_model=IngredientResponse)
async def get_ingredient(
    ingredient_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get a specific ingredient."""
    result = await db.execute(
        select(Ingredient).where(Ingredient.id == ingredient_id)
    )
    ingredient = result.scalar_one_or_none()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ingredient


@router.patch("/{ingredient_id}", response_model=IngredientResponse)
async def update_ingredient(
    ingredient_id: int,
    data: IngredientUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update an ingredient."""
    result = await db.execute(
        select(Ingredient).where(Ingredient.id == ingredient_id)
    )
    ingredient = result.scalar_one_or_none()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ingredient, key, value)

    await db.flush()
    await db.refresh(ingredient)
    return ingredient


@router.post("/{ingredient_id}/set-default", response_model=IngredientResponse)
async def set_default_ingredient(
    ingredient_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Set an ingredient as the default for its generic name."""
    result = await db.execute(
        select(Ingredient).where(Ingredient.id == ingredient_id)
    )
    ingredient = result.scalar_one_or_none()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    # Clear default status from other ingredients with similar names
    similar = await db.execute(
        select(Ingredient).where(
            Ingredient.name.ilike(f"%{ingredient.name.split()[0]}%"),
            Ingredient.id != ingredient_id,
        )
    )
    for other in similar.scalars().all():
        other.is_default = False

    ingredient.is_default = True
    await db.flush()
    await db.refresh(ingredient)
    return ingredient
