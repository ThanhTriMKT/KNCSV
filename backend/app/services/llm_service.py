"""
Adapter mỏng nối routers/chat.py với app/ai/agent.py (LangGraph).

Lý do tách lớp này:
  - routers/chat.py không biết gì về LangGraph — chỉ nhận AsyncGenerator.
  - app/ai/agent.py là file DUY NHẤT được phép import LangGraph/LangChain.
  - Nếu sau này đổi framework, chỉ sửa agent.py + file này,
    routers/chat.py không đổi dòng nào.

Không viết business logic ở đây — chỉ map ChatEvent sang kiểu dữ liệu
mà routers/chat.py kỳ vọng.
"""

from collections.abc import AsyncGenerator
from typing import Any

from loguru import logger

from app.ai.agent import run_chat_agent
from app.ai.schemas import (
    ActionCardEvent,
    ActivityEvent,
    ChunkEvent,
    ClarifyEvent,
    DoneEvent,
    MetaEvent,
)


class LLMUnavailableError(Exception):
    """Raise khi không có LLM provider nào được cấu hình (thiếu API key)."""


async def stream_chat_answer(
    query: str,
    alumni_matches: list[dict],  # reserved — pre-fetched RAG context
    conversation_id: str | None = None,
    clarification_data: dict | None = None,
    db: Any = None,  # AsyncSession inject từ router, tránh tạo session riêng trong agent
) -> AsyncGenerator[dict, None]:
    """Gọi LangGraph agent, yield dict chuẩn để routers/chat.py emit SSE.

    Yield format:
      {"type": "activity",    "label": str, "status": str}
      {"type": "clarify",     "fields": list[dict]}
      {"type": "chunk",       "text": str}
      {"type": "action_card", "alumni_id": str, "brief": str, "alumni_cards": list[dict]}
      {"type": "meta",        "brief": str, "recommended_alumni": list[dict]}
      {"type": "done"}

    Raises:
        LLMUnavailableError: khi agent.py không tìm được API key nào.
    """
    try:
        async for event in run_chat_agent(
            query=query,
            conversation_id=conversation_id,
            clarification_data=clarification_data,
            alumni_matches=alumni_matches,
            db=db,
        ):
            if isinstance(event, ActivityEvent):
                yield {
                    "type": "activity",
                    "label": event.label,
                    "status": event.status,
                    "tool": event.tool,
                }
            elif isinstance(event, ClarifyEvent):
                yield {"type": "clarify", "fields": event.fields}
            elif isinstance(event, ChunkEvent):
                yield {"type": "chunk", "text": event.text}
            elif isinstance(event, ActionCardEvent):
                # Không forward riêng — action_card được đóng gói trong MetaEvent.action_card
                # và router sẽ gửi cùng event "meta" để tránh frontend nhận 2 lần.
                pass
            elif isinstance(event, MetaEvent):
                yield {
                    "type": "meta",
                    "brief": event.brief,
                    "recommended_alumni": event.recommended_alumni,
                    "action_card": event.action_card,
                }
            elif isinstance(event, DoneEvent):
                yield {"type": "done"}
            else:
                # Phòng khi thêm ChatEvent mới ở schemas.py mà quên map ở đây —
                # log cảnh báo thay vì âm thầm nuốt mất event.
                logger.warning(f"stream_chat_answer: ChatEvent chưa được map: {event!r}")

    except RuntimeError as exc:
        # agent.py raise RuntimeError("Không có LLM API key nào...")
        raise LLMUnavailableError(str(exc)) from exc
