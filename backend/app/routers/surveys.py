"""
Surveys Router — Tạo & quản lý khảo sát việc làm sau tốt nghiệp.
"""

import uuid
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Survey, SurveyAnswer, SurveyQuestion, SurveyResponse, User
from app.database.session import get_session
from app.schemas.survey_schemas import (
    SurveyCreate,
    SurveyListResult,
    SurveyRead,
    SurveyResponseCreate,
    SurveyResponseRead,
    SurveyStats,
    SurveyUpdate,
)
from app.services.auth_service import (
    current_active_user,
    current_active_user_optional,
    require_admin,
)

router = APIRouter(prefix="/surveys", tags=["Surveys"])


# ─── Surveys ──────────────────────────────────────────────────────────────────


@router.get("", response_model=SurveyListResult)
async def list_surveys(
    db: AsyncSession = Depends(get_session),
    user: User | None = Depends(current_active_user_optional),
):
    stmt = select(Survey).options(selectinload(Survey.questions))
    if not user or user.role != "admin":
        stmt = stmt.where(Survey.status == "ACTIVE")

    result = await db.execute(stmt.order_by(Survey.created_at.desc()))
    surveys = result.scalars().all()

    items = []
    for sv in surveys:
        r_count = await db.execute(select(SurveyResponse).where(SurveyResponse.survey_id == sv.id))
        data = SurveyRead.model_validate(sv)
        data.response_count = len(r_count.scalars().all())
        items.append(data)

    return SurveyListResult(items=items, total=len(items))


@router.get("/{survey_id}", response_model=SurveyRead)
async def get_survey(survey_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(Survey).where(Survey.id == survey_id).options(selectinload(Survey.questions))
    )
    sv = result.scalar_one_or_none()
    if not sv:
        raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát")
    return SurveyRead.model_validate(sv)


@router.post("", response_model=SurveyRead, status_code=201)
async def create_survey(
    data: SurveyCreate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(require_admin),
):
    """Admin tạo biểu mẫu khảo sát."""
    sv = Survey(
        created_by_id=user.id,
        title=data.title,
        description=data.description,
        target_graduation_year=data.target_graduation_year,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(sv)
    await db.flush()  # get sv.id

    for q_data in data.questions:
        q = SurveyQuestion(
            survey_id=sv.id,
            question_text=q_data.question_text,
            question_type=q_data.question_type,
            options=q_data.options,
            is_required=q_data.is_required,
            order_index=q_data.order_index,
        )
        db.add(q)

    await db.commit()
    await db.refresh(sv, ["questions"])
    return SurveyRead.model_validate(sv)


@router.patch("/{survey_id}", response_model=SurveyRead)
async def update_survey(
    survey_id: uuid.UUID,
    data: SurveyUpdate,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    sv = await db.get(Survey, survey_id)
    if not sv:
        raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(sv, field, value)
    await db.commit()
    await db.refresh(sv, ["questions"])
    return SurveyRead.model_validate(sv)


@router.delete("/{survey_id}", status_code=204)
async def delete_survey(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    sv = await db.get(Survey, survey_id)
    if not sv:
        raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát")
    await db.delete(sv)
    await db.commit()


# ─── Survey Responses ─────────────────────────────────────────────────────────


@router.post("/{survey_id}/respond", response_model=SurveyResponseRead, status_code=201)
async def submit_response(
    survey_id: uuid.UUID,
    data: SurveyResponseCreate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    """Alumni điền khảo sát."""
    sv = await db.get(Survey, survey_id)
    if not sv or sv.status != "ACTIVE":
        raise HTTPException(status_code=404, detail="Khảo sát không khả dụng")

    if user.role not in ("alumni", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ Cựu sinh viên mới được điền khảo sát")

    # Kiểm tra đã điền chưa
    existing = (
        await db.execute(
            select(SurveyResponse).where(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.respondent_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Bạn đã điền khảo sát này rồi")

    response = SurveyResponse(survey_id=survey_id, respondent_id=user.id)
    db.add(response)
    await db.flush()

    for ans_data in data.answers:
        ans = SurveyAnswer(
            response_id=response.id,
            question_id=ans_data.question_id,
            answer_text=ans_data.answer_text,
            answer_choices=ans_data.answer_choices,
            answer_scale=ans_data.answer_scale,
        )
        db.add(ans)

    await db.commit()
    await db.refresh(response)

    result = SurveyResponseRead.model_validate(response)
    result.respondent_name = user.full_name
    return result


@router.get("/{survey_id}/stats", response_model=SurveyStats)
async def get_survey_stats(
    survey_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    """Admin xem thống kê khảo sát."""
    result = await db.execute(
        select(Survey)
        .where(Survey.id == survey_id)
        .options(
            selectinload(Survey.questions).selectinload(SurveyQuestion.answers),
            selectinload(Survey.responses),
        )
    )
    sv = result.scalar_one_or_none()
    if not sv:
        raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát")

    questions_stats = []
    for q in sv.questions:
        answers = q.answers

        stat: dict = {
            "id": str(q.id),
            "question_text": q.question_text,
            "question_type": q.question_type,
            "total_answers": len(answers),
        }

        if q.question_type == "text":
            stat["sample_answers"] = [a.answer_text for a in answers[:5] if a.answer_text]
        elif q.question_type in ("single_choice", "multiple_choice"):
            counts: Counter = Counter()
            for a in answers:
                if a.answer_choices and "selected" in a.answer_choices:
                    for choice in a.answer_choices["selected"]:
                        counts[choice] += 1
            stat["choice_counts"] = dict(counts)
        elif q.question_type == "scale":
            vals = [a.answer_scale for a in answers if a.answer_scale is not None]
            stat["average"] = sum(vals) / len(vals) if vals else 0
            stat["distribution"] = dict(Counter(vals))

        questions_stats.append(stat)

    return SurveyStats(
        survey_id=sv.id,
        title=sv.title,
        total_responses=len(sv.responses),
        questions=questions_stats,
    )
