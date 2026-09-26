"""
Schema nội bộ cho luồng chat.

Đây là "hợp đồng" duy nhất mà routers/chat.py và frontend dựa vào.
Không phụ thuộc vào bất kỳ AI framework nào (LangGraph, langchain, ...).

Luồng sự kiện SSE:
  activity  → tiến trình đang xử lý
  clarify   → AI cần SV bổ sung thông tin → frontend render inline form
  chunk     → đoạn text câu trả lời stream dần
  action_card → AI đề xuất card tư vấn → frontend hiển thị preview email + nút duyệt
  meta      → tóm tắt cuối (brief + danh sách CSV)
  done      → kết thúc stream
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ActivityEvent:
    """SSE 'activity' — tiến trình xử lý (spinner/status bar cho SV thấy)."""

    label: str
    status: Literal["working", "complete"]
    tool: str | None = None


@dataclass
class ClarifyEvent:
    """SSE 'clarify' — AI cần thêm thông tin từ SV.

    Frontend nhận event này → render inline form (giống Claude.ai).
    SV điền xong → POST /api/chat cùng conversation_id + clarification_data.

    Mỗi field dict:
      name         key trong clarification_data khi gửi lại
      label        nhãn hiển thị
      type         "text" | "select" | "multiselect" | "textarea"
      required     bool
      placeholder  gợi ý (optional)
      options      list[str] — chỉ khi type select/multiselect
    """

    fields: list[dict] = field(default_factory=list)


@dataclass
class ChunkEvent:
    """SSE 'chunk' — 1 đoạn text câu trả lời, stream dần."""

    text: str


@dataclass
class ActionCardEvent:
    """SSE 'action_card' — AI đề xuất card kết nối tư vấn.

    Frontend hiển thị preview dạng email (giống Gemini compose view)
    với các nút: 'Gửi qua Zalo', 'Gửi qua Email', 'Tạo Google Meet'.
    SV bấm nút → gọi REST endpoint /api/mentorship/request.

    Fields:
      alumni_id      ID (ẩn danh) của CSV được đề xuất kết nối
      brief          nội dung brief tư vấn đã soạn sẵn
      alumni_cards   danh sách CSV gợi ý (anonymized)
    """

    alumni_id: str
    brief: str
    alumni_cards: list[dict] = field(default_factory=list)


@dataclass
class MetaEvent:
    """SSE 'meta' — tóm tắt cuối stream: brief + danh sách CSV + action_card (nếu có)."""

    brief: str
    recommended_alumni: list[dict]
    action_card: dict | None = None


@dataclass
class DoneEvent:
    """SSE 'done' — kết thúc stream."""

    status: str = "complete"


ChatEvent = ActivityEvent | ClarifyEvent | ChunkEvent | ActionCardEvent | MetaEvent | DoneEvent
