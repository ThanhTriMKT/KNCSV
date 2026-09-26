"""
Tools cho create_agent — hàm Python thuần (không cần @tool decorator).

Docstring = mô tả cho LLM quyết định khi nào gọi tool.
Type hint = schema tham số truyền cho model.

QUY TẮC (giữ nguyên từ SPEC):
  1. KHÔNG viết business logic ở đây — delegate sang services/*.py.
  2. Tools đọc (search) → an toàn, cho vào agent mặc định.
  3. Tools có tác dụng phụ (gửi Email, tạo Meet) → KHÔNG đưa vào agent,
     kích hoạt qua REST endpoint /mentorship/request khi SV bấm nút.

interrupt_before được khai báo ở agent.py, không phải ở đây.
"""

import json
from typing import Annotated

# ---------------------------------------------------------------------------
# Tool 1: Yêu cầu thông tin bổ sung (trigger interrupt → hiện Form cho SV)
# ---------------------------------------------------------------------------


def request_more_info_form(
    reason: str,
    missing_fields: Annotated[
        list[str],
        "Danh sách tên field cần hỏi thêm, ví dụ: ['industry', 'skills', 'duration']",
    ],
    field_configs: Annotated[
        str,
        "JSON string của list[dict], mỗi dict có: name, label, type (text/select/multiselect/textarea), "
        "required (bool), placeholder (optional), options (list[str], chỉ khi select/multiselect). "
        'Ví dụ: [{"name":"industry","label":"Ngành muốn thực tập?",'
        '"type":"select","required":true,"options":["IT","Finance"]}]',
    ] = "[]",
) -> str:
    """Gọi tool này khi câu hỏi của sinh viên còn mơ hồ và cần thu thập thêm
    thông tin trước khi tìm kiếm CSV phù hợp. Tool này sẽ khiến hệ thống
    hiển thị Form nhập liệu cho sinh viên (giống Claude inline form).

    Chỉ hỏi tối đa 3 trường thực sự cần thiết để tìm CSV phù hợp.
    Thường hỏi: lĩnh vực/ngành, kỹ năng mong muốn, giai đoạn (SV năm mấy).
    """
    # Tool này bị interrupt_before — phần thân KHÔNG chạy ở lượt 1.
    # Khi resume (lượt 2), tool được cung cấp ToolMessage với form data từ SV.
    # Trả về marker để agent biết form đã được thu thập.
    return json.dumps(
        {
            "status": "form_collected",
            "reason": reason,
            "missing_fields": missing_fields,
        }
    )


# ---------------------------------------------------------------------------
# Tool 2: Tìm kiếm CSV trong pgvector
# ---------------------------------------------------------------------------


async def search_alumni_pgvector(
    subject: Annotated[str, "Chủ đề, ngành, kỹ năng hoặc câu hỏi cần tìm CSV phù hợp"],
    target_role: Annotated[str, "Vị trí/vai trò nghề nghiệp mong muốn (có thể để trống)"] = "",
) -> str:
    """Tìm kiếm cựu sinh viên phù hợp trong pgvector bằng semantic similarity.
    Gọi tool này sau khi đã có đủ thông tin từ sinh viên (sau form hoặc khi
    câu hỏi đã rõ ràng). Trả về danh sách CSV đã được ẩn danh hoá.
    KHÔNG bao giờ trả về SĐT, email hoặc Zalo ID thật.
    """
    from app.database.session import async_session_factory
    from app.services.rag_service import search_relevant_alumni

    query = f"{subject} {target_role}".strip()
    async with async_session_factory() as db:
        matches = await search_relevant_alumni(db, query)

    # Ẩn danh hoá trước khi trả về cho LLM
    safe_matches = [
        {
            "id": m.get("id"),
            "anonymized_name": m.get("anonymized_name"),
            "current_job": m.get("current_job"),
            "company": m.get("company"),
            "skills": m.get("skills", []),
            "courses_taken": m.get("courses_taken", []),
        }
        for m in matches
    ]
    return json.dumps(safe_matches, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool 3: Render card kết nối (trigger interrupt → hiện preview email cho SV)
# ---------------------------------------------------------------------------


def render_connection_action_card(
    alumni_id: Annotated[
        str,
        "ID (UUID) hoặc tên ẩn danh (ví dụ 'Anh/Chị L.T.H.V') của cựu sinh viên được chọn để kết nối",
    ],
    brief_content: Annotated[
        str,
        "Nội dung brief tư vấn 15 phút đã soạn sẵn, gồm: chủ đề, mục tiêu, "
        "2-3 câu hỏi chuẩn bị cho sinh viên",
    ],
) -> str:
    """Tạo card xem trước yêu cầu tư vấn ẩn danh để sinh viên duyệt và gửi Email hoặc hẹn Google Meet.

    LƯU Ý ĐẶC BIỆT QUAN TRỌNG:
    CHỈ GỌI TOOL NÀY khi sinh viên yêu cầu rõ ràng việc kết nối/soạn email/xin tư vấn (ví dụ: 'kết nối cho em',
    'soạn email giúp em', 'gửi brief tư vấn', 'hẹn meet') HOẶC khi sinh viên xác nhận đồng ý sau khi được gợi ý.
    TUYỆT ĐỐI KHÔNG gọi tool này khi sinh viên chỉ đang tìm kiếm hoặc hỏi thông tin về cựu sinh viên!
    """
    return json.dumps(
        {
            "status": "card_shown",
            "alumni_id": alumni_id,
            "brief_content": brief_content,
        }
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

# Tất cả tools cho agent — interrupt_before sẽ chặn trước khi chạy
# request_more_info_form và render_connection_action_card
ALL_TOOLS = [
    request_more_info_form,
    search_alumni_pgvector,
    render_connection_action_card,
]

# Tên tool cần DỪNG LẠI chờ dữ liệu THẬT từ người dùng trước khi agent có
# thể tiếp tục — truyền vào HumanInTheLoopMiddleware(interrupt_on=...) ở
# agent.py. CHỈ 1 tool cần việc này: request_more_info_form, vì đây là tool
# duy nhất mà kết quả trả về (câu trả lời form) không thể biết trước, phải
# chờ SV nhập. 3 tool còn lại chạy ngay, không bị chặn — kể cả
# render_connection_action_card (xem lý do ở docstring của nó phía trên).
INTERRUPT_TOOL_NAMES: list[str] = [
    request_more_info_form.__name__,
]
