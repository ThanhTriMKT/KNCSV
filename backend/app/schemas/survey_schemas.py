"""
Pydantic schemas cho Surveys & Responses.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

QuestionTypeEnum = Literal["text", "single_choice", "multiple_choice", "scale"]


class SurveyQuestionCreate(BaseModel):
    question_text: str
    question_type: QuestionTypeEnum
    options: dict | None = None  # {"items": ["A", "B", "C"]}
    is_required: bool = True
    order_index: int = 0


class SurveyCreate(BaseModel):
    title: str
    description: str | None = None
    target_graduation_year: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    questions: list[SurveyQuestionCreate] = []


class SurveyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Literal["DRAFT", "ACTIVE", "CLOSED"] | None = None
    target_graduation_year: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class SurveyQuestionRead(BaseModel):
    id: uuid.UUID
    question_text: str
    question_type: str
    options: dict | None = None
    is_required: bool
    order_index: int

    model_config = {"from_attributes": True}


class SurveyRead(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    status: str
    target_graduation_year: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_at: datetime
    questions: list[SurveyQuestionRead] = []
    response_count: int = 0

    model_config = {"from_attributes": True}


class SurveyListResult(BaseModel):
    items: list[SurveyRead]
    total: int


# --------------- Survey Response ---------------


class SurveyAnswerCreate(BaseModel):
    question_id: uuid.UUID
    answer_text: str | None = None
    answer_choices: dict | None = None  # {"selected": ["A"]}
    answer_scale: int | None = None


class SurveyResponseCreate(BaseModel):
    answers: list[SurveyAnswerCreate]


class SurveyResponseRead(BaseModel):
    id: uuid.UUID
    survey_id: uuid.UUID
    respondent_id: uuid.UUID
    submitted_at: datetime
    respondent_name: str | None = None

    model_config = {"from_attributes": True}


# --------------- Survey Statistics ---------------


class SurveyStats(BaseModel):
    survey_id: uuid.UUID
    title: str
    total_responses: int
    questions: list[dict]  # mỗi question có stats riêng
