"""
SQLAlchemy ORM models — Alumni Portal
Cổng thông tin kết nối Cựu sinh viên, Khoa & Sinh viên.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

UserRole = Enum("student", "alumni", "admin", name="user_role", native_enum=False)

JobPostStatus = Enum(
    "PENDING", "APPROVED", "REJECTED", "CLOSED", name="job_post_status", native_enum=False
)

JobType = Enum("full_time", "part_time", "internship", name="job_type", native_enum=False)

EventType = Enum(
    "anniversary", "talkshow", "workshop", "seminar", "other", name="event_type", native_enum=False
)

RegistrationType = Enum("attendee", "speaker", name="registration_type", native_enum=False)

RegistrationStatus = Enum(
    "REGISTERED", "ATTENDED", "CANCELLED", name="registration_status", native_enum=False
)

SurveyStatus = Enum("DRAFT", "ACTIVE", "CLOSED", name="survey_status", native_enum=False)

QuestionType = Enum(
    "text", "single_choice", "multiple_choice", "scale", name="question_type", native_enum=False
)

AidApplicationStatus = Enum(
    "PENDING", "APPROVED", "REJECTED", "DISBURSED", name="aid_application_status", native_enum=False
)

ContributionStatus = Enum("PLEDGED", "CONFIRMED", name="contribution_status", native_enum=False)

DocumentStatus = Enum("PROCESSING", "READY", "FAILED", name="document_status", native_enum=False)


# ---------------------------------------------------------------------------
# users — tài khoản đăng nhập (admin / alumni / student)
# ---------------------------------------------------------------------------


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    role: Mapped[str] = mapped_column(UserRole, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    student_id: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)

    # Thông tin thêm
    graduation_year: Mapped[int | None] = mapped_column(Integer)
    major: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    alumni_profile: Mapped[Optional["AlumniProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    job_posts: Mapped[list["JobPost"]] = relationship(
        back_populates="created_by", foreign_keys="JobPost.created_by_id"
    )
    job_applications: Mapped[list["JobApplication"]] = relationship(back_populates="applicant")
    event_registrations: Mapped[list["EventRegistration"]] = relationship(back_populates="user")
    survey_responses: Mapped[list["SurveyResponse"]] = relationship(back_populates="respondent")
    financial_contributions: Mapped[list["FinancialContribution"]] = relationship(
        back_populates="contributor"
    )
    aid_applications: Mapped[list["AidApplication"]] = relationship(
        back_populates="applicant", foreign_keys="[AidApplication.applicant_id]"
    )


# ---------------------------------------------------------------------------
# companies — đơn vị công tác của cựu sinh viên
# ---------------------------------------------------------------------------


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    industry: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(500))
    address: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    alumni_profiles: Mapped[list["AlumniProfile"]] = relationship(back_populates="company_rel")
    job_posts: Mapped[list["JobPost"]] = relationship(back_populates="company")

    __table_args__ = (Index("idx_companies_name", "name"),)


# ---------------------------------------------------------------------------
# alumni_profiles — hồ sơ đầy đủ cựu sinh viên
# ---------------------------------------------------------------------------


class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )

    # Thông tin cơ bản
    student_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))

    # Thông tin học vấn
    graduation_year: Mapped[int | None] = mapped_column(Integer)
    major: Mapped[str | None] = mapped_column(String(255))
    gpa: Mapped[float | None] = mapped_column(Numeric(3, 2))

    # Thông tin công tác
    current_job_title: Mapped[str | None] = mapped_column(String(255))
    company_name: Mapped[str | None] = mapped_column(String(255))  # fallback nếu chưa có company_id
    work_location: Mapped[str | None] = mapped_column(String(255))
    job_field: Mapped[str | None] = mapped_column(String(255))  # đúng ngành / trái ngành

    # Thêm thông tin
    bio: Mapped[str | None] = mapped_column(Text)
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    skills: Mapped[dict | None] = mapped_column(JSON)  # {"items": ["Python", "Java", ...]}
    achievements: Mapped[str | None] = mapped_column(Text)

    # Meta
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    raw_text: Mapped[str | None] = mapped_column(Text)  # text gốc từ import

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="alumni_profile")
    company_rel: Mapped[Optional["Company"]] = relationship(back_populates="alumni_profiles")

    __table_args__ = (
        Index("idx_alumni_profiles_graduation_year", "graduation_year"),
        Index("idx_alumni_profiles_major", "major"),
    )


# ---------------------------------------------------------------------------
# import_sessions — theo dõi batch import từ Excel/PDF
# ---------------------------------------------------------------------------


class ImportSession(Base):
    __tablename__ = "import_sessions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(DocumentStatus, nullable=False, server_default="PROCESSING")
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    new_records: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    updated_records: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error: Mapped[str | None] = mapped_column(Text)
    preview_data: Mapped[dict | None] = mapped_column(JSON)  # records chờ xác nhận

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ---------------------------------------------------------------------------
# job_posts — tin tuyển dụng / thực tập
# ---------------------------------------------------------------------------


class JobPost(Base):
    __tablename__ = "job_posts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="SET NULL")
    )
    company_name: Mapped[str | None] = mapped_column(String(255))
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_type: Mapped[str] = mapped_column(JobType, nullable=False)  # full_time | internship | ...
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text)
    benefits: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))
    salary_min: Mapped[int | None] = mapped_column(Integer)  # VND
    salary_max: Mapped[int | None] = mapped_column(Integer)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(JobPostStatus, nullable=False, server_default="PENDING")
    rejection_note: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    created_by: Mapped[Optional["User"]] = relationship(
        back_populates="job_posts", foreign_keys=[created_by_id]
    )
    company: Mapped[Optional["Company"]] = relationship(back_populates="job_posts")
    applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="job_post", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_job_posts_status", "status"),
        Index("idx_job_posts_job_type", "job_type"),
        Index("idx_job_posts_created_at", "created_at"),
    )


# ---------------------------------------------------------------------------
# job_applications — ứng tuyển của sinh viên
# ---------------------------------------------------------------------------


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job_post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("job_posts.id", ondelete="CASCADE")
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE")
    )

    cover_letter: Mapped[str | None] = mapped_column(Text)
    cv_url: Mapped[str | None] = mapped_column(String(500))  # URL hoặc tên file
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="submitted")
    note: Mapped[str | None] = mapped_column(Text)  # note từ người tuyển

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    job_post: Mapped["JobPost"] = relationship(back_populates="applications")
    applicant: Mapped["User"] = relationship(back_populates="job_applications")

    __table_args__ = (
        Index("idx_job_applications_job_post_id", "job_post_id"),
        Index("idx_job_applications_applicant_id", "applicant_id"),
    )


# ---------------------------------------------------------------------------
# events — sự kiện, talkshow, lễ kỷ niệm
# ---------------------------------------------------------------------------


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = _uuid_pk()
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(EventType, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(500))
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    online_link: Mapped[str | None] = mapped_column(String(500))

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    max_attendees: Mapped[int | None] = mapped_column(Integer)
    max_speakers: Mapped[int | None] = mapped_column(Integer)

    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    banner_url: Mapped[str | None] = mapped_column(String(500))
    agenda: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    registrations: Mapped[list["EventRegistration"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_events_start_time", "start_time"),
        Index("idx_events_event_type", "event_type"),
        Index("idx_events_is_published", "is_published"),
    )


# ---------------------------------------------------------------------------
# event_registrations — đăng ký tham dự / làm diễn giả
# ---------------------------------------------------------------------------


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("events.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE")
    )

    registration_type: Mapped[str] = mapped_column(
        RegistrationType, nullable=False, server_default="attendee"
    )
    status: Mapped[str] = mapped_column(
        RegistrationStatus, nullable=False, server_default="REGISTERED"
    )

    # Thông tin diễn giả (nếu type = speaker)
    speaker_topic: Mapped[str | None] = mapped_column(String(500))
    speaker_bio: Mapped[str | None] = mapped_column(Text)

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="registrations")
    user: Mapped["User"] = relationship(back_populates="event_registrations")

    __table_args__ = (
        Index("idx_event_reg_event_id", "event_id"),
        Index("idx_event_reg_user_id", "user_id"),
    )


# ---------------------------------------------------------------------------
# surveys — biểu mẫu khảo sát việc làm sau tốt nghiệp
# ---------------------------------------------------------------------------


class Survey(Base):
    __tablename__ = "surveys"

    id: Mapped[uuid.UUID] = _uuid_pk()
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(SurveyStatus, nullable=False, server_default="DRAFT")

    # Lọc theo khóa tốt nghiệp (None = gửi tất cả CSV)
    target_graduation_year: Mapped[int | None] = mapped_column(Integer)

    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    questions: Mapped[list["SurveyQuestion"]] = relationship(
        back_populates="survey", cascade="all, delete-orphan", order_by="SurveyQuestion.order_index"
    )
    responses: Mapped[list["SurveyResponse"]] = relationship(
        back_populates="survey", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# survey_questions — câu hỏi trong khảo sát
# ---------------------------------------------------------------------------


class SurveyQuestion(Base):
    __tablename__ = "survey_questions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    survey_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("surveys.id", ondelete="CASCADE")
    )

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(QuestionType, nullable=False)
    options: Mapped[dict | None] = mapped_column(JSON)  # {"items": ["Có", "Không"]}
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # Relationships
    survey: Mapped["Survey"] = relationship(back_populates="questions")
    answers: Mapped[list["SurveyAnswer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# survey_responses — một lần điền của một CSV
# ---------------------------------------------------------------------------


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id: Mapped[uuid.UUID] = _uuid_pk()
    survey_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("surveys.id", ondelete="CASCADE")
    )
    respondent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE")
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    survey: Mapped["Survey"] = relationship(back_populates="responses")
    respondent: Mapped["User"] = relationship(back_populates="survey_responses")
    answers: Mapped[list["SurveyAnswer"]] = relationship(
        back_populates="response", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_survey_responses_survey_id", "survey_id"),
        Index("idx_survey_responses_respondent_id", "respondent_id"),
    )


# ---------------------------------------------------------------------------
# survey_answers — câu trả lời cho từng câu hỏi
# ---------------------------------------------------------------------------


class SurveyAnswer(Base):
    __tablename__ = "survey_answers"

    id: Mapped[uuid.UUID] = _uuid_pk()
    response_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("survey_responses.id", ondelete="CASCADE")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("survey_questions.id", ondelete="CASCADE")
    )

    answer_text: Mapped[str | None] = mapped_column(Text)  # cho text type
    answer_choices: Mapped[dict | None] = mapped_column(JSON)  # {"selected": ["A", "B"]}
    answer_scale: Mapped[int | None] = mapped_column(Integer)  # cho scale type

    # Relationships
    response: Mapped["SurveyResponse"] = relationship(back_populates="answers")
    question: Mapped["SurveyQuestion"] = relationship(back_populates="answers")


# ---------------------------------------------------------------------------
# financial_contributions — đóng góp quỹ học bổng từ CSV/Doanh nghiệp
# ---------------------------------------------------------------------------


class FinancialContribution(Base):
    __tablename__ = "financial_contributions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    contributor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )

    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # VND
    message: Mapped[str | None] = mapped_column(Text)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    status: Mapped[str] = mapped_column(
        ContributionStatus, nullable=False, server_default="PLEDGED"
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    contributor: Mapped[Optional["User"]] = relationship(back_populates="financial_contributions")


# ---------------------------------------------------------------------------
# aid_applications — đơn xin hỗ trợ tài chính / học bổng của sinh viên
# ---------------------------------------------------------------------------


class AidApplication(Base):
    __tablename__ = "aid_applications"

    id: Mapped[uuid.UUID] = _uuid_pk()
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE")
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL")
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    amount_requested: Mapped[int | None] = mapped_column(Integer)  # VND
    amount_approved: Mapped[int | None] = mapped_column(Integer)  # VND
    supporting_documents: Mapped[dict | None] = mapped_column(JSON)  # {"files": [...]}

    status: Mapped[str] = mapped_column(
        AidApplicationStatus, nullable=False, server_default="PENDING"
    )
    review_note: Mapped[str | None] = mapped_column(Text)
    disbursed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    applicant: Mapped["User"] = relationship(
        back_populates="aid_applications", foreign_keys=[applicant_id]
    )

    __table_args__ = (
        Index("idx_aid_applications_status", "status"),
        Index("idx_aid_applications_applicant_id", "applicant_id"),
    )
