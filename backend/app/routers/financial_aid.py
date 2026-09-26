"""
Financial Aid Router — Quản lý Quỹ học bổng & Hỗ trợ tài chính.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AidApplication, FinancialContribution, User
from app.database.session import get_session
from app.schemas.financial_schemas import (
    AidApplicationCreate,
    AidApplicationListResult,
    AidApplicationRead,
    AidApplicationReview,
    ContributionListResult,
    FinancialContributionCreate,
    FinancialContributionRead,
)
from app.services.auth_service import current_active_user, require_admin

router = APIRouter(prefix="/financial-aid", tags=["Financial Aid"])


# ─── Financial Contributions ─────────────────────────────────────────────────


@router.get("/contributions", response_model=ContributionListResult)
async def list_contributions(
    db: AsyncSession = Depends(get_session),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Public: danh sách đóng góp (ẩn tên nếu anonymous)."""
    stmt = select(FinancialContribution).order_by(FinancialContribution.created_at.desc())
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    total_confirmed = (
        await db.execute(
            select(func.coalesce(func.sum(FinancialContribution.amount), 0)).where(
                FinancialContribution.status == "CONFIRMED"
            )
        )
    ).scalar_one()

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    contribs = result.scalars().all()

    items = []
    for c in contribs:
        r = FinancialContributionRead.model_validate(c)
        if c.is_anonymous:
            r.contributor_name = "Ẩn danh"
        items.append(r)

    return ContributionListResult(items=items, total=total, total_amount=total_confirmed)


@router.post("/contributions", response_model=FinancialContributionRead, status_code=201)
async def create_contribution(
    data: FinancialContributionCreate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    """Alumni/Admin đăng ký đóng góp quỹ."""
    if user.role not in ("alumni", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ Cựu sinh viên mới được đóng góp quỹ")

    contrib = FinancialContribution(
        contributor_id=user.id,
        amount=data.amount,
        message=data.message,
        is_anonymous=data.is_anonymous,
    )
    db.add(contrib)
    await db.commit()
    await db.refresh(contrib)

    r = FinancialContributionRead.model_validate(contrib)
    if not data.is_anonymous:
        r.contributor_name = user.full_name
    return r


@router.get("/stats")
async def get_financial_aid_stats(db: AsyncSession = Depends(get_session)):
    """Thống kê tổng quan Quỹ học bổng cựu sinh viên."""
    total_confirmed_amount = (
        await db.execute(
            select(func.coalesce(func.sum(FinancialContribution.amount), 0)).where(
                FinancialContribution.status == "CONFIRMED"
            )
        )
    ).scalar_one()

    total_contributors = (
        await db.execute(
            select(func.count(FinancialContribution.id)).where(
                FinancialContribution.status == "CONFIRMED"
            )
        )
    ).scalar_one()

    total_applications = (
        await db.execute(select(func.count(AidApplication.id)))
    ).scalar_one()

    total_granted_amount = (
        await db.execute(
            select(func.coalesce(func.sum(AidApplication.amount_approved), 0)).where(
                AidApplication.status.in_(["APPROVED", "DISBURSED"])
            )
        )
    ).scalar_one()

    total_students_helped = (
        await db.execute(
            select(func.count(AidApplication.id)).where(
                AidApplication.status.in_(["APPROVED", "DISBURSED"])
            )
        )
    ).scalar_one()

    return {
        "total_fund_amount": total_confirmed_amount,
        "total_contributors": total_contributors,
        "total_applications": total_applications,
        "total_granted_amount": total_granted_amount,
        "total_students_helped": total_students_helped,
    }


@router.put("/contributions/{contrib_id}/confirm")
@router.patch("/contributions/{contrib_id}/confirm")
async def confirm_contribution(
    contrib_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    """Admin xác nhận đã nhận tiền đóng góp."""
    contrib = await db.get(FinancialContribution, contrib_id)
    if not contrib:
        raise HTTPException(status_code=404, detail="Không tìm thấy đóng góp")
    contrib.status = "CONFIRMED"
    contrib.confirmed_at = datetime.now(UTC)
    await db.commit()
    return {"message": "Đã xác nhận đóng góp"}


# ─── Aid Applications ─────────────────────────────────────────────────────────


@router.get("/applications", response_model=AidApplicationListResult)
async def list_aid_applications(
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    """
    Sinh viên thấy đơn của mình.
    Admin thấy tất cả.
    """
    stmt = select(AidApplication)

    if user.role != "admin":
        stmt = stmt.where(AidApplication.applicant_id == user.id)
    elif status:
        stmt = stmt.where(AidApplication.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(AidApplication.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    apps = result.scalars().all()

    items = []
    for app in apps:
        r = AidApplicationRead.model_validate(app)
        if user.role == "admin":
            # Load applicant info
            applicant = await db.get(User, app.applicant_id)
            if applicant:
                r.applicant_name = applicant.full_name
                r.applicant_email = applicant.email
                r.applicant_student_id = applicant.student_id
        items.append(r)

    return AidApplicationListResult(items=items, total=total)


@router.post("/applications", response_model=AidApplicationRead, status_code=201)
async def create_aid_application(
    data: AidApplicationCreate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    """Sinh viên nộp đơn xin hỗ trợ tài chính."""
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Chỉ Sinh viên mới được nộp đơn")

    app = AidApplication(
        applicant_id=user.id,
        title=data.title,
        reason=data.reason,
        amount_requested=data.amount_requested,
        supporting_documents=data.supporting_documents,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return AidApplicationRead.model_validate(app)


@router.get("/applications/me", response_model=AidApplicationListResult)
async def get_my_aid_applications(
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    """Sinh viên xem danh sách các đơn đã nộp của mình."""
    stmt = (
        select(AidApplication)
        .where(AidApplication.applicant_id == user.id)
        .order_by(AidApplication.created_at.desc())
    )
    result = await db.execute(stmt)
    apps = result.scalars().all()
    items = []
    for app in apps:
        r = AidApplicationRead.model_validate(app)
        r.applicant_name = user.full_name
        r.applicant_email = user.email
        r.applicant_student_id = user.student_id
        items.append(r)
    return AidApplicationListResult(items=items, total=len(items))


@router.get("/applications/{app_id}", response_model=AidApplicationRead)
async def get_aid_application(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    app = await db.get(AidApplication, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn")
    if user.role != "admin" and app.applicant_id != user.id:
        raise HTTPException(status_code=403, detail="Không có quyền")
    return AidApplicationRead.model_validate(app)


@router.put("/applications/{app_id}/review", response_model=AidApplicationRead)
@router.patch("/applications/{app_id}/review", response_model=AidApplicationRead)
async def review_aid_application(
    app_id: uuid.UUID,
    data: AidApplicationReview,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(require_admin),
):
    """Admin xét duyệt đơn xin hỗ trợ."""
    app = await db.get(AidApplication, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn")

    app.status = data.status
    app.reviewed_by_id = user.id
    if data.amount_approved is not None:
        app.amount_approved = data.amount_approved
    if data.review_note:
        app.review_note = data.review_note
    if data.status == "DISBURSED":
        app.disbursed_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(app)
    return AidApplicationRead.model_validate(app)
