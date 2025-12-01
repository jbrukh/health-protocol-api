from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.models import NutritionLabel, Ingredient
from app.schemas import NutritionLabelCreate, NutritionLabelUpdate, NutritionLabelResponse, IngredientResponse

router = APIRouter(prefix="/nutrition-labels", tags=["Nutrition Labels"])


@router.post("", response_model=NutritionLabelResponse, status_code=status.HTTP_201_CREATED)
async def create_nutrition_label(
    data: NutritionLabelCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Create a nutrition label from packaged food."""
    # Check for duplicate barcode
    if data.barcode:
        result = await db.execute(
            select(NutritionLabel).where(NutritionLabel.barcode == data.barcode)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Barcode already exists")

    label = NutritionLabel(**data.model_dump())
    db.add(label)
    await db.flush()
    await db.refresh(label)
    return label


@router.get("", response_model=List[NutritionLabelResponse])
async def list_nutrition_labels(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List all nutrition labels."""
    result = await db.execute(
        select(NutritionLabel).order_by(NutritionLabel.product_name)
    )
    return result.scalars().all()


@router.get("/search", response_model=List[NutritionLabelResponse])
async def search_nutrition_labels(
    q: Optional[str] = Query(None, min_length=1, description="Search by product name or brand"),
    barcode: Optional[str] = Query(None, description="Search by barcode"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Search nutrition labels by name, brand, or barcode."""
    if barcode:
        result = await db.execute(
            select(NutritionLabel).where(NutritionLabel.barcode == barcode)
        )
    elif q:
        result = await db.execute(
            select(NutritionLabel)
            .where(
                NutritionLabel.product_name.ilike(f"%{q}%")
                | NutritionLabel.brand.ilike(f"%{q}%")
            )
            .order_by(NutritionLabel.product_name)
        )
    else:
        raise HTTPException(status_code=400, detail="Provide either q or barcode parameter")

    return result.scalars().all()


@router.get("/{label_id}", response_model=NutritionLabelResponse)
async def get_nutrition_label(
    label_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get a specific nutrition label."""
    result = await db.execute(
        select(NutritionLabel).where(NutritionLabel.id == label_id)
    )
    label = result.scalar_one_or_none()
    if not label:
        raise HTTPException(status_code=404, detail="Nutrition label not found")
    return label


@router.patch("/{label_id}", response_model=NutritionLabelResponse, include_in_schema=False)
async def update_nutrition_label(
    label_id: int,
    data: NutritionLabelUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update a nutrition label."""
    result = await db.execute(
        select(NutritionLabel).where(NutritionLabel.id == label_id)
    )
    label = result.scalar_one_or_none()
    if not label:
        raise HTTPException(status_code=404, detail="Nutrition label not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(label, key, value)

    await db.flush()
    await db.refresh(label)
    return label


@router.post("/{label_id}/to-ingredient", response_model=IngredientResponse)
async def convert_to_ingredient(
    label_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Convert a nutrition label to an ingredient for food logging."""
    result = await db.execute(
        select(NutritionLabel).where(NutritionLabel.id == label_id)
    )
    label = result.scalar_one_or_none()
    if not label:
        raise HTTPException(status_code=404, detail="Nutrition label not found")

    # Create ingredient from label
    name = f"{label.brand} {label.product_name}" if label.brand else label.product_name
    ingredient = Ingredient(
        name=name,
        serving_size=label.serving_size,
        serving_unit=label.serving_unit,
        protein_g=label.protein_g,
        carbs_g=label.carbs_g,
        fat_g=label.fat_g,
        sodium_mg=label.sodium_mg,
        calories=label.calories,
        is_default=False,
    )
    db.add(ingredient)
    await db.flush()
    await db.refresh(ingredient)
    return ingredient
