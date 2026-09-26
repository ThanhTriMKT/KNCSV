"""
Pydantic schemas for Auth API (fastapi-users).
"""

import uuid
from datetime import datetime
from typing import Literal

from fastapi_users import schemas
from pydantic import Field

UserRoleLiteral = Literal["student", "alumni", "admin"]
SelfRegisterableRole = Literal["student", "alumni"]


class UserRead(schemas.BaseUser[uuid.UUID]):
    role: UserRoleLiteral
    full_name: str | None = None
    student_id: str | None = None
    graduation_year: int | None = None
    major: str | None = None
    phone: str | None = None
    created_at: datetime


class UserCreate(schemas.BaseUserCreate):
    role: SelfRegisterableRole = Field(
        description="'student' hoặc 'alumni'. Admin không tự đăng ký."
    )
    full_name: str | None = None
    student_id: str | None = None
    graduation_year: int | None = None
    major: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    full_name: str | None = None
    student_id: str | None = None
    graduation_year: int | None = None
    major: str | None = None
    phone: str | None = None
