from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.models import Supplement
from app.schemas import SupplementCreate, SupplementUpdate, SupplementResponse

router = APIRouter(prefix="/supplements", tags=["Supplements"])


@router.post("", response_model=SupplementResponse, status_code=status.HTTP_201_CREATED)
async def create_supplement(
    data: SupplementCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Add a new supplement."""
    supplement = Supplement(**data.model_dump())
    db.add(supplement)
    await db.flush()
    await db.refresh(supplement)
    return supplement


@router.get("", response_model=List[SupplementResponse])
async def list_active_supplements(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List active supplements."""
    result = await db.execute(
        select(Supplement)
        .where(Supplement.is_active == True)
        .order_by(Supplement.time_of_day, Supplement.name)
    )
    return result.scalars().all()


@router.get("/all", response_model=List[SupplementResponse], include_in_schema=False)
async def list_all_supplements(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """List all supplements (including inactive)."""
    result = await db.execute(
        select(Supplement).order_by(Supplement.is_active.desc(), Supplement.name)
    )
    return result.scalars().all()


@router.get("/{supplement_id}", response_model=SupplementResponse)
async def get_supplement(
    supplement_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get a specific supplement."""
    result = await db.execute(
        select(Supplement).where(Supplement.id == supplement_id)
    )
    supplement = result.scalar_one_or_none()
    if not supplement:
        raise HTTPException(status_code=404, detail="Supplement not found")
    return supplement


@router.patch("/{supplement_id}", response_model=SupplementResponse)
async def update_supplement(
    supplement_id: int,
    data: SupplementUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Update a supplement."""
    result = await db.execute(
        select(Supplement).where(Supplement.id == supplement_id)
    )
    supplement = result.scalar_one_or_none()
    if not supplement:
        raise HTTPException(status_code=404, detail="Supplement not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(supplement, key, value)

    await db.flush()
    await db.refresh(supplement)
    return supplement


@router.delete("/{supplement_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def deactivate_supplement(
    supplement_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Deactivate a supplement (soft delete)."""
    result = await db.execute(
        select(Supplement).where(Supplement.id == supplement_id)
    )
    supplement = result.scalar_one_or_none()
    if not supplement:
        raise HTTPException(status_code=404, detail="Supplement not found")

    supplement.is_active = False
    await db.flush()
