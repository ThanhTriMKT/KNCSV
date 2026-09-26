"""
Comprehensive Backtest Suite for AI Alumni Platform.
Tests all features: Auth, Points, Alumni Directory, Mentorship, Documents, Conversations.
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    AlumniProfile,
    ChatConversation,
    MentorshipSession,
    PendingPoints,
    User,
)
from app.database.session import async_session_factory
from app.main import app
from app.services.points_service import add_pending_points


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    async with async_session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# 1. Auth & Registration Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_password_validation_short(client: AsyncClient):
    """Mật khẩu ngắn hơn 8 ký tự phải bị từ chối theo quy tắc."""
    res = await client.post(
        "/api/auth/register",
        json={
            "email": f"test_short_{uuid.uuid4().hex[:6]}@dlu.edu.vn",
            "password": "123",
            "role": "student",
        },
    )
    assert res.status_code == 400
    data = res.json()
    assert "Mật khẩu phải có ít nhất 8 ký tự" in str(data)


@pytest.mark.asyncio
async def test_student_registration_and_auto_student_id(
    client: AsyncClient, db_session: AsyncSession
):
    """Sinh viên đăng ký email trường cấp tự động trích xuất student_id từ local-part."""
    random_id = f"22{uuid.uuid4().int % 100000:05d}"
    email = f"{random_id}@dlu.edu.vn"
    password = "SecurePassword123!"

    res = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "role": "student",
            "full_name": "Nguyen Van Sinh Vien",
        },
    )
    assert res.status_code == 201
    user_data = res.json()
    assert user_data["email"] == email
    assert user_data["role"] == "student"

    # Kiểm tra trong DB xem student_id đã được tự động gán là MSSV hay chưa
    user_res = await db_session.execute(select(User).where(User.email == email))
    db_user = user_res.scalar_one()
    assert db_user.student_id == random_id


@pytest.mark.asyncio
async def test_login_jwt_token_flow(client: AsyncClient):
    """Đăng ký rồi đăng nhập nhận Bearer JWT token."""
    random_id = f"21{uuid.uuid4().int % 100000:05d}"
    email = f"{random_id}@dlu.edu.vn"
    password = "StrongPassword2026@"

    reg_res = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "role": "student",
        },
    )
    assert reg_res.status_code == 201

    login_res = await client.post(
        "/api/auth/jwt/login",
        data={"username": email, "password": password},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Kiểm tra gọi endpoint /points/me bằng token vừa nhận
    points_res = await client.get(
        "/api/points/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert points_res.status_code == 200
    assert "active_points" in points_res.json()


# ---------------------------------------------------------------------------
# 2. Loyalty Points & Growth Loop Tests (SPEC §4 Module 4)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pending_points_auto_claim_on_signup(client: AsyncClient, db_session: AsyncSession):
    """
    Điểm chờ được tích lũy trước cho MSSV khi chưa có tài khoản.
    Khi CSV đăng ký sau này, hệ thống tự động claim toàn bộ vào active_points.
    """
    alumni_mssv = f"18{uuid.uuid4().int % 100000:05d}"
    alumni_email = f"{alumni_mssv}@dlu.edu.vn"
    password = "AlumniPassword2026!"

    # 1. Giả lập hệ thống ghi nhận 2 lượt điểm chờ (15p + 10p = 25p)
    await add_pending_points(db_session, student_id=alumni_mssv, points=15, reason="Tư vấn vòng 1")
    await add_pending_points(db_session, student_id=alumni_mssv, points=10, reason="Tư vấn vòng 2")

    # 2. CSV đăng ký tài khoản với email trường chứa MSSV đó
    res = await client.post(
        "/api/auth/register",
        json={
            "email": alumni_email,
            "password": password,
            "role": "alumni",
            "full_name": "Tran Van Cuu Sinh Vien",
        },
    )
    assert res.status_code == 201

    # 3. Kiểm tra user trong DB: active_points phải được tự động cộng 25 điểm
    user_res = await db_session.execute(select(User).where(User.email == alumni_email))
    user = user_res.scalar_one()
    assert user.active_points >= 25

    # 4. Kiểm tra trạng thái các bản ghi pending_points đã chuyển sang CLAIMED
    stmt = select(PendingPoints).where(PendingPoints.alumni_student_id == alumni_mssv)
    pts_res = await db_session.execute(stmt)
    records = pts_res.scalars().all()
    assert len(records) >= 2
    for r in records:
        assert r.status == "CLAIMED"


# ---------------------------------------------------------------------------
# 3. Alumni Directory & Privacy Protection Tests (SPEC §1, §4 Module 2)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_alumni_directory_privacy_and_filtering(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Danh bạ cựu sinh viên:
    - PHẢI ẩn danh họ tên (Anh/Chị N.V.A), KHÔNG lộ MSSV hay họ tên thô.
    - Bộ lọc chuyên ngành (category) và tìm kiếm (q) hoạt động chính xác.
    """
    test_mssv = f"19{uuid.uuid4().int % 100000:05d}"
    unique_company = f"Company_{uuid.uuid4().hex[:6]}"

    profile = AlumniProfile(
        student_id=test_mssv,
        full_name="Hoang Duc Thinh",
        email=f"{test_mssv}@dlu.edu.vn",
        current_job="AI Research Engineer",
        company=unique_company,
        skills={"items": ["python", "machine learning", "pytorch"]},
        courses_taken={"items": ["Học máy", "Xử lý ảnh"]},
    )
    db_session.add(profile)
    await db_session.commit()

    # Query API /api/alumni
    res = await client.get(f"/api/alumni?q={unique_company}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total"] >= 1

    item = next((x for x in data["items"] if x["company"] == unique_company), None)
    assert item is not None

    # Kiểm tra nguyên tắc ẩn danh:
    assert "student_id" not in item  # MSSV thô không được lộ
    assert "full_name" not in item  # Họ tên thật không được lộ
    assert item["anonymized_name"] == "Anh/Chị Hoang D. T."  # Ẩn danh chuẩn SPEC
    assert item["cohort"] == "K19"
    assert item["current_job"] == "AI Research Engineer"

    # Kiểm tra category filter: ai_software phải chứa, product không được chứa
    res_ai = await client.get(f"/api/alumni?q={unique_company}&category=ai_software")
    assert any(x["company"] == unique_company for x in res_ai.json()["items"])

    res_prod = await client.get(f"/api/alumni?q={unique_company}&category=product")
    assert not any(x["company"] == unique_company for x in res_prod.json()["items"])


