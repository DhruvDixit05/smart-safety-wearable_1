from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.device import Device
from app.models.emergency_contact import EmergencyContact
from app.schemas import EmergencyContactCreate, EmergencyContactResponse, MessageResponse
from app.services.auth_service import get_current_device

router = APIRouter(prefix="/api/emergency-contact", tags=["emergency-contacts"])


@router.post("", response_model=EmergencyContactResponse)
async def add_emergency_contact(
    request: EmergencyContactCreate,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """Add a new emergency contact for the device."""
    if request.device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    new_contact = EmergencyContact(
        device_id=request.device_id,
        name=request.name,
        relation=request.relation,
        phone_number=request.phone_number,
        priority=request.priority,
        is_active=True
    )
    db.add(new_contact)
    await db.commit()
    await db.refresh(new_contact)
    return new_contact


@router.get("/{device_id}", response_model=list[EmergencyContactResponse])
async def list_emergency_contacts(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """List active contacts sorted by priority (1=highest)."""
    if device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    result = await db.execute(
        select(EmergencyContact)
        .where(
            EmergencyContact.device_id == device_id,
            EmergencyContact.is_active == True
        )
        .order_by(EmergencyContact.priority.asc())
    )
    contacts = result.scalars().all()
    return contacts


@router.delete("/{contact_id}", response_model=MessageResponse)
async def delete_emergency_contact(
    contact_id: str,
    db: AsyncSession = Depends(get_db),
    current_device: Device = Depends(get_current_device)
):
    """Soft delete a contact (is_active=False)."""
    result = await db.execute(
        select(EmergencyContact).where(EmergencyContact.id == contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        
    if contact.device_id != current_device.device_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    contact.is_active = False
    await db.commit()
    return MessageResponse(message=f"Contact {contact_id} deactivated", success=True)
