from fastapi import APIRouter, Depends

from app.auth import verify_token
from app.models.profile import ProfileResponse, ProfileUpdate
from app.services import profile_service

router = APIRouter()


@router.get("", response_model=ProfileResponse)
async def get_profile(_: str = Depends(verify_token)) -> ProfileResponse:
    """Get user profile with computed age."""
    return await profile_service.get_profile()


@router.put("", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    _: str = Depends(verify_token),
) -> ProfileResponse:
    """Update user profile."""
    return await profile_service.update_profile(data)
