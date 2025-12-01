from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.models import Biomarker
from app.schemas import BiomarkerCreate, BiomarkerResponse, BiomarkerComparison

router = APIRouter(prefix="/biomarkers", tags=["Biomarkers"])


@router.post("", response_model=BiomarkerResponse, status_code=status.HTTP_201_CREATED)
async def create_biomarker(
    data: BiomarkerCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Record a biomarker reading."""
    biomarker = Biomarker(**data.model_dump())
    db.add(biomarker)
    await db.flush()
    await db.refresh(biomarker)
    return biomarker


@router.get("", response_model=List[BiomarkerResponse])
async def get_biomarker_history(
    name: str = Query(..., description="Biomarker name"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get history for a specific biomarker."""
    result = await db.execute(
        select(Biomarker)
        .where(Biomarker.name.ilike(name))
        .order_by(Biomarker.measured_at.desc())
    )
    return result.scalars().all()


@router.get("/latest", response_model=List[BiomarkerResponse])
async def get_latest_biomarkers(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Get the most recent reading for all biomarkers."""
    # Subquery to get the max measured_at for each biomarker name
    subquery = (
        select(Biomarker.name, func.max(Biomarker.measured_at).label("max_date"))
        .group_by(Biomarker.name)
        .subquery()
    )

    result = await db.execute(
        select(Biomarker)
        .join(
            subquery,
            (Biomarker.name == subquery.c.name)
            & (Biomarker.measured_at == subquery.c.max_date),
        )
        .order_by(Biomarker.name)
    )
    return result.scalars().all()


@router.get("/compare", response_model=BiomarkerComparison)
async def compare_biomarker(
    name: str = Query(..., description="Biomarker name"),
    start: datetime = Query(..., description="Start datetime"),
    end: datetime = Query(..., description="End datetime"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Compare a biomarker over time."""
    result = await db.execute(
        select(Biomarker)
        .where(
            Biomarker.name.ilike(name),
            Biomarker.measured_at >= start,
            Biomarker.measured_at <= end,
        )
        .order_by(Biomarker.measured_at)
    )
    readings = result.scalars().all()

    if not readings:
        raise HTTPException(status_code=404, detail="No readings found for this biomarker in the specified range")

    values = [r.value for r in readings]
    first_value = readings[0].value
    last_value = readings[-1].value
    change = last_value - first_value
    change_percent = (change / first_value * 100) if first_value != 0 else None

    return BiomarkerComparison(
        name=name,
        unit=readings[0].unit,
        readings=readings,
        min_value=min(values),
        max_value=max(values),
        change=round(change, 2),
        change_percent=round(change_percent, 2) if change_percent is not None else None,
    )
