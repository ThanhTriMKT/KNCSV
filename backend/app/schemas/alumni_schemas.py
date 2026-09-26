"""
Pydantic schemas cho Alumni Profile & Company.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel

# --------------- Company ---------------


class CompanyBase(BaseModel):
    name: str
    industry: str | None = None
    website: str | None = None
    address: str | None = None
    description: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyRead(CompanyBase):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# --------------- AlumniProfile ---------------


class AlumniProfileBase(BaseModel):
    student_id: str
    full_name: str
    email: str
    phone: str | None = None
    graduation_year: int | None = None
    major: str | None = None
    gpa: float | None = None
    current_job_title: str | None = None
    company_name: str | None = None
    work_location: str | None = None
    job_field: str | None = None
    bio: str | None = None
    linkedin_url: str | None = None
    skills: dict | None = None
    achievements: str | None = None


class AlumniProfileCreate(AlumniProfileBase):
    pass


class AlumniProfileUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    graduation_year: int | None = None
    major: str | None = None
    gpa: float | None = None
    current_job_title: str | None = None
    company_name: str | None = None
    company_id: uuid.UUID | None = None
    work_location: str | None = None
    job_field: str | None = None
    bio: str | None = None
    linkedin_url: str | None = None
    skills: dict | None = None
    achievements: str | None = None
    is_verified: bool | None = None


class AlumniProfileRead(AlumniProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlumniListResult(BaseModel):
    items: list[AlumniProfileRead]
    total: int
    limit: int
    offset: int


# --------------- Import ---------------


class ImportPreviewRecord(BaseModel):
    action: str  # "create" | "update"
    student_id: str
    full_name: str
    email: str
    graduation_year: int | None = None
    major: str | None = None
    current_job_title: str | None = None
    company_name: str | None = None
    changes: dict | None = None  # chỉ có khi action = "update"


class ImportPreviewResult(BaseModel):
    session_id: uuid.UUID
    filename: str
    total: int
    new_count: int
    update_count: int
    records: list[ImportPreviewRecord]


class ImportConfirmRequest(BaseModel):
    session_id: uuid.UUID
    selected_student_ids: list[str] | None = None  # None = xác nhận tất cả
