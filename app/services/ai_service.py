import logging
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client only if API key is provided
openai_client = None
if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_emergency_message(
    user_name: str, contact_name: str, relation: str, maps_url: str
) -> str:
    """
    Generate an urgent, personalized emergency message using OpenAI.
    Fallback to a hardcoded string if OpenAI is unconfigured or fails.
    """
    fallback_message = (
        f"EMERGENCY: {user_name} may have fallen! "
        f"Location: {maps_url} — Please check immediately."
    )

    if not openai_client:
        logger.warning("OpenAI API key not set. Using fallback emergency message.")
        return fallback_message

    prompt = (
        f"A person named {user_name} has potentially fallen. "
        f"Write a SHORT urgent emergency SMS (max 160 chars) for their {relation} named {contact_name}. "
        f"Include location: {maps_url}. Be direct and human."
    )

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an urgent emergency alert assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=60,
            temperature=0.2,
        )
        ai_message = response.choices[0].message.content.strip()
        # Fallback if too long or empty
        if not ai_message or len(ai_message) > 200:
            return fallback_message
        return ai_message
    except Exception as e:
        logger.error(f"Failed to generate OpenAI message: {e}")
        return fallback_message
