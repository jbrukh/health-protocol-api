from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import verify_token
from app.models.macro import MacroTodayResponse, MacroRemainingResponse, MacroHistoryResponse
from app.services import macro_service
from app.services.profile_service import get_profile

router = APIRouter()


@router.get("/today", response_model=MacroTodayResponse)
async def get_today_macros(
    _: str = Depends(verify_token),
) -> MacroTodayResponse:
    """Get today's macro totals with target percentages."""
    return await macro_service.get_today_macros()


@router.get("/remaining", response_model=MacroRemainingResponse)
async def get_remaining_macros(
    _: str = Depends(verify_token),
) -> MacroRemainingResponse:
    """Get remaining macro budget for today."""
    return await macro_service.get_remaining_macros()


@router.get("/history", response_model=MacroHistoryResponse)
async def get_macro_history(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD), defaults to 30 days ago"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD), defaults to today"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of days to return"),
    offset: int = Query(0, ge=0, description="Number of days to skip"),
    _: str = Depends(verify_token),
) -> MacroHistoryResponse:
    """Get macro and body measurement history for a date range with pagination."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    profile = await get_profile()
    return await macro_service.get_macro_history(start_date, end_date, limit, offset, timezone=profile.timezone)
