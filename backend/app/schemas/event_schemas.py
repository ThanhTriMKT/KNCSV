"""
Pydantic schemas cho Events & Registrations.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

EventTypeEnum = Literal["anniversary", "talkshow", "workshop", "seminar", "other"]


class EventCreate(BaseModel):
    title: str
    event_type: EventTypeEnum
    description: str | None = None
    location: str | None = None
    is_online: bool = False
    online_link: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    max_attendees: int | None = None
    max_speakers: int | None = None
    banner_url: str | None = None
    agenda: str | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    event_type: EventTypeEnum | None = None
    description: str | None = None
    location: str | None = None
    is_online: bool | None = None
    online_link: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    max_attendees: int | None = None
    max_speakers: int | None = None
    is_published: bool | None = None
    banner_url: str | None = None
    agenda: str | None = None


class EventRead(BaseModel):
    id: uuid.UUID
    title: str
    event_type: str
    description: str | None = None
    location: str | None = None
    is_online: bool
    online_link: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    max_attendees: int | None = None
    max_speakers: int | None = None
    is_published: bool
    banner_url: str | None = None
    agenda: str | None = None
    created_at: datetime
    attendee_count: int = 0
    speaker_count: int = 0

    model_config = {"from_attributes": True}


class EventListResult(BaseModel):
    items: list[EventRead]
    total: int
    limit: int
    offset: int


# --------------- Event Registration ---------------


class EventRegistrationCreate(BaseModel):
    registration_type: Literal["attendee", "speaker"] = "attendee"
    speaker_topic: str | None = None
    speaker_bio: str | None = None


class EventRegistrationRead(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    user_id: uuid.UUID
    registration_type: str
    status: str
    speaker_topic: str | None = None
    speaker_bio: str | None = None
    registered_at: datetime
    user_name: str | None = None
    user_email: str | None = None
    user_role: str | None = None

    model_config = {"from_attributes": True}


class AttendanceUpdate(BaseModel):
    status: Literal["ATTENDED", "CANCELLED"]
