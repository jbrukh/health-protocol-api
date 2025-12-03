from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import verify_token
from app.models.body import BodyMeasurementCreate, BodyMeasurementResponse, BodyMeasurementUpdate
from app.services import body_service

router = APIRouter()


@router.post("", response_model=BodyMeasurementResponse, status_code=201)
async def create_measurement(
    data: BodyMeasurementCreate,
    _: str = Depends(verify_token),
) -> BodyMeasurementResponse:
    """Log a body measurement."""
    return await body_service.create_measurement(data)


@router.get("", response_model=list[BodyMeasurementResponse])
async def get_measurements(
    date: date = Query(..., description="Date to get measurements for (YYYY-MM-DD)"),
    _: str = Depends(verify_token),
) -> list[BodyMeasurementResponse]:
    """Get body measurements for a date."""
    return await body_service.get_measurements(date)


@router.get("/latest", response_model=Optional[BodyMeasurementResponse])
async def get_latest_measurement(
    _: str = Depends(verify_token),
) -> Optional[BodyMeasurementResponse]:
    """Get the most recent body measurement."""
    return await body_service.get_latest_measurement()


@router.get("/{measurement_id}", response_model=BodyMeasurementResponse)
async def get_measurement(
    measurement_id: int,
    _: str = Depends(verify_token),
) -> BodyMeasurementResponse:
    """Get a body measurement by ID."""
    return await body_service.get_measurement(measurement_id)


@router.put("/{measurement_id}", response_model=BodyMeasurementResponse)
async def update_measurement(
    measurement_id: int,
    data: BodyMeasurementUpdate,
    _: str = Depends(verify_token),
) -> BodyMeasurementResponse:
    """Update a body measurement."""
    return await body_service.update_measurement(measurement_id, data)


@router.delete("/{measurement_id}", status_code=204)
async def delete_measurement(
    measurement_id: int,
    _: str = Depends(verify_token),
) -> None:
    """Delete a body measurement."""
    await body_service.delete_measurement(measurement_id)
