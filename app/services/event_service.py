import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.event import Event, EventStatus
from app.models.device import Device
from app.models.emergency_contact import EmergencyContact
from app.models.location import Location
from app.services.emergency_service import send_emergency_alerts

logger = logging.getLogger(__name__)


async def handle_pending_fall_event(event_id: str):
    """
    Background timer for fall events.
    Waits for FALL_CONFIRM_TIMEOUT_SECONDS. If not cancelled, confirms and triggers alerts.
    """
    await asyncio.sleep(settings.FALL_CONFIRM_TIMEOUT_SECONDS)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()

        if event and event.status == EventStatus.pending:
            logger.info(f"Event {event_id} timeout reached. Escalating to CONFIRMED.")
            event.status = EventStatus.confirmed
            event.confirmed_at = datetime.now(timezone.utc)
            await db.commit()
            
            # Immediately trigger alerts
            asyncio.create_task(_trigger_emergency_response(event_id))
        else:
            logger.info(f"Event {event_id} is no longer pending. Doing nothing.")


async def _trigger_emergency_response(event_id: str):
    """
    Fetches device names, contacts, and last location, then triggers SMS/Calls.
    Updates the database with sending results.
    """
    async with AsyncSessionLocal() as db:
        # Load event and its relationship with device
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            return

        device_id = event.device_id
        
        # Load Device
        dev_res = await db.execute(select(Device).where(Device.device_id == device_id))
        device = dev_res.scalar_one_or_none()
        
        # Load Contacts
        con_res = await db.execute(
            select(EmergencyContact)
            .where(EmergencyContact.device_id == device_id, EmergencyContact.is_active == True)
            .order_by(EmergencyContact.priority.asc())
        )
        contacts = con_res.scalars().all()
        
        # Load Latest Location
        loc_res = await db.execute(
            select(Location)
            .where(Location.device_id == device_id)
            .order_by(Location.timestamp.desc())
            .limit(1)
        )
        location = loc_res.scalar_one_or_none()
        
        map_url = location.google_maps_url if location else "Lat/Lng Not Found"
        device_name = device.name if device else str(device_id)

        logger.info(f"Triggering alerts for Event {event_id} (Device: {device_name})")

        # Send Alerts
        sms_ids, call_ids = await send_emergency_alerts(
            device_name=device_name,
            map_url=map_url,
            contacts=list(contacts)
        )
        
        # Update Event record status & sent flags
        event.status = EventStatus.responded
        if sms_ids:
            event.sms_sent = ",".join(sms_ids)
        if call_ids:
            event.call_initiated = ",".join(call_ids)
            
        await db.commit()
        logger.info(f"Emergency Response completed for Event {event_id}")
