"""
Pydantic schemas cho Job Posts & Applications.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

JobTypeEnum = Literal["full_time", "part_time", "internship"]
JobPostStatusEnum = Literal["PENDING", "APPROVED", "REJECTED", "CLOSED"]


class JobPostCreate(BaseModel):
    title: str
    job_type: JobTypeEnum
    description: str
    requirements: str | None = None
    benefits: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    deadline: datetime | None = None
    company_id: uuid.UUID | None = None
    # Nếu chưa có company, nhập tên trực tiếp
    company_name: str | None = None


class JobPostUpdate(BaseModel):
    title: str | None = None
    job_type: JobTypeEnum | None = None
    description: str | None = None
    requirements: str | None = None
    benefits: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    deadline: datetime | None = None


class JobPostRead(BaseModel):
    id: uuid.UUID
    title: str
    job_type: str
    description: str
    requirements: str | None = None
    benefits: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    deadline: datetime | None = None
    status: str
    rejection_note: str | None = None
    created_by_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    company_name: str | None = None  # từ company relation hoặc trực tiếp
    created_at: datetime
    updated_at: datetime
    application_count: int = 0

    model_config = {"from_attributes": True}


class JobPostListResult(BaseModel):
    items: list[JobPostRead]
    total: int
    limit: int
    offset: int


class JobPostApprove(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    rejection_note: str | None = None


# --------------- Job Application ---------------


class JobApplicationCreate(BaseModel):
    cover_letter: str | None = None
    cv_url: str | None = None


class JobApplicationRead(BaseModel):
    id: uuid.UUID
    job_post_id: uuid.UUID
    applicant_id: uuid.UUID
    cover_letter: str | None = None
    cv_url: str | None = None
    status: str
    note: str | None = None
    created_at: datetime
    # Thông tin người ứng tuyển
    applicant_name: str | None = None
    applicant_email: str | None = None

    model_config = {"from_attributes": True}


class JobApplicationListResult(BaseModel):
    items: list[JobApplicationRead]
    total: int
