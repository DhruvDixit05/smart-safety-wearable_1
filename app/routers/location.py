from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.device import Device
from app.models.location import Location
from app.schemas import LocationCreate, LocationResponse
from app.services.auth_service import get_current_device

router = APIRouter(prefix="/api/location", tags=["location"])


@router.post("", response_model=LocationResponse)
async def create_location(
    request: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """Store GPS from the device."""
    if request.device_id != current_device.device_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create location for another device",
        )

    new_location = Location(
        device_id=request.device_id,
        latitude=request.latitude,
        longitude=request.longitude,
        altitude=request.altitude,
        accuracy=request.accuracy,
        speed=request.speed
    )
    db.add(new_location)
    await db.commit()
    await db.refresh(new_location)
    return new_location


@router.get("/latest/{device_id}", response_model=LocationResponse)
async def get_latest_location(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """Get the latest location for a specific device."""
    if device_id != current_device.device_id:
        # In a real app we might allow users to see other devices under same account
        # but for simplicity enforce self viewing or add account logic
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot fetch location for another device",
        )

    result = await db.execute(
        select(Location)
        .where(Location.device_id == device_id)
        .order_by(Location.timestamp.desc())
        .limit(1)
    )
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No locations found for this device"
        )
    return location
