"""
Pending Points System & Loyalty Credit Claim Service for Alumni.
Updated: standardized on alumni_student_id & email, added concurrency safety.
"""

import uuid
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PendingPoints, User


async def add_pending_points(
    db: AsyncSession,
    student_id: str,
    points: int = 10,
    session_id: str | uuid.UUID | None = None,
    reason: str = "Tư vấn cống hiến cho Sinh viên",
) -> PendingPoints:
    """
    Ghi nhận điểm chờ cho Cựu sinh viên chưa kích hoạt tài khoản theo MSSV (student_id).
    """
    session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id

    pp = PendingPoints(
        alumni_student_id=student_id.strip(),
        points=points,
        session_id=session_uuid,
        status="PENDING",
        reason=reason,
    )
    db.add(pp)
    await db.commit()
    await db.refresh(pp)

    logger.info(
        f"Recorded {points} pending points for alumni_student_id '{student_id}' (Session: {session_uuid})"
    )
    return pp


async def claim_pending_points_for_user(
    db: AsyncSession,
    user: User,
) -> dict[str, Any]:
    """
    Tìm kiếm toàn bộ điểm chờ theo student_id của tài khoản và chuyển vào active_points.
    """
    if not user.student_id:
        return {
            "claimed_points": 0,
            "total_active_points": user.active_points or 0,
            "claimed_records": 0,
        }

    # Dùng with_for_update() để khóa các dòng đang đọc, tránh race condition claim 2 lần
    stmt = (
        select(PendingPoints)
        .where(
            PendingPoints.alumni_student_id == user.student_id.strip(),
            PendingPoints.status == "PENDING",
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    pending_records = result.scalars().all()

    if not pending_records:
        return {
            "claimed_points": 0,
            "total_active_points": user.active_points or 0,
            "claimed_records": 0,
        }

    total_claimed = sum(record.points for record in pending_records)
    current_points = user.active_points or 0
    user.active_points = current_points + total_claimed

    for record in pending_records:
        record.status = "CLAIMED"

    await db.commit()
    await db.refresh(user)

    logger.info(
        f"User {user.id} ({user.student_id}) successfully claimed {total_claimed} points "
        f"across {len(pending_records)} pending records. New active_points: {user.active_points}"
    )

    return {
        "claimed_points": total_claimed,
        "total_active_points": user.active_points,
        "claimed_records": len(pending_records),
    }
