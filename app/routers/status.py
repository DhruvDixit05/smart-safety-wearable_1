from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.device import Device, DeviceStatus
from app.schemas import DeviceStatusCreate, DeviceStatusResponse
from app.services.auth_service import get_current_device

router = APIRouter(prefix="/api/status", tags=["status"])


@router.post("", response_model=DeviceStatusResponse)
async def create_status(
    request: DeviceStatusCreate,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """Device pushes battery/SIM status periodically."""
    if request.device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # Note: DeviceStatus class comes from models.__init__ because the model
    # was actually defined inside app.models.device alongside Device
    
    new_status = DeviceStatus(
        device_id=request.device_id,
        battery_level=request.battery_level,
        sim_status=request.sim_status,
        signal_strength=request.signal_strength,
        firmware_version=request.firmware_version
    )
    db.add(new_status)
    
    # We should also update the parent device object so we have quick access
    # to latest battery level and sim status
    if request.battery_level is not None:
        current_device.battery_level = request.battery_level
    if request.sim_status is not None:
        current_device.sim_status = request.sim_status
        
    await db.commit()
    await db.refresh(new_status)
    return new_status


@router.get("/{device_id}", response_model=DeviceStatusResponse)
async def get_latest_status(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """Get latest status snapshot for the device."""
    if device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await db.execute(
        select(DeviceStatus)
        .where(DeviceStatus.device_id == device_id)
        .order_by(DeviceStatus.timestamp.desc())
        .limit(1)
    )
    stat = result.scalar_one_or_none()
    
    if not stat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No status recorded for this device"
        )
    return stat
