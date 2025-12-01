from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.models import Target
from app.schemas import TargetCreate, TargetResponse

router = APIRouter(prefix="/targets", tags=["Targets"])


@router.post("", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    data: TargetCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Set a new target (creates a new record, preserving history)."""
    target = Target(**data.model_dump())
    db.add(target)
    await db.flush()
    await db.refresh(target)
    return target


@router.get("", response_model=List[TargetResponse])
async def get_current_targets(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get current targets (most recent for each name)."""
    today = date.today()

    # Subquery to get the max effective_from for each target name (not in future)
    subquery = (
        select(Target.name, func.max(Target.effective_from).label("max_date"))
        .where(Target.effective_from <= today)
        .group_by(Target.name)
        .subquery()
    )

    result = await db.execute(
        select(Target)
        .join(
            subquery,
            (Target.name == subquery.c.name)
            & (Target.effective_from == subquery.c.max_date),
        )
        .order_by(Target.name)
    )
    return result.scalars().all()


@router.get("/{name}/history", response_model=List[TargetResponse])
async def get_target_history(
    name: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get target change history for a specific target name."""
    result = await db.execute(
        select(Target)
        .where(Target.name.ilike(name))
        .order_by(Target.effective_from.desc())
    )
    targets = result.scalars().all()
    if not targets:
        raise HTTPException(status_code=404, detail="Target not found")
    return targets
