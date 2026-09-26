import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AlumniProfile, ChatConversation, ChatMessage, User
from app.services.rag_service import search_relevant_alumni


@pytest.mark.asyncio
async def test_hybrid_search_shopee_weights(db_session: AsyncSession):
    """
    Kiểm tra trọng số & độ chính xác của Hybrid Search:
    Khi tìm 'shope', 'Shopee' hoặc câu hỏi tự nhiên 'có anh chị nào làm việc tại shope ko',
    hồ sơ của Hoàng Ngọc Mai tại Shopee PHẢI luôn được xếp hạng số 1 (rank 1).
    """
    for query in ["shope", "Shopee", "có anh chị nào làm việc tại shope ko", "Shopee Product Lead"]:
        matches = await search_relevant_alumni(db_session, query, limit=5)
        assert len(matches) > 0, f"Không tìm thấy kết quả nào cho query: {query}"
        top = matches[0]
        assert top["company"] == "Shopee (Sea Group)", (
            f"Query '{query}' không trả về Shopee ở top 1! Kết quả thực tế: {top['company']} ({top['anonymized_name']})"
        )
        assert top["anonymized_name"] == "Anh/Chị H.N.M"


@pytest.mark.asyncio
async def test_clarification_persistence(client: AsyncClient, db_session: AsyncSession):
    """
    Kiểm tra lưu vết form câu hỏi bổ sung (request_more_info_form):
    1. Tạo 1 hội thoại với 1 message clarify (status pending).
    2. SV submit form (gửi query kèm clarification_data).
    3. Backend PHẢI cập nhật message clarify trước đó thành clarify_pending=False,
       clarify_status='answered', và lưu answers=clarification_data.
    """
    test_mssv = f"22{uuid.uuid4().int % 100000:05d}"
    email = f"{test_mssv}@dlu.edu.vn"
    pw = "TestPassword123!"

    # Đăng ký & login
    await client.post(
        "/api/auth/register", json={"email": email, "password": pw, "role": "student"}
    )
    login_res = await client.post("/api/auth/jwt/login", data={"username": email, "password": pw})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Lấy user
    user_res = await db_session.execute(select(User).where(User.email == email))
    user = user_res.scalar_one()

    # Tạo conversation và clarify message
    conv = ChatConversation(user_id=user.id, title="Test clarify flow")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    clarify_msg = ChatMessage(
        conversation_id=conv.id,
        role="assistant",
        content="",
        meta={
            "clarify_fields": [
                {
                    "name": "industry",
                    "label": "Lĩnh vực",
                    "type": "multiselect",
                    "options": ["Backend", "AI"],
                },
                {
                    "name": "stage",
                    "label": "Giai đoạn",
                    "type": "select",
                    "options": ["Năm 3", "Năm 4"],
                },
            ],
            "clarify_pending": True,
            "clarify_status": "pending",
        },
    )
    db_session.add(clarify_msg)
    await db_session.commit()
    await db_session.refresh(clarify_msg)

    # Sinh viên gửi câu trả lời qua /api/chat
    form_answers = {"industry": ["AI"], "stage": "Năm 3"}
    # Gửi chat request
    async with client.stream(
        "POST",
        "/api/chat",
        headers=headers,
        json={
            "query": "AI | Năm 3",
            "conversation_id": str(conv.id),
            "clarification_data": form_answers,
        },
    ) as response:
        assert response.status_code == 200
        # Đọc hết stream để router xử lý hoàn tất
        async for _ in response.aiter_lines():
            pass

    # Kiểm tra DB: clarify_msg trước đó đã được cập nhật thành công
    await db_session.refresh(clarify_msg)
    assert clarify_msg.meta["clarify_pending"] is False
    assert clarify_msg.meta["clarify_status"] == "answered"
    assert clarify_msg.meta["answers"] == form_answers


@pytest.mark.asyncio
async def test_action_card_persistence_and_reject(client: AsyncClient, db_session: AsyncSession):
    """
    Kiểm tra lưu vết form gửi email / tạo Google Meet (render_connection_action_card):
    1. Khi SV duyệt gửi yêu cầu tư vấn (/api/mentorship/request), ChatMessage.meta['action_card']
       phải được cập nhật status='approved', channel, result, session_id.
    2. Khi SV từ chối (/api/mentorship/action-card/reject), ChatMessage.meta['action_card']
       phải được cập nhật status='rejected'.
    """
    test_mssv = f"22{uuid.uuid4().int % 100000:05d}"
    email = f"{test_mssv}@dlu.edu.vn"
    pw = "TestPassword123!"

    await client.post(
        "/api/auth/register", json={"email": email, "password": pw, "role": "student"}
    )
    login_res = await client.post("/api/auth/jwt/login", data={"username": email, "password": pw})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    user_res = await db_session.execute(select(User).where(User.email == email))
    user = user_res.scalar_one()

    # Tìm 1 profile CSV
    prof_res = await db_session.execute(select(AlumniProfile).limit(1))
    profile = prof_res.scalar_one()

    # Tạo conversation và assistant message có action_card (status pending)
    conv = ChatConversation(user_id=user.id, title="Test action card")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    card_msg = ChatMessage(
        conversation_id=conv.id,
        role="assistant",
        content="Mình đã chuẩn bị brief kết nối cho bạn.",
        meta={
            "action_card": {
                "alumni_id": str(profile.id),
                "brief": "Brief tư vấn 15 phút về định hướng nghề nghiệp",
                "alumni_cards": [{"id": str(profile.id), "anonymized_name": "Anh/Chị Test"}],
                "status": "pending",
            }
        },
    )
    db_session.add(card_msg)
    await db_session.commit()
    await db_session.refresh(card_msg)

    # 1. Gửi yêu cầu tư vấn kèm conversation_id & message_id
    req_res = await client.post(
        "/api/mentorship/request",
        headers=headers,
        json={
            "alumni_profile_id": str(profile.id),
            "brief": "Brief tư vấn 15 phút về định hướng nghề nghiệp",
            "channel": "email",
            "conversation_id": str(conv.id),
            "message_id": str(card_msg.id),
        },
    )
    assert req_res.status_code == 200

    # Kiểm tra ChatMessage.meta trong DB đã được cập nhật thành 'approved'
    await db_session.refresh(card_msg)
    assert card_msg.meta["action_card"]["status"] == "approved"
    assert card_msg.meta["action_card"]["channel"] == "email"
    assert card_msg.meta["action_card"]["result"]["status"] == "success"

    # 2. Test reject action card
    rej_res = await client.post(
        "/api/mentorship/action-card/reject",
        headers=headers,
        json={
            "conversation_id": str(conv.id),
            "message_id": str(card_msg.id),
        },
    )
    assert rej_res.status_code == 200
    await db_session.refresh(card_msg)
    assert card_msg.meta["action_card"]["status"] == "rejected"
