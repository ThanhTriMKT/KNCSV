"""
Mentorship Sessions Router — SPEC §4 Luồng 1 bước 3-6.

Luồng: SV bấm "Xin tư vấn" → chọn hình thức (email | meet) → server gửi Gmail
qua Resend → CSV chấp nhận → tạo Meet link → +Điểm cống hiến cho CSV.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AlumniProfile, MentorshipSession, User
from app.database.session import get_session
from app.services.auth_service import current_active_user
from app.services.email_service import send_email_notification
from app.services.meet_service import CalendarAPIError, create_anonymous_meet_link
from app.services.points_service import add_pending_points, claim_pending_points_for_user

router = APIRouter(prefix="/mentorship", tags=["Mentorship"])


class RequestMentorshipBody(BaseModel):
    alumni_profile_id: str | None = None  # UUID của AlumniProfile được Agent gợi ý
    alumni_identifier: str | None = None  # Hoặc identifier/student_id từ client
    brief: str  # Brief do AI soạn sẵn
    channel: str = "email"  # "email" | "meet"
    conversation_id: uuid.UUID | None = None
    message_id: str | None = None


class AcceptMentorshipBody(BaseModel):
    session_id: str


@router.post("/request")
async def request_mentorship(
    body: RequestMentorshipBody,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    """
    [Luồng 1 bước 3-5] SV gửi yêu cầu tư vấn ẩn danh tới CSV đã được AI chọn.

    - Tạo MentorshipSession với status=PENDING.
    - Gửi email thông báo cho CSV qua Resend (SPEC bước 5).
    - Nếu channel="meet", tạo Meet link ngay và trả về luôn.
    """
    target_id = (body.alumni_profile_id or body.alumni_identifier or "").strip()
    if not target_id:
        raise HTTPException(status_code=400, detail="Thiếu thông tin định danh cựu sinh viên.")

    # Tìm theo UUID trước, nếu không phải UUID thì tìm theo student_id
    alumni_profile: AlumniProfile | None = None
    try:
        profile_uuid = uuid.UUID(target_id)
        res = await db.execute(select(AlumniProfile).where(AlumniProfile.id == profile_uuid))
        alumni_profile = res.scalar_one_or_none()
    except ValueError:
        pass

    if not alumni_profile:
        res = await db.execute(select(AlumniProfile).where(AlumniProfile.student_id == target_id))
        alumni_profile = res.scalar_one_or_none()

    if not alumni_profile:
        # Fallback: tìm theo tên ẩn danh (ví dụ "Anh/Chị L.T.H.V" hoặc "L.T.H.V") hoặc tên đầy đủ
        from app.services.rag_service import anonymize_name

        all_res = await db.execute(select(AlumniProfile))
        all_profiles = all_res.scalars().all()
        normalized_target = (
            target_id.lower()
            .replace("anh/chị", "")
            .replace("anh", "")
            .replace("chị", "")
            .replace(".", "")
            .strip()
        )
        for p in all_profiles:
            anon = anonymize_name(p.full_name)
            anon_clean = anon.lower().replace("anh/chị", "").replace(".", "").strip()
            if (
                target_id.lower() in anon.lower()
                or anon.lower() in target_id.lower()
                or (normalized_target and normalized_target == anon_clean)
                or target_id.lower() in p.full_name.lower()
            ):
                alumni_profile = p
                break

    if not alumni_profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ cựu sinh viên phù hợp.")

    channel = body.channel if body.channel in ("email", "meet") else "email"

    session = MentorshipSession(
        student_id=current_user.id,
        alumni_student_id=alumni_profile.student_id,
        brief=body.brief,
        channel=channel,
        status="PENDING",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    meet_link: str | None = None

    if channel == "meet":
        try:
            meet_link = await create_anonymous_meet_link(str(session.id))
            session.meet_link = meet_link
        except CalendarAPIError:
            pass  # fallback gracefully — session vẫn tạo được, chỉ thiếu meet_link

    # Gửi email thông báo cho CSV (SPEC bước 5: "Server gửi Gmail")
    email_sent = False
    if alumni_profile.email:
        subject = "Sinh viên mời bạn tham gia buổi tư vấn ẩn danh 15 phút"
        email_body = (
            f"Xin chào,\n\n"
            f"Một sinh viên muốn được tư vấn với bạn qua kênh: {channel.upper()}.\n\n"
            f"Nội dung brief:\n{body.brief}\n\n"
        )
        if meet_link:
            email_body += f"Link Google Meet: {meet_link}\n\n"
        email_body += (
            "Để xác nhận tham gia, vui lòng liên hệ qua hệ thống.\n\n"
            "Trân trọng,\nAI Alumni Platform"
        )
        email_sent = await send_email_notification(alumni_profile.email, subject, email_body)

    # --- WORKAROUND TẠM THỜI (2026-09) ---
    # Trước đây channel="meet" tự set status=ACCEPTED nhưng KHÔNG cộng điểm
    # (add_pending_points chỉ được gọi trong /mentorship/accept, mà endpoint
    # đó không có caller nào ở FE — Module 4 "điểm cống hiến" vì vậy chết
    # hoàn toàn dù DB/service đã viết đủ). Sửa: coi việc gửi thành công
    # (email hoặc tạo được Meet link thật/fallback) là điều kiện đủ để cộng
    # điểm ngay tại đây.
    # TODO: khi có trang "CSV xác nhận yêu cầu tư vấn" thật, chuyển cộng
    # điểm về đúng /mentorship/accept và xoá đoạn dưới đây.
    if email_sent or meet_link:
        session.status = "ACCEPTED"
        await db.commit()

        await add_pending_points(
            db,
            student_id=alumni_profile.student_id,
            points=15,
            session_id=session.id,
            reason="Được Sinh viên gửi yêu cầu tư vấn ẩn danh (auto-accept tạm thời)",
        )

        # Nếu CSV đã có tài khoản (không phải lần đăng ký đầu tiên), cộng
        # thẳng vào active_points ngay — claim_pending_points_for_user vốn
        # chỉ tự chạy 1 lần lúc đăng ký (auth_service.on_after_register),
        # nếu không gọi lại ở đây điểm sẽ kẹt vĩnh viễn trong pending_points
        # cho CSV tư vấn lần 2 trở đi.
        if alumni_profile.user_id:
            linked_user = await db.get(User, alumni_profile.user_id)
            if linked_user:
                await claim_pending_points_for_user(db, linked_user)

    # Cập nhật trạng thái Action Card trong ChatMessage.meta nếu có conversation_id
    if body.conversation_id:
        try:
            from app.database.models import ChatMessage

            target_msg = None
            if body.message_id:
                try:
                    msg_uuid = uuid.UUID(body.message_id)
                    res_msg = await db.execute(
                        select(ChatMessage).where(
                            ChatMessage.id == msg_uuid,
                            ChatMessage.conversation_id == body.conversation_id,
                        )
                    )
                    target_msg = res_msg.scalar_one_or_none()
                except ValueError:
                    pass

            if not target_msg:
                # Tìm assistant message gần nhất có action_card trong conversation
                res_msg = await db.execute(
                    select(ChatMessage)
                    .where(
                        ChatMessage.conversation_id == body.conversation_id,
                        ChatMessage.role == "assistant",
                    )
                    .order_by(ChatMessage.created_at.desc())
                    .limit(5)
                )
                for m in res_msg.scalars().all():
                    if m.meta and m.meta.get("action_card"):
                        target_msg = m
                        break

            if target_msg and target_msg.meta:
                meta_copy = dict(target_msg.meta)
                card = dict(meta_copy.get("action_card") or {})
                card["status"] = "approved"
                card["channel"] = channel
                card["session_id"] = str(session.id)
                card["result"] = {
                    "status": "success",
                    "message": (
                        "Đã gửi yêu cầu tư vấn qua Email tới Cựu sinh viên thành công!"
                        if channel == "email"
                        else "Đã tạo phòng Google Meet và gửi thông báo tới Cựu sinh viên!"
                    ),
                    "meetLink": meet_link,
                }
                meta_copy["action_card"] = card
                target_msg.meta = meta_copy
                await db.commit()
        except Exception as exc:
            logger.warning(f"Không thể cập nhật chat message meta sau khi gửi mentorship: {exc}")

    return {
        "status": "success",
        "message": (
            "Đã gửi yêu cầu tư vấn qua Email tới Cựu sinh viên thành công!"
            if channel == "email"
            else "Đã tạo phòng Google Meet và gửi thông báo tới Cựu sinh viên!"
        ),
        "session_id": str(session.id),
        "channel": channel,
        "meet_link": meet_link,
        "brief": session.brief,
    }


class DismissActionCardBody(BaseModel):
    conversation_id: uuid.UUID
    message_id: str | None = None


@router.post("/action-card/reject")
async def reject_action_card(
    body: DismissActionCardBody,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    """Lưu trạng thái rejected khi SV từ chối hoặc bỏ qua đề xuất kết nối."""
    from app.database.models import ChatMessage

    target_msg = None
    if body.message_id:
        try:
            msg_uuid = uuid.UUID(body.message_id)
            res_msg = await db.execute(
                select(ChatMessage).where(
                    ChatMessage.id == msg_uuid,
                    ChatMessage.conversation_id == body.conversation_id,
                )
            )
            target_msg = res_msg.scalar_one_or_none()
        except ValueError:
            pass

    if not target_msg:
        res_msg = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.conversation_id == body.conversation_id,
                ChatMessage.role == "assistant",
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(5)
        )
        for m in res_msg.scalars().all():
            if m.meta and m.meta.get("action_card"):
                target_msg = m
                break

    if target_msg and target_msg.meta:
        meta_copy = dict(target_msg.meta)
        card = dict(meta_copy.get("action_card") or {})
        card["status"] = "rejected"
        meta_copy["action_card"] = card
        target_msg.meta = meta_copy
        await db.commit()
        return {"status": "ok"}

    return {"status": "not_found"}


@router.post("/accept")
async def accept_mentorship(body: AcceptMentorshipBody, db: AsyncSession = Depends(get_session)):
    """
    [Luồng 1 bước 6] CSV xác nhận → tạo Meet link nếu chưa có →
    +Điểm cống hiến (PendingPoints theo alumni_student_id = MSSV của CSV).
    """
    try:
        session_uuid = uuid.UUID(body.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format.") from None

    stmt = select(MentorshipSession).where(MentorshipSession.id == session_uuid)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Mentorship session not found.")
    if session.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Session đã ở trạng thái '{session.status}'.")

    if not session.meet_link:
        meet_link = await create_anonymous_meet_link(str(session.id))
        session.meet_link = meet_link

    session.status = "ACCEPTED"
    await db.commit()

    # +Điểm cống hiến (SPEC bước 6) — alumni_student_id là MSSV của CSV
    await add_pending_points(
        db,
        student_id=session.alumni_student_id,
        points=15,
        session_id=session.id,
        reason="Hoàn thành chấp nhận tư vấn ẩn danh cho Sinh viên",
    )

    return {
        "status": "success",
        "message": "Phiên tư vấn đã được kích hoạt!",
        "session_id": str(session.id),
        "meet_link": session.meet_link,
    }


@router.get("/sessions/{session_id}")
async def get_session_status(session_id: str, db: AsyncSession = Depends(get_session)):
    """Kiểm tra trạng thái phiên tư vấn và lấy Meet link."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format.") from None

    stmt = select(MentorshipSession).where(MentorshipSession.id == session_uuid)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    return {
        "session_id": str(session.id),
        "status": session.status,
        "channel": session.channel,
        "meet_link": session.meet_link,
        "brief": session.brief,
    }
