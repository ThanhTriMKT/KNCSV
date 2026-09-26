"""
Jobs Router — Quản lý tin tuyển dụng & thực tập.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import JobApplication, JobPost, User
from app.database.session import get_session
from app.schemas.job_schemas import (
    JobApplicationCreate,
    JobApplicationListResult,
    JobApplicationRead,
    JobPostApprove,
    JobPostCreate,
    JobPostListResult,
    JobPostRead,
    JobPostUpdate,
)
from app.services.auth_service import (
    current_active_user,
    current_active_user_optional,
    require_admin,
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# ─── Job Posts ────────────────────────────────────────────────────────────────


@router.get("", response_model=JobPostListResult)
async def list_jobs(
    search: str | None = Query(None),
    job_type: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
    user: User | None = Depends(current_active_user_optional),
):
    """
    Public: chỉ trả về APPROVED jobs.
    Admin: có thể lọc thêm theo status.
    """
    stmt = select(JobPost)

    # Non-admin chỉ thấy bài đã duyệt
    if not user or user.role != "admin":
        stmt = stmt.where(JobPost.status == "APPROVED")
    elif status:
        stmt = stmt.where(JobPost.status == status)

    if search:
        stmt = stmt.where(
            JobPost.title.ilike(f"%{search}%") | JobPost.description.ilike(f"%{search}%")
        )
    if job_type:
        stmt = stmt.where(JobPost.job_type == job_type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(JobPost.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    posts = result.scalars().all()

    items = []
    for post in posts:
        app_count = (
            await db.execute(select(func.count()).where(JobApplication.job_post_id == post.id))
        ).scalar_one()
        data = JobPostRead.model_validate(post)
        data.application_count = app_count
        items.append(data)

    return JobPostListResult(items=items, total=total, limit=limit, offset=offset)


@router.get("/{job_id}", response_model=JobPostRead)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    post = await db.get(JobPost, job_id)
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin tuyển dụng")
    return JobPostRead.model_validate(post)


@router.post("", response_model=JobPostRead, status_code=201)
async def create_job(
    data: JobPostCreate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    """Alumni hoặc Admin tạo tin. Alumni → PENDING, Admin → APPROVED luôn."""
    if user.role not in ("alumni", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ Alumni hoặc Admin mới được đăng tin")

    post = JobPost(
        created_by_id=user.id,
        title=data.title,
        job_type=data.job_type,
        description=data.description,
        requirements=data.requirements,
        benefits=data.benefits,
        location=data.location,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        deadline=data.deadline,
        company_id=data.company_id,
        status="APPROVED" if user.role == "admin" else "PENDING",
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return JobPostRead.model_validate(post)


@router.patch("/{job_id}", response_model=JobPostRead)
async def update_job(
    job_id: uuid.UUID,
    data: JobPostUpdate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    post = await db.get(JobPost, job_id)
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin")

    if user.role != "admin" and post.created_by_id != user.id:
        raise HTTPException(status_code=403, detail="Không có quyền")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    return JobPostRead.model_validate(post)


@router.patch("/{job_id}/approve", response_model=JobPostRead)
async def approve_job(
    job_id: uuid.UUID,
    data: JobPostApprove,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(require_admin),
):
    """Admin duyệt hoặc từ chối tin tuyển dụng."""
    post = await db.get(JobPost, job_id)
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin")

    post.status = data.status
    post.approved_by_id = user.id
    if data.rejection_note:
        post.rejection_note = data.rejection_note

    await db.commit()
    await db.refresh(post)
    return JobPostRead.model_validate(post)


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(require_admin),
):
    post = await db.get(JobPost, job_id)
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin")
    await db.delete(post)
    await db.commit()


# ─── Job Applications ─────────────────────────────────────────────────────────


@router.post("/{job_id}/apply", response_model=JobApplicationRead, status_code=201)
async def apply_job(
    job_id: uuid.UUID,
    data: JobApplicationCreate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    """Sinh viên ứng tuyển."""
    post = await db.get(JobPost, job_id)
    if not post or post.status != "APPROVED":
        raise HTTPException(status_code=404, detail="Tin tuyển dụng không khả dụng")

    # Kiểm tra đã ứng tuyển chưa
    existing = (
        await db.execute(
            select(JobApplication).where(
                JobApplication.job_post_id == job_id,
                JobApplication.applicant_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Bạn đã ứng tuyển vị trí này rồi")

    app = JobApplication(
        job_post_id=job_id,
        applicant_id=user.id,
        cover_letter=data.cover_letter,
        cv_url=data.cv_url,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)

    result = JobApplicationRead.model_validate(app)
    result.applicant_name = user.full_name
    result.applicant_email = user.email
    return result


@router.get("/{job_id}/applications", response_model=JobApplicationListResult)
async def list_applications(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    """Alumni (người đăng tin) hoặc Admin xem danh sách ứng tuyển."""
    post = await db.get(JobPost, job_id)
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin")
    if user.role != "admin" and post.created_by_id != user.id:
        raise HTTPException(status_code=403, detail="Không có quyền")

    result = await db.execute(
        select(JobApplication, User)
        .join(User, JobApplication.applicant_id == User.id)
        .where(JobApplication.job_post_id == job_id)
    )
    rows = result.all()

    items = []
    for app, applicant in rows:
        r = JobApplicationRead.model_validate(app)
        r.applicant_name = applicant.full_name
        r.applicant_email = applicant.email
        items.append(r)

    return JobApplicationListResult(items=items, total=len(items))
