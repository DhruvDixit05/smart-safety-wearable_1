from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.device import Device
from app.schemas import DeviceRegisterRequest, DeviceLoginRequest, TokenResponse
from app.services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
async def register(request: DeviceRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new device and return a JWT access token."""
    result = await db.execute(select(Device).where(Device.device_id == request.device_id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device ID already registered"
        )

    new_device = Device(
        device_id=request.device_id,
        user_id=request.user_id,
        hashed_password=hash_password(request.password),
        name=request.name
    )
    db.add(new_device)
    await db.commit()
    await db.refresh(new_device)

    token = create_access_token(new_device.device_id)
    return TokenResponse(access_token=token, device_id=new_device.device_id)


@router.post("/login", response_model=TokenResponse)
async def login(request: DeviceLoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a device and return a JWT access token."""
    result = await db.execute(select(Device).where(Device.device_id == request.device_id))
    device = result.scalar_one_or_none()

    if not device or not verify_password(request.password, device.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect device_id or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not device.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device is inactive",
        )

    device.last_seen = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token(device.device_id)
    return TokenResponse(access_token=token, device_id=device.device_id)
