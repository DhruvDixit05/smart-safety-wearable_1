import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# ─────────────────────────────────────────────
# Generic
# ─────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

class DeviceRegisterRequest(BaseModel):
    device_id: str
    user_id: str
    password: str
    name: Optional[str] = None

    @field_validator("device_id")
    @classmethod
    def device_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("device_id must not be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class DeviceLoginRequest(BaseModel):
    device_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    device_id: str


# ─────────────────────────────────────────────
# Location
# ─────────────────────────────────────────────

class LocationCreate(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v


class LocationResponse(BaseModel):
    id: str
    device_id: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    timestamp: datetime
    google_maps_url: str

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────

class FallEventCreate(BaseModel):
    device_id: str
    type: str = "fall"
    lat: float
    long: float
    impact: Optional[float] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"fall", "gesture", "sos"}
        if v not in allowed:
            raise ValueError(f"Event type must be one of {allowed}")
        return v


class EventCancelRequest(BaseModel):
    event_id: str
    device_id: str


class EventConfirmRequest(BaseModel):
    event_id: str
    device_id: str


class EventResponse(BaseModel):
    id: str
    device_id: str
    type: str
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    impact_force: Optional[float] = None
    ai_message: Optional[str] = None
    sms_sent: Optional[str] = None
    call_initiated: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Emergency Contacts
# ─────────────────────────────────────────────

class EmergencyContactCreate(BaseModel):
    device_id: str
    name: str
    relation: str
    phone_number: str
    priority: int = 1

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # E.164 format: +<country_code><number>, 8-15 digits total
        cleaned = re.sub(r"\s+", "", v)
        if not re.match(r"^\+?[1-9]\d{7,14}$", cleaned):
            raise ValueError("Invalid phone number format. Use E.164 format e.g. +911234567890")
        return cleaned

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Priority must be >= 1 (1 = highest)")
        return v


class EmergencyContactResponse(BaseModel):
    id: str
    device_id: str
    name: str
    relation: str
    phone_number: str
    priority: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# Device Status
# ─────────────────────────────────────────────

class DeviceStatusCreate(BaseModel):
    device_id: str
    battery_level: Optional[float] = None
    sim_status: Optional[bool] = None
    signal_strength: Optional[float] = None
    firmware_version: Optional[str] = None


class DeviceStatusResponse(BaseModel):
    id: str
    device_id: str
    battery_level: Optional[float] = None
    sim_status: Optional[bool] = None
    signal_strength: Optional[float] = None
    firmware_version: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