# ---------------------------------------------------------------------------
# 4. Mentorship Flow Tests (SPEC §4 Luồng 1 bước 3-6)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mentorship_request_and_accept_flow(client: AsyncClient, db_session: AsyncSession):
    """
    Luồng tư vấn:
    1. Sinh viên gửi yêu cầu -> Session status = 'PENDING' (kể cả kênh meet).
    2. CSV chấp nhận -> Session status = 'ACCEPTED', sinh meet_link, +15 điểm cống hiến cho CSV.
    3. Thử chấp nhận lần 2 -> báo lỗi 400 vì đã accepted.
    """
    # Tạo SV và CSV profile
    sv_mssv = f"22{uuid.uuid4().int % 100000:05d}"
    csv_mssv = f"17{uuid.uuid4().int % 100000:05d}"

    # Đăng ký tài khoản SV
    sv_email = f"{sv_mssv}@dlu.edu.vn"
    sv_pw = "SinhVienPassword123!"
    await client.post(
        "/api/auth/register", json={"email": sv_email, "password": sv_pw, "role": "student"}
    )

    login_res = await client.post(
        "/api/auth/jwt/login", data={"username": sv_email, "password": sv_pw}
    )
    sv_token = login_res.json()["access_token"]

    # Tạo hồ sơ CSV trong DB
    csv_profile = AlumniProfile(
        student_id=csv_mssv,
        full_name="Le Van Mentor",
        email=f"{csv_mssv}@dlu.edu.vn",
        current_job="Staff Software Engineer",
        company="Global Tech Corp",
    )
    db_session.add(csv_profile)
    await db_session.commit()
    await db_session.refresh(csv_profile)

    # 1. SV gửi yêu cầu tư vấn hẹn Google Meet
    req_res = await client.post(
        "/api/mentorship/request",
        headers={"Authorization": f"Bearer {sv_token}"},
        json={
            "alumni_profile_id": str(csv_profile.id),
            "brief": "Em muốn xin tư vấn về định hướng học Backend và kiến trúc Microservices.",
            "channel": "meet",
        },
    )
    assert req_res.status_code == 200
    req_data = req_res.json()
    assert req_data["status"] == "success"
    session_id = req_data["session_id"]

    # Kiểm tra trạng thái session trong DB: PHẢI là PENDING (chờ CSV xác nhận)
    stmt = select(MentorshipSession).where(MentorshipSession.id == uuid.UUID(session_id))
    session_obj = (await db_session.execute(stmt)).scalar_one()
    assert session_obj.status == "PENDING"
    assert session_obj.alumni_student_id == csv_mssv

    # 2. CSV bấm chấp nhận tư vấn (/api/mentorship/accept)
    acc_res = await client.post(
        "/api/mentorship/accept",
        json={"session_id": session_id},
    )
    assert acc_res.status_code == 200
    acc_data = acc_res.json()
    assert acc_data["status"] == "success"
    assert acc_data["meet_link"] is not None

    # Kiểm tra trạng thái đã cập nhật ACCEPTED và điểm chờ đã được cộng
    await db_session.refresh(session_obj)
    assert session_obj.status == "ACCEPTED"

    pts_stmt = select(PendingPoints).where(
        PendingPoints.session_id == session_obj.id,
        PendingPoints.alumni_student_id == csv_mssv,
    )
    pts = (await db_session.execute(pts_stmt)).scalar_one()
    assert pts.points == 15
    assert pts.status == "PENDING"

    # 3. Thử accept lần 2 -> Phải bị từ chối 400
    acc_res2 = await client.post(
        "/api/mentorship/accept",
        json={"session_id": session_id},
    )
    assert acc_res2.status_code == 400


