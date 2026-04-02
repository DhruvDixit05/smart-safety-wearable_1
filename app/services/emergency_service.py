import logging
from typing import List, Tuple

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

from app.config import settings
from app.models.emergency_contact import EmergencyContact
from app.services.ai_service import generate_emergency_message

logger = logging.getLogger(__name__)

# Initialize Twilio client lazily if configured
twilio_client = None
if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE_NUMBER:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


async def send_emergency_alerts(
    device_name: str, map_url: str, contacts: List[EmergencyContact]
) -> Tuple[List[str], List[str]]:
    """
    Generate AI emergency message and dispatch SMS & Voice calls.
    Returns lists of contact IDs successfully notified via SMS and Voice.
    """
    sent_sms_ids = []
    sent_call_ids = []

    for contact in contacts:
        # Create user-friendly names
        d_name = device_name or "A user"
        c_name = contact.name or "Contact"
        c_relation = contact.relation or "friend/family"

        # Generate message
        message_body = await generate_emergency_message(
            user_name=d_name, contact_name=c_name, relation=c_relation, maps_url=map_url
        )

        if twilio_client:
            # Send SMS
            try:
                msg = twilio_client.messages.create(
                    body=message_body,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=contact.phone_number,
                )
                logger.info(f"Sent SMS to {c_name} via Twilio SID {msg.sid}")
                sent_sms_ids.append(contact.id)
            except Exception as e:
                logger.error(f"Failed to send SMS to {c_name}: {e}")

            # Send Voice Call using TwiML
            try:
                call_script = (
                    f"Emergency alert. {d_name} may have fallen and needs immediate assistance. "
                    f"As their {c_relation}, please check on them immediately."
                )
                vr = VoiceResponse()
                vr.say(call_script, voice="alice")

                call = twilio_client.calls.create(
                    twiml=str(vr),
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=contact.phone_number,
                )
                logger.info(f"Initiated Voice Call to {c_name} via Twilio SID {call.sid}")
                sent_call_ids.append(contact.id)
            except Exception as e:
                logger.error(f"Failed to initiate call to {c_name}: {e}")

        else:
            # Fallback if Twilio not configured
            logger.warning(
                f"[SIMULATION] Twilio not configured. Would have sent SMS and CALL to {contact.phone_number}. "
                f"Message: {message_body}"
            )
            sent_sms_ids.append(contact.id)
            sent_call_ids.append(contact.id)

    return sent_sms_ids, sent_call_ids
