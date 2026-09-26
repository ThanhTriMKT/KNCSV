"""
Alumni Router — Quản lý hồ sơ Cựu sinh viên & Import từ Excel/PDF.
"""

import contextlib
import io
import uuid
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AlumniProfile, ImportSession, User
from app.database.session import get_session
from app.schemas.alumni_schemas import (
    AlumniListResult,
    AlumniProfileRead,
    AlumniProfileUpdate,
    ImportConfirmRequest,
    ImportPreviewRecord,
    ImportPreviewResult,
)
from app.services.auth_service import current_active_user, require_admin

router = APIRouter(prefix="/alumni", tags=["Alumni"])


# ─── Danh sách Alumni ────────────────────────────────────────────────────────


@router.get("", response_model=AlumniListResult)
async def list_alumni(
    search: str | None = Query(None, description="Tìm theo tên hoặc MSSV"),
    major: str | None = Query(None),
    graduation_year: int | None = Query(None),
    company: str | None = Query(None),
    is_verified: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    """Danh sách cựu sinh viên — public với thông tin cơ bản."""
    stmt = select(AlumniProfile)

    if search:
        stmt = stmt.where(
            AlumniProfile.full_name.ilike(f"%{search}%")
            | AlumniProfile.student_id.ilike(f"%{search}%")
        )
    if major:
        stmt = stmt.where(AlumniProfile.major.ilike(f"%{major}%"))
    if graduation_year:
        stmt = stmt.where(AlumniProfile.graduation_year == graduation_year)
    if company:
        stmt = stmt.where(AlumniProfile.company_name.ilike(f"%{company}%"))
    if is_verified is not None:
        stmt = stmt.where(AlumniProfile.is_verified == is_verified)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(AlumniProfile.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    profiles = result.scalars().all()

    return AlumniListResult(
        items=[AlumniProfileRead.model_validate(p) for p in profiles],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{profile_id}", response_model=AlumniProfileRead)
async def get_alumni(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
):
    profile = await db.get(AlumniProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ")
    return AlumniProfileRead.model_validate(profile)


@router.patch("/{profile_id}", response_model=AlumniProfileRead)
async def update_alumni(
    profile_id: uuid.UUID,
    data: AlumniProfileUpdate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    """Cập nhật hồ sơ — CSV chỉ sửa hồ sơ của mình, Admin sửa mọi hồ sơ."""
    profile = await db.get(AlumniProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ")

    if user.role != "admin" and profile.user_id != user.id:
        raise HTTPException(status_code=403, detail="Không có quyền chỉnh sửa")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return AlumniProfileRead.model_validate(profile)


@router.delete("/{profile_id}", status_code=204)
async def delete_alumni(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    """Xóa hồ sơ CSV — chỉ Admin."""
    profile = await db.get(AlumniProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ")
    await db.delete(profile)
    await db.commit()


# ─── Import từ Excel ─────────────────────────────────────────────────────────


@router.post("/import/upload", response_model=ImportPreviewResult)
@router.post("/import/preview", response_model=ImportPreviewResult)
async def upload_import(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    user: User = Depends(require_admin),
):
    """
    Admin upload file Excel (.xlsx) danh sách CSV.
    Trả về preview (thêm mới / cập nhật) trước khi xác nhận.
    """
    if not file.filename or not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ file Excel (.xlsx, .xls) hoặc CSV",
        )

    content = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(content), dtype=str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không đọc được file: {e}") from e

    # Chuẩn hóa tên cột
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Mapping cột cần thiết
    col_map = {
        "mssv": "student_id",
        "student_id": "student_id",
        "ma_sv": "student_id",
        "ho_ten": "full_name",
        "full_name": "full_name",
        "ten": "full_name",
        "email": "email",
        "khoa_tot_nghiep": "graduation_year",
        "graduation_year": "graduation_year",
        "nam_tot_nghiep": "graduation_year",
        "nganh": "major",
        "major": "major",
        "cong_ty": "company_name",
        "company": "company_name",
        "chuc_vu": "current_job_title",
        "job_title": "current_job_title",
    }

    mapped = {}
    for col in df.columns:
        if col in col_map:
            mapped[col_map[col]] = col

    required = ["student_id", "full_name", "email"]
    missing = [r for r in required if r not in mapped]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"File thiếu các cột: {missing}. Cần có: MSSV, Họ tên, Email",
        )

    records: list[ImportPreviewRecord] = []
    new_count = 0
    update_count = 0

    for _, row in df.iterrows():
        sid = str(row[mapped["student_id"]]).strip()
        if not sid or sid == "nan":
            continue

        existing_q = await db.execute(select(AlumniProfile).where(AlumniProfile.student_id == sid))
        existing = existing_q.scalar_one_or_none()

        rec_data: dict[str, Any] = {
            "student_id": sid,
            "full_name": str(row[mapped["full_name"]]).strip() if "full_name" in mapped else "",
            "email": str(row[mapped["email"]]).strip() if "email" in mapped else "",
        }
        if "graduation_year" in mapped:
            val = str(row[mapped["graduation_year"]]).strip()
            if val and val != "nan":
                with contextlib.suppress(ValueError):
                    rec_data["graduation_year"] = int(float(val))
        if "major" in mapped:
            val = str(row[mapped["major"]]).strip()
            if val and val != "nan":
                rec_data["major"] = val
        if "company_name" in mapped:
            val = str(row[mapped["company_name"]]).strip()
            if val and val != "nan":
                rec_data["company_name"] = val
        if "current_job_title" in mapped:
            val = str(row[mapped["current_job_title"]]).strip()
            if val and val != "nan":
                rec_data["current_job_title"] = val

        if existing:
            update_count += 1
            changes = {
                k: {"old": getattr(existing, k), "new": v}
                for k, v in rec_data.items()
                if k != "student_id" and getattr(existing, k, None) != v
            }
            records.append(ImportPreviewRecord(action="update", changes=changes, **rec_data))
        else:
            new_count += 1
            records.append(ImportPreviewRecord(action="create", **rec_data))

    # Lưu session import
    session = ImportSession(
        uploaded_by_id=user.id,
        filename=file.filename,
        status="READY",
        total_records=len(records),
        new_records=new_count,
        updated_records=update_count,
        preview_data={"records": [r.model_dump(mode="json") for r in records]},
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return ImportPreviewResult(
        session_id=session.id,
        filename=file.filename,
        total=len(records),
        new_count=new_count,
        update_count=update_count,
        records=records,
    )


@router.post("/import/confirm", status_code=200)
async def confirm_import(
    body: ImportConfirmRequest,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    """Admin xác nhận import — upsert các record đã chọn vào DB."""
    session = await db.get(ImportSession, body.session_id)
    if not session or not session.preview_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên import")

    records = session.preview_data.get("records", [])
    if body.selected_student_ids:
        records = [r for r in records if r["student_id"] in body.selected_student_ids]

    imported = 0
    for rec in records:
        existing_q = await db.execute(
            select(AlumniProfile).where(AlumniProfile.student_id == rec["student_id"])
        )
        existing = existing_q.scalar_one_or_none()
        if existing:
            for k, v in rec.items():
                if k not in ("student_id", "action", "changes") and v is not None:
                    setattr(existing, k, v)
        else:
            profile = AlumniProfile(
                student_id=rec["student_id"],
                full_name=rec.get("full_name", ""),
                email=rec.get("email", ""),
                graduation_year=rec.get("graduation_year"),
                major=rec.get("major"),
                company_name=rec.get("company_name"),
                current_job_title=rec.get("current_job_title"),
            )
            db.add(profile)
        imported += 1

    await db.commit()
    return {"imported": imported, "message": f"Đã import {imported} hồ sơ thành công"}