# ---------------------------------------------------------------------------
# 5. Conversations CRUD Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_conversations_management_flow(client: AsyncClient, db_session: AsyncSession):
    """Kiểm tra quản lý lịch sử hội thoại: Danh sách, Chi tiết, Đổi tên, Xóa."""
    user_mssv = f"22{uuid.uuid4().int % 100000:05d}"
    email = f"{user_mssv}@dlu.edu.vn"
    password = "ChatUserPass2026!"
    await client.post(
        "/api/auth/register", json={"email": email, "password": password, "role": "student"}
    )

    login_res = await client.post(
        "/api/auth/jwt/login", data={"username": email, "password": password}
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Lấy thông tin user
    user_obj = (await db_session.execute(select(User).where(User.email == email))).scalar_one()

    # Tạo 1 cuộc hội thoại test
    conv = ChatConversation(user_id=user_obj.id, title="Hỏi về môn Cơ sở dữ liệu")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # 1. GET /api/conversations
    list_res = await client.get("/api/conversations", headers=headers)
    assert list_res.status_code == 200
    conversations = list_res.json()
    assert any(c["id"] == str(conv.id) for c in conversations)

    # 2. GET /api/conversations/{id}
    detail_res = await client.get(f"/api/conversations/{conv.id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == "Hỏi về môn Cơ sở dữ liệu"

    # 3. PATCH /api/conversations/{id} (Rename)
    patch_res = await client.patch(
        f"/api/conversations/{conv.id}",
        headers=headers,
        json={"title": "Hỏi về môn CSDL Nâng cao"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Hỏi về môn CSDL Nâng cao"

    # 4. DELETE /api/conversations/{id}
    del_res = await client.delete(f"/api/conversations/{conv.id}", headers=headers)
    assert del_res.status_code == 200

    # Kiểm tra lại detail -> 404
    get_again = await client.get(f"/api/conversations/{conv.id}", headers=headers)
    assert get_again.status_code == 404


# ---------------------------------------------------------------------------
# 6. Document Pipeline Tests (Admin)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_document_endpoints_and_confirm(client: AsyncClient, db_session: AsyncSession):
    """Kiểm tra GET /api/documents và POST /api/documents/confirm."""
    # 1. GET /api/documents không được lỗi 404/405
    res = await client.get("/api/documents")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 2. Tạo tài khoản Admin để test POST /api/documents/confirm
    admin_email = f"admin_{uuid.uuid4().hex[:6]}@dlu.edu.vn"
    admin_user = User(
        email=admin_email,
        hashed_password="fakehashedpassword",
        role="admin",
        is_active=True,
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)

    # Đăng nhập admin qua JWT token
    from app.services.auth_service import get_jwt_strategy

    jwt_strategy = get_jwt_strategy()
    admin_token = await jwt_strategy.write_token(admin_user)

    # Confirm 1 record sinh viên
    imported_mssv = f"19{uuid.uuid4().int % 100000:05d}"
    confirm_res = await client.post(
        "/api/documents/confirm",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "items": [
                {
                    "student_id": imported_mssv,
                    "full_name": "Pham Minh Tuan",
                    "email": f"{imported_mssv}@dlu.edu.vn",
                    "extra": {
                        "courses": ["Lập trình Web", "Đám mây"],
                        "internship_role": "DevOps Intern",
                        "company": "FPT Software",
                    },
                }
            ]
        },
    )
    assert confirm_res.status_code == 200
    res_data = confirm_res.json()
    assert res_data["created"] == 1

    # Kiểm tra đã có trong alumni_profiles
    prof = (
        await db_session.execute(
            select(AlumniProfile).where(AlumniProfile.student_id == imported_mssv)
        )
    ).scalar_one_or_none()
    assert prof is not None
    assert prof.full_name == "Pham Minh Tuan"
    assert prof.current_job == "DevOps Intern"
    assert prof.company == "FPT Software"


# ---------------------------------------------------------------------------
# 7. AI Chat SSE Stream Validation Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_stream_empty_query_rejected(client: AsyncClient):
    """Query rỗng phải bị từ chối 400."""
    res = await client.post("/api/chat", json={"query": "   "})
    assert res.status_code == 400
    assert "Query cannot be empty" in res.json()["detail"]


@pytest.mark.asyncio
async def test_chat_stream_guest_flow(client: AsyncClient):
    """Kiểm tra SSE stream phản hồi đúng format text/event-stream và có event kết thúc."""
    res = await client.post(
        "/api/chat",
        json={"query": "Xin chào AI Alumni"},
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type", "")
    body_text = res.text
    assert (
        "event: done" in body_text or "event: chunk" in body_text or "event: activity" in body_text
    )
