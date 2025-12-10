from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import verify_token
from app.models.phase import (
    PhaseCreate,
    PhaseResponse,
    PhaseUpdate,
    PhaseListResponse,
    ActivePhasesResponse,
)
from app.services import phase_service
from app.services.profile_service import get_profile

router = APIRouter()


@router.post("", response_model=PhaseResponse, status_code=201)
async def create_phase(
    data: PhaseCreate,
    _: str = Depends(verify_token),
) -> PhaseResponse:
    """Create a new phase."""
    return await phase_service.create_phase(data)


@router.get("", response_model=PhaseListResponse)
async def list_phases(
    active: Optional[bool] = Query(None, description="Filter by active status"),
    include_past: bool = Query(True, description="Include past phases"),
    _: str = Depends(verify_token),
) -> PhaseListResponse:
    """List all phases with optional filters."""
    profile = await get_profile()
    return await phase_service.list_phases(active=active, include_past=include_past, timezone=profile.timezone)


@router.get("/active", response_model=ActivePhasesResponse)
async def get_active_phases(
    _: str = Depends(verify_token),
) -> ActivePhasesResponse:
    """Get all currently active phases and upcoming phases (next 7 days)."""
    profile = await get_profile()
    return await phase_service.get_active_phases(timezone=profile.timezone)


@router.get("/{phase_id}", response_model=PhaseResponse)
async def get_phase(
    phase_id: int,
    _: str = Depends(verify_token),
) -> PhaseResponse:
    """Get a phase by ID."""
    return await phase_service.get_phase(phase_id)


@router.put("/{phase_id}", response_model=PhaseResponse)
async def update_phase(
    phase_id: int,
    data: PhaseUpdate,
    _: str = Depends(verify_token),
) -> PhaseResponse:
    """Update a phase."""
    return await phase_service.update_phase(phase_id, data)


@router.delete("/{phase_id}", status_code=204)
async def delete_phase(
    phase_id: int,
    _: str = Depends(verify_token),
) -> None:
    """Delete a phase."""
    await phase_service.delete_phase(phase_id)
