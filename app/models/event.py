import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import String, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EventType(str, PyEnum):
    fall = "fall"
    gesture = "gesture"
    sos = "sos"


class EventStatus(str, PyEnum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    responded = "responded"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    device_id: Mapped[str] = mapped_column(
        String, ForeignKey("devices.device_id"), nullable=False
    )
    type: Mapped[EventType] = mapped_column(
        SAEnum(EventType), nullable=False
    )
    status: Mapped[EventStatus] = mapped_column(
        SAEnum(EventStatus), nullable=False, default=EventStatus.pending
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    impact_force: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_message: Mapped[str | None] = mapped_column(String, nullable=True)
    sms_sent: Mapped[str | None] = mapped_column(String, nullable=True)       # comma-separated contact IDs
    call_initiated: Mapped[str | None] = mapped_column(String, nullable=True)  # comma-separated contact IDs
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    device = relationship("Device", back_populates="events")
