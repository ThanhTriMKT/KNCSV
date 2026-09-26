"""
Pydantic schemas cho Financial Aid & Contributions.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# --------------- Financial Contribution ---------------


class FinancialContributionCreate(BaseModel):
    amount: int  # VND
    message: str | None = None
    is_anonymous: bool = False


class FinancialContributionRead(BaseModel):
    id: uuid.UUID
    contributor_id: uuid.UUID | None = None
    amount: int
    message: str | None = None
    is_anonymous: bool
    status: str
    confirmed_at: datetime | None = None
    created_at: datetime
    contributor_name: str | None = None  # None nếu anonymous hoặc chưa có user

    model_config = {"from_attributes": True}


class ContributionListResult(BaseModel):
    items: list[FinancialContributionRead]
    total: int
    total_amount: int  # tổng số tiền đã confirm


# --------------- Aid Application ---------------


class AidApplicationCreate(BaseModel):
    title: str
    reason: str
    amount_requested: int | None = None
    supporting_documents: dict | None = None  # {"files": ["url1", "url2"]}


class AidApplicationReview(BaseModel):
    status: Literal["APPROVED", "REJECTED", "DISBURSED"]
    amount_approved: int | None = None
    review_note: str | None = None


class AidApplicationRead(BaseModel):
    id: uuid.UUID
    applicant_id: uuid.UUID
    title: str
    reason: str
    amount_requested: int | None = None
    amount_approved: int | None = None
    supporting_documents: dict | None = None
    status: str
    review_note: str | None = None
    disbursed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    applicant_name: str | None = None
    applicant_email: str | None = None
    applicant_student_id: str | None = None

    model_config = {"from_attributes": True}


class AidApplicationListResult(BaseModel):
    items: list[AidApplicationRead]
    total: int
