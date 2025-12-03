from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import verify_token
from app.models.supplement import (
    SupplementCreate,
    SupplementResponse,
    SupplementUpdate,
    SupplementScheduleResponse,
    SupplementHistoryResponse,
    SupplementListResponse,
    TimeOfDay,
)
from app.services import supplement_service

router = APIRouter()


@router.post("", response_model=SupplementResponse, status_code=201)
async def create_supplement(
    data: SupplementCreate,
    _: str = Depends(verify_token),
) -> SupplementResponse:
    """Create a new supplement entry."""
    return await supplement_service.create_supplement(data)


@router.get("", response_model=SupplementListResponse)
async def list_supplements(
    active: Optional[bool] = Query(None, description="Filter by active status"),
    time_of_day: Optional[TimeOfDay] = Query(None, description="Filter by time of day"),
    _: str = Depends(verify_token),
) -> SupplementListResponse:
    """List all supplements with optional filters."""
    return await supplement_service.list_supplements(active=active, time_of_day=time_of_day)


# Note: These routes must come BEFORE /{supplement_id} to avoid being matched as an ID
@router.get("/active", response_model=SupplementListResponse)
async def get_active_supplements(
    _: str = Depends(verify_token),
) -> SupplementListResponse:
    """Get all currently active supplements."""
    return await supplement_service.get_active_supplements()


@router.get("/schedule", response_model=SupplementScheduleResponse)
async def get_supplement_schedule(
    _: str = Depends(verify_token),
) -> SupplementScheduleResponse:
    """Get today's supplement schedule organized by time of day."""
    return await supplement_service.get_supplement_schedule()


@router.get("/history", response_model=SupplementHistoryResponse)
async def get_supplement_history(
    start_date: date = Query(..., description="Range start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Range end date (YYYY-MM-DD)"),
    _: str = Depends(verify_token),
) -> SupplementHistoryResponse:
    """Get supplements that were active during a date range."""
    return await supplement_service.get_supplement_history(start_date, end_date)


@router.get("/{supplement_id}", response_model=SupplementResponse)
async def get_supplement(
    supplement_id: int,
    _: str = Depends(verify_token),
) -> SupplementResponse:
    """Get a supplement by ID."""
    return await supplement_service.get_supplement(supplement_id)


@router.put("/{supplement_id}", response_model=SupplementResponse)
async def update_supplement(
    supplement_id: int,
    data: SupplementUpdate,
    _: str = Depends(verify_token),
) -> SupplementResponse:
    """Update a supplement."""
    return await supplement_service.update_supplement(supplement_id, data)


@router.delete("/{supplement_id}", status_code=204)
async def delete_supplement(
    supplement_id: int,
    _: str = Depends(verify_token),
) -> None:
    """Delete a supplement."""
    await supplement_service.delete_supplement(supplement_id)
