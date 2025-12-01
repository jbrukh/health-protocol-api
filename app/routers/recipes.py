from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import verify_api_key
from app.database import get_db
from app.models import Recipe, RecipeIngredient, Ingredient, DailyLog, FoodEntry
from app.schemas import RecipeCreate, RecipeUpdate, RecipeResponse, FoodEntryResponse
from app.services.nutrition import calculate_recipe_nutrition, calculate_entry_nutrition

router = APIRouter(prefix="/recipes", tags=["Recipes"])


def recipe_to_response(recipe: Recipe) -> RecipeResponse:
    """Convert a recipe model to response with computed nutrition."""
    totals = calculate_recipe_nutrition(recipe.ingredients)
    return RecipeResponse(
        id=recipe.id,
        name=recipe.name,
        description=recipe.description,
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
        ingredients=recipe.ingredients,
        total_protein_g=totals["protein_g"],
        total_carbs_g=totals["carbs_g"],
        total_fat_g=totals["fat_g"],
        total_sodium_mg=totals["sodium_mg"],
        total_calories=totals["calories"],
    )


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    data: RecipeCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Create a new recipe."""
    # Verify all ingredients exist
    ingredient_ids = [i.ingredient_id for i in data.ingredients]
    result = await db.execute(
        select(Ingredient).where(Ingredient.id.in_(ingredient_ids))
    )
    found_ingredients = {i.id: i for i in result.scalars().all()}

    missing = set(ingredient_ids) - set(found_ingredients.keys())
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Ingredients not found: {list(missing)}",
        )

    recipe = Recipe(name=data.name, description=data.description)
    db.add(recipe)
    await db.flush()

    for ing_data in data.ingredients:
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ing_data.ingredient_id,
            quantity=ing_data.quantity,
            unit=ing_data.unit,
        )
        db.add(recipe_ingredient)

    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
        .where(Recipe.id == recipe.id)
    )
    recipe = result.scalar_one()
    return recipe_to_response(recipe)


@router.get("", response_model=List[RecipeResponse])
async def list_recipes(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List all recipes."""
    result = await db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
        .order_by(Recipe.name)
    )
    recipes = result.scalars().all()
    return [recipe_to_response(r) for r in recipes]


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get a recipe with computed macros."""
    result = await db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
        .where(Recipe.id == recipe_id)
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe_to_response(recipe)


@router.patch("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    data: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update a recipe."""
    result = await db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients))
        .where(Recipe.id == recipe_id)
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if data.name is not None:
        recipe.name = data.name
    if data.description is not None:
        recipe.description = data.description

    if data.ingredients is not None:
        # Verify all ingredients exist
        ingredient_ids = [i.ingredient_id for i in data.ingredients]
        result = await db.execute(
            select(Ingredient).where(Ingredient.id.in_(ingredient_ids))
        )
        found_ingredients = {i.id: i for i in result.scalars().all()}

        missing = set(ingredient_ids) - set(found_ingredients.keys())
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Ingredients not found: {list(missing)}",
            )

        # Delete existing ingredients
        for ri in recipe.ingredients:
            await db.delete(ri)

        # Add new ingredients
        for ing_data in data.ingredients:
            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ing_data.ingredient_id,
                quantity=ing_data.quantity,
                unit=ing_data.unit,
            )
            db.add(recipe_ingredient)

    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
        .where(Recipe.id == recipe.id)
    )
    recipe = result.scalar_one()
    return recipe_to_response(recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def delete_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Delete a recipe."""
    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id)
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    await db.delete(recipe)


@router.post("/{recipe_id}/log", response_model=List[FoodEntryResponse])
async def log_recipe(
    recipe_id: int,
    log_date: date = Query(..., alias="date", description="Date to log recipe (YYYY-MM-DD)"),
    meal_label: Optional[str] = Query(None, description="Meal label (breakfast, lunch, etc.)"),
    servings: float = Query(1.0, description="Number of servings"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Log a recipe as food entries."""
    result = await db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient))
        .where(Recipe.id == recipe_id)
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Get or create daily log
    result = await db.execute(
        select(DailyLog).where(DailyLog.date == log_date)
    )
    daily_log = result.scalar_one_or_none()
    if not daily_log:
        daily_log = DailyLog(date=log_date)
        db.add(daily_log)
        await db.flush()

    entries = []
    for ri in recipe.ingredients:
        adjusted_quantity = ri.quantity * servings
        nutrition = calculate_entry_nutrition(ri.ingredient, adjusted_quantity, ri.unit)

        entry = FoodEntry(
            daily_log_id=daily_log.id,
            ingredient_id=ri.ingredient_id,
            quantity=adjusted_quantity,
            unit=ri.unit,
            meal_label=meal_label,
            description=f"From recipe: {recipe.name}",
            **nutrition,
        )
        db.add(entry)
        entries.append(entry)

    await db.flush()

    # Reload with ingredients
    entry_ids = [e.id for e in entries]
    result = await db.execute(
        select(FoodEntry)
        .options(selectinload(FoodEntry.ingredient))
        .where(FoodEntry.id.in_(entry_ids))
    )
    return result.scalars().all()
