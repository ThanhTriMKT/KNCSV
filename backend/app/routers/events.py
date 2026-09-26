"""
Events Router — Quản lý sự kiện, talkshow, lễ kỷ niệm.
"""

import uuid
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Event, EventRegistration, User
from app.database.session import get_session
from app.schemas.event_schemas import (
    AttendanceUpdate,
    EventCreate,
    EventListResult,
    EventRead,
    EventRegistrationCreate,
    EventRegistrationRead,
    EventUpdate,
)
from app.services.auth_service import (
    current_active_user,
    current_active_user_optional,
    require_admin,
)

router = APIRouter(prefix="/events", tags=["Events"])


# ─── Events ──────────────────────────────────────────────────────────────────


@router.get("", response_model=EventListResult)
async def list_events(
    event_type: str | None = Query(None),
    upcoming: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
    user: User | None = Depends(current_active_user_optional),
):
    from datetime import datetime

    stmt = select(Event)

    if not user or user.role != "admin":
        stmt = stmt.where(Event.is_published == True)  # noqa: E712

    if event_type:
        stmt = stmt.where(Event.event_type == event_type)
    if upcoming is True:
        now = datetime.now(UTC)
        stmt = stmt.where(Event.start_time >= now)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Event.start_time.asc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    events = result.scalars().all()

    items = []
    for ev in events:
        attendee_count = (
            await db.execute(
                select(func.count()).where(
                    EventRegistration.event_id == ev.id,
                    EventRegistration.registration_type == "attendee",
                )
            )
        ).scalar_one()
        speaker_count = (
            await db.execute(
                select(func.count()).where(
                    EventRegistration.event_id == ev.id,
                    EventRegistration.registration_type == "speaker",
                )
            )
        ).scalar_one()
        data = EventRead.model_validate(ev)
        data.attendee_count = attendee_count
        data.speaker_count = speaker_count
        items.append(data)

    return EventListResult(items=items, total=total, limit=limit, offset=offset)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    return EventRead.model_validate(ev)


@router.post("", response_model=EventRead, status_code=201)
async def create_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    """Chỉ Admin tạo sự kiện."""
    ev = Event(**data.model_dump())
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return EventRead.model_validate(ev)


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: uuid.UUID,
    data: EventUpdate,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(ev, field, value)
    await db.commit()
    await db.refresh(ev)
    return EventRead.model_validate(ev)


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    ev = await db.get(Event, event_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
    await db.delete(ev)
    await db.commit()


# ─── Event Registrations ──────────────────────────────────────────────────────


@router.post("/{event_id}/register", response_model=EventRegistrationRead, status_code=201)
async def register_event(
    event_id: uuid.UUID,
    data: EventRegistrationCreate,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    """Đăng ký tham dự hoặc làm diễn giả."""
    ev = await db.get(Event, event_id)
    if not ev or not ev.is_published:
        raise HTTPException(status_code=404, detail="Sự kiện không khả dụng")

    # Kiểm tra đã đăng ký chưa
    existing = (
        await db.execute(
            select(EventRegistration).where(
                EventRegistration.event_id == event_id,
                EventRegistration.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Bạn đã đăng ký sự kiện này rồi")

    # Kiểm tra speaker chỉ dành cho Alumni
    if data.registration_type == "speaker" and user.role not in ("alumni", "admin"):
        raise HTTPException(
            status_code=403, detail="Chỉ Cựu sinh viên mới được đăng ký làm Diễn giả"
        )

    # Kiểm tra giới hạn số lượng
    if data.registration_type == "attendee" and ev.max_attendees:
        count = (
            await db.execute(
                select(func.count()).where(
                    EventRegistration.event_id == event_id,
                    EventRegistration.registration_type == "attendee",
                    EventRegistration.status != "CANCELLED",
                )
            )
        ).scalar_one()
        if count >= ev.max_attendees:
            raise HTTPException(status_code=409, detail="Sự kiện đã đủ số người tham dự")

    reg = EventRegistration(
        event_id=event_id,
        user_id=user.id,
        registration_type=data.registration_type,
        speaker_topic=data.speaker_topic,
        speaker_bio=data.speaker_bio,
    )
    db.add(reg)
    await db.commit()
    await db.refresh(reg)

    result = EventRegistrationRead.model_validate(reg)
    result.user_name = user.full_name
    result.user_email = user.email
    result.user_role = user.role
    return result


@router.get("/{event_id}/registrations", response_model=list[EventRegistrationRead])
async def list_registrations(
    event_id: uuid.UUID,
    registration_type: str | None = Query(None),
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    """Admin xem danh sách đăng ký."""
    stmt = (
        select(EventRegistration, User)
        .join(User, EventRegistration.user_id == User.id)
        .where(EventRegistration.event_id == event_id)
    )
    if registration_type:
        stmt = stmt.where(EventRegistration.registration_type == registration_type)

    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for reg, u in rows:
        r = EventRegistrationRead.model_validate(reg)
        r.user_name = u.full_name
        r.user_email = u.email
        r.user_role = u.role
        items.append(r)
    return items


@router.patch("/{event_id}/registrations/{reg_id}/attendance")
async def update_attendance(
    event_id: uuid.UUID,
    reg_id: uuid.UUID,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_admin),
):
    """Admin điểm danh."""
    reg = await db.get(EventRegistration, reg_id)
    if not reg or reg.event_id != event_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy đăng ký")
    reg.status = data.status
    await db.commit()
    return {"message": "Cập nhật trạng thái thành công"}
