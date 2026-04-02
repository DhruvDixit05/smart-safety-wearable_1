import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    battery_level: Mapped[float] = mapped_column(Float, default=100.0)
    sim_status: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    locations = relationship("Location", back_populates="device", lazy="selectin")
    events = relationship("Event", back_populates="device", lazy="selectin")
    emergency_contacts = relationship(
        "EmergencyContact", back_populates="device", lazy="selectin"
    )
    statuses = relationship("DeviceStatus", back_populates="device", lazy="selectin")


class DeviceStatus(Base):
    __tablename__ = "device_statuses"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    device_id: Mapped[str] = mapped_column(
        String, ForeignKey("devices.device_id"), nullable=False
    )
    battery_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    sim_status: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    signal_strength: Mapped[float | None] = mapped_column(Float, nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    device = relationship("Device", back_populates="statuses")
