import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.device import Device
from app.models.event import Event, EventStatus
from app.schemas import (
    FallEventCreate, 
    EventCancelRequest, 
    EventConfirmRequest, 
    EventResponse, 
    MessageResponse
)
from app.services.auth_service import get_current_device
from app.services.event_service import handle_pending_fall_event, _trigger_emergency_response

router = APIRouter(prefix="/api/event", tags=["events"])


@router.post("/fall", response_model=MessageResponse)
async def trigger_fall_event(
    request: FallEventCreate,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """Create pending fall event and start 5s timer."""
    if request.device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    new_event = Event(
        device_id=request.device_id,
        type=request.type,
        status=EventStatus.pending,
        latitude=request.lat,
        longitude=request.long,
        impact_force=request.impact
    )
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)

    # Start 5s timer in the background
    asyncio.create_task(handle_pending_fall_event(new_event.id))
    
    return MessageResponse(message=f"Created pending fall event {new_event.id}", success=True)


@router.post("/cancel", response_model=MessageResponse)
async def cancel_event(
    request: EventCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """User pressed 'I'm Safe', cancel pending event."""
    if request.device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await db.execute(select(Event).where(Event.id == request.event_id))
    event = result.scalar_one_or_none()

    if not event or event.device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        
    if event.status != EventStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Cannot cancel event with status {event.status}"
        )

    event.status = EventStatus.cancelled
    event.cancelled_at = datetime.now(timezone.utc)
    await db.commit()
    return MessageResponse(message="Event cancelled successfully", success=True)


@router.post("/confirm", response_model=MessageResponse)
async def confirm_event(
    request: EventConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """Manually confirm fall, triggering immediate emergency response."""
    if request.device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await db.execute(select(Event).where(Event.id == request.event_id))
    event = result.scalar_one_or_none()

    if not event or event.device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        
    if event.status not in (EventStatus.pending, EventStatus.confirmed):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Cannot manually confirm event with status {event.status}"
        )

    event.status = EventStatus.confirmed
    event.confirmed_at = datetime.now(timezone.utc)
    await db.commit()
    
    # Trigger alerting immediately
    asyncio.create_task(_trigger_emergency_response(event.id))
    
    return MessageResponse(message="Event confirmed and alerts triggered", success=True)


@router.get("/{device_id}", response_model=list[EventResponse])
async def list_recent_events(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """List recent events limit=20."""
    if device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await db.execute(
        select(Event)
        .where(Event.device_id == device_id)
        .order_by(Event.timestamp.desc())
        .limit(20)
    )
    events = result.scalars().all()
    return events
