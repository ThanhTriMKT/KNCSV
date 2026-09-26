"""
Admin Document Pipeline: Upload → AI Extract → Preview diff → Confirm → Lưu DB.

Luồng duy nhất (SPEC §4 Module 1):
  1. Admin upload PDF tài liệu trường (bảng điểm, danh sách thực tập, đăng ký môn...)
  2. extract_text_from_pdf() → parse_student_document() trích xuất danh sách SV
  3. preview_student_document() so sánh với DB, trả diff để Admin xem trước
  4. confirm_student_document() upsert vào alumni_profiles (kể cả CSV chưa đăng ký)
"""

import uuid
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AlumniProfile, User
from app.services.parser_service import (
    DocumentType,
    extract_text_from_file,
    parse_student_document,
)
from app.services.rag_service import generate_embedding


async def preview_student_document(
    db: AsyncSession,
    file_bytes: bytes,
    filename: str,
    doc_type: DocumentType = "general",
) -> list[dict[str, Any]]:
    """
    Bước 1/2 của Admin Document Pipeline.

    Extract text từ file (PDF/Excel/CSV) → AI trích xuất danh sách sinh viên → query DB theo
    student_id để xác định trạng thái từng record (new | update) + diff nếu update.

    KHÔNG lưu bất kỳ gì vào DB.

    Trả về list[dict] mỗi phần tử gồm:
      - status: "new" | "update"
      - record: dict (dữ liệu trích xuất từ AI)
      - diff: dict | None (chỉ có khi status=="update", map field -> {old, new})
    """
    raw_text = extract_text_from_file(file_bytes, filename)
    if not raw_text.strip():
        logger.warning(f"File '{filename}' has no extractable text — preview returns empty list")
        return []

    records = await parse_student_document(raw_text, doc_type)
    if not records:
        return []

    preview_items: list[dict[str, Any]] = []
    for rec in records:
        student_id = (rec.get("student_id") or "").strip() or None
        full_name = (rec.get("full_name") or "").strip()
        email = (rec.get("email") or "").strip() or None
        phone = (rec.get("phone") or "").strip() or None
        extra = rec.get("extra") or {}

        # Định danh chính là student_id — tìm profile hiện có theo student_id
        existing_profile: AlumniProfile | None = None
        if student_id:
            profile_result = await db.execute(
                select(AlumniProfile).where(AlumniProfile.student_id == student_id)
            )
            existing_profile = profile_result.scalar_one_or_none()

        diff: dict[str, Any] | None = None
        status = "new"

        if existing_profile:
            status = "update"
            diff = {}

            new_skills = extra.get("courses") or []
            old_skills = (
                existing_profile.skills.get("items", [])
                if isinstance(existing_profile.skills, dict)
                else []
            )
            if set(new_skills) != set(old_skills):
                diff["skills"] = {"old": old_skills, "new": new_skills}

            new_job = extra.get("internship_role")
            if new_job and new_job != existing_profile.current_job:
                diff["current_job"] = {"old": existing_profile.current_job, "new": new_job}

            new_company = extra.get("company")
            if new_company and new_company != existing_profile.company:
                diff["company"] = {"old": existing_profile.company, "new": new_company}

            if not diff:
                diff = None  # no actual changes

        preview_items.append(
            {
                "status": status,
                "record": {
                    "student_id": student_id,
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "extra": extra,
                },
                "diff": diff,
            }
        )

    return preview_items


async def confirm_student_document(
    db: AsyncSession,
    preview_items: list[dict[str, Any]],
    uploaded_by_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """
    Bước 2/2 của Admin Document Pipeline.

    Nhận danh sách record đã Admin review, upsert vào alumni_profiles theo student_id.
    CSV chưa có tài khoản vẫn được import (user_id=None) — khi đăng ký sau,
    claim flow sẽ tự gắn user_id vào profile.

    Trả về {"created": int, "updated": int, "skipped": int}.
    """
    created = updated = skipped = 0
    skip_reasons: list[str] = []

    for item in preview_items:
        rec = item.get("record") or item
        student_id = (rec.get("student_id") or "").strip() or None
        full_name = (rec.get("full_name") or "").strip()
        email = (rec.get("email") or "").strip() or None
        phone = (rec.get("phone") or "").strip() or None
        extra = rec.get("extra") or {}

        # student_id và full_name là bắt buộc
        if not student_id or not full_name:
            skipped += 1
            missing = "MSSV" if not student_id else "họ tên"
            label = full_name or email or student_id or "(không rõ)"
            skip_reasons.append(f"{label}: thiếu {missing}")
            logger.debug(f"Skipping record — thiếu student_id hoặc full_name: {rec}")
            continue

        skills_list = extra.get("courses") or []
        current_job = extra.get("internship_role") or None
        company = extra.get("company") or None
        courses = extra.get("courses") or []

        # Tìm user đã đăng ký qua email (nếu có) để gắn user_id
        user: User | None = None
        if email:
            user_result = await db.execute(select(User).where(User.email == email))
            user = user_result.scalar_one_or_none()

        # Cập nhật phone nếu user đã có tài khoản và chưa có phone
        if user and phone and not user.phone:
            user.phone = phone

        # Build raw_text summary cho embedding
        raw_summary = (
            f"{full_name}. {current_job or ''} tại {company or ''}. Môn học: {', '.join(courses)}."
        )
        embedding = await generate_embedding(raw_summary)

        # Upsert theo student_id
        profile_result = await db.execute(
            select(AlumniProfile).where(AlumniProfile.student_id == student_id)
        )
        profile = profile_result.scalar_one_or_none()

        if profile:
            profile.full_name = full_name
            if email:
                profile.email = email
            if user and not profile.user_id:
                profile.user_id = user.id
            profile.skills = {"items": skills_list}
            if current_job:
                profile.current_job = current_job
            if company:
                profile.company = company
            if courses:
                profile.courses_taken = {"items": courses}
            profile.raw_text = raw_summary[:2000]
            profile.embedding = embedding
            updated += 1
        else:
            # user_id có thể None nếu CSV chưa đăng ký
            db.add(
                AlumniProfile(
                    user_id=user.id if user else None,
                    student_id=student_id,
                    full_name=full_name,
                    email=email or "",
                    raw_text=raw_summary[:2000],
                    embedding=embedding,
                    skills={"items": skills_list},
                    current_job=current_job,
                    company=company,
                    courses_taken={"items": courses},
                )
            )
            created += 1

    await db.commit()
    logger.info(
        f"confirm_student_document: created={created}, updated={updated}, skipped={skipped}"
    )
    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "skip_reasons": skip_reasons,
    }
