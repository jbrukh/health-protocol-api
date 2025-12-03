from fastapi import APIRouter, Depends, Query

from app.auth import verify_token
from app.models.macro import MacroTodayResponse, MacroRemainingResponse, MacroHistoryResponse
from app.services import macro_service

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
    days: int = Query(7, description="Number of days to look back"),
    _: str = Depends(verify_token),
) -> MacroHistoryResponse:
    """Get macro and body measurement history for the last N days."""
    return await macro_service.get_macro_history(days)
