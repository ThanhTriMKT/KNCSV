"""
AI Chat RAG & Streaming Endpoint.

Contract (khớp với frontend/src/lib/api.ts):
  Request:  POST /api/chat  {
    "query": "<câu hỏi của SV>",
    "conversation_id": "<uuid|null>",
    "clarification_data": {"field_name": "value", ...} | null
  }

  Response: SSE stream với các event:
    - "activity": { "label": str, "status": "working"|"complete" }
    - "clarify":  { "fields": [{"name", "label", "type", "required",
                                "placeholder", "options"?}] }
    - "chunk":    "<đoạn text>"
    - "meta":     { "brief": str, "recommended_alumni": [...],
                     "conversation_id": str | null }
    - "done":     { "status": "complete" }

Luồng 2 lượt:
  Lượt 1 — SV gửi query mơ hồ:
    → server stream "clarify" event với form fields
    → frontend render inline form (giống Claude.ai)

  Lượt 2 — SV điền form và gửi lại:
    → server tìm kiếm pgvector + stream câu trả lời + meta card
    → frontend hiển thị email-preview card (giống Gemini compose)

Lịch sử hội thoại: nếu SV đã đăng nhập, mỗi lượt chat được lưu vào
chat_conversations/chat_messages. Nếu chưa đăng nhập, chat vẫn hoạt động
nhưng KHÔNG được lưu lại.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from sse_starlette.sse import EventSourceResponse

from app.ai.agent import _DEFAULT_CLARIFY_FIELDS
from app.database.models import ChatConversation, ChatMessage, User
from app.database.session import get_session
from app.services.auth_service import current_active_user_optional
from app.services.llm_service import LLMUnavailableError, stream_chat_answer

router = APIRouter(prefix="/chat", tags=["AI Chat"])

# Giới hạn tổng thời gian xử lý 1 lượt chat (bao gồm mọi tool call + LLM
# round-trip của LangGraph agent). Nếu vượt quá, dừng lại và báo lỗi rõ
# ràng cho người dùng thay vì để kết nối treo vô thời hạn — đây chính là
# nguyên nhân gây lỗi "không truy cập được server sau khi chờ quá lâu".
_AGENT_TIMEOUT_SECONDS = 90


class ChatRequest(BaseModel):
    query: str
    # None → tạo hội thoại mới (nếu đã đăng nhập); có giá trị → tiếp tục.
    conversation_id: uuid.UUID | None = None
    # Form data SV điền sau khi nhận clarify event (lượt 2).
    clarification_data: dict | None = None


async def _get_or_create_conversation(
    db: AsyncSession, user: User, conversation_id: uuid.UUID | None, query: str
) -> ChatConversation:
    if conversation_id is not None:
        stmt = select(ChatConversation).where(
            ChatConversation.id == conversation_id, ChatConversation.user_id == user.id
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại.")
        return conversation

    conversation = ChatConversation(user_id=user.id, title=query.strip()[:80])
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.post("")
async def chat_stream(
    req: ChatRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(current_active_user_optional),
):
    """Process Student's query with LangGraph agent and stream response via SSE."""
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    conversation: ChatConversation | None = None
    if current_user is not None:
        conversation = await _get_or_create_conversation(
            db, current_user, req.conversation_id, query
        )
        # Nếu SV đang gửi form trả lời (clarification_data):
        # Cập nhật message clarify trước đó trong conversation:
        # clarify_pending = False, clarify_status = "answered", lưu answers = req.clarification_data
        if req.clarification_data:
            stmt_prev = (
                select(ChatMessage)
                .where(
                    ChatMessage.conversation_id == conversation.id,
                    ChatMessage.role == "assistant",
                )
                .order_by(ChatMessage.created_at.desc())
            )
            res_prev = await db.execute(stmt_prev)
            for prev_msg in res_prev.scalars().all():
                if (
                    prev_msg.meta
                    and (
                        prev_msg.meta.get("clarify_pending") or prev_msg.meta.get("clarify_fields")
                    )
                    and prev_msg.meta.get("clarify_status") != "answered"
                ):
                    meta_copy = dict(prev_msg.meta)
                    meta_copy["clarify_pending"] = False
                    meta_copy["clarify_status"] = "answered"
                    meta_copy["answers"] = req.clarification_data
                    prev_msg.meta = meta_copy
                    flag_modified(prev_msg, "meta")
                    break

        user_meta = (
            {"clarification_data": req.clarification_data} if req.clarification_data else None
        )
        db.add(
            ChatMessage(conversation_id=conversation.id, role="user", content=query, meta=user_meta)
        )
        await db.commit()

    conversation_id_str = str(conversation.id) if conversation else None

    async def event_generator() -> AsyncGenerator[dict, None]:
        full_answer_parts: list[str] = []
        activity_items: list[dict] = []
        action_card_payload: dict | None = None
        got_chunk = False
        got_clarify = False
        got_error = False
        meta_payload: dict | None = None
        clarify_fields: list | None = None  # lưu để persist vào DB

        # Emit initial activity event so SSE connection sends visual feedback immediately
        yield {
            "event": "activity",
            "data": json.dumps(
                {
                    "id": "agent_init",
                    "label": "Đang kết nối AI và phân tích câu hỏi…",
                    "status": "working",
                },
                ensure_ascii=False,
            ),
        }

        try:
            async with asyncio.timeout(_AGENT_TIMEOUT_SECONDS):
                async for event in stream_chat_answer(
                    query=query,
                    alumni_matches=[],  # agent tự search trong search_node
                    conversation_id=conversation_id_str,
                    clarification_data=req.clarification_data,
                    db=db,
                ):
                    etype = event.get("type")

                    if etype == "activity":
                        status = event.get("status", "")
                        act_item = {
                            "id": event.get("tool") or event.get("label"),
                            "label": event.get("label", ""),
                            "status": status,
                            "tool": event.get("tool"),
                        }
                        # Stream cả "working" và "complete" để client thấy real-time.
                        # Chỉ lưu event "complete" vào DB — lưu cả hai gây duplicate
                        # khi load lại conversation.
                        yield {
                            "event": "activity",
                            "data": json.dumps(act_item, ensure_ascii=False),
                        }
                        if status == "complete":
                            # Upsert theo tool id để tránh duplicate
                            existing = next(
                                (
                                    i
                                    for i, a in enumerate(activity_items)
                                    if a.get("id") == act_item["id"]
                                ),
                                -1,
                            )
                            if existing >= 0:
                                activity_items[existing] = act_item
                            else:
                                activity_items.append(act_item)

                    elif etype == "clarify":
                        got_clarify = True
                        clarify_fields = event["fields"]  # capture để lưu DB
                        yield {
                            "event": "clarify",
                            "data": json.dumps(
                                {
                                    "fields": clarify_fields,
                                    "conversation_id": conversation_id_str,
                                }
                            ),
                        }

                    elif etype == "chunk":
                        got_chunk = True
                        full_answer_parts.append(event["text"])
                        yield {"event": "chunk", "data": event["text"]}

                    elif etype == "action_card":
                        # Chỉ capture payload — KHÔNG emit SSE riêng.
                        # action_card sẽ được gửi cùng event "meta" ở cuối
                        # để frontend không nhận 2 lần (onActionCard + onMeta).
                        action_card_payload = {
                            "alumni_id": event.get("alumni_id", ""),
                            "brief": event.get("brief", ""),
                            "alumni_cards": event.get("alumni_cards", []),
                            "status": "pending",
                        }

                    elif etype == "meta":
                        act_card = event.get("action_card") or action_card_payload
                        meta_payload = {
                            "brief": event.get("brief", ""),
                            "recommended_alumni": event.get("recommended_alumni", []),
                            "conversation_id": conversation_id_str,
                            "activities": activity_items,
                            "action_card": act_card,
                        }

                    # "done" được emit bên dưới sau khi lưu DB

        except LLMUnavailableError:
            # Không có LLM key → fallback template
            pass

        except TimeoutError:
            # Vượt quá _AGENT_TIMEOUT_SECONDS — AI/tool call phản hồi quá
            # chậm (OpenRouter/Gemini chậm, mạng chập chờn...). Báo lỗi rõ
            # ràng cho người dùng thay vì để kết nối treo vô thời hạn.
            logger.error(
                f"[chat] Agent timeout sau {_AGENT_TIMEOUT_SECONDS}s cho query: {query[:80]!r}"
            )
            got_error = True
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "message": (
                            "AI phản hồi quá lâu (vượt quá "
                            f"{_AGENT_TIMEOUT_SECONDS}s). Vui lòng thử lại "
                            "hoặc đặt câu hỏi ngắn gọn hơn."
                        ),
                        "code": "AGENT_TIMEOUT",
                    },
                    ensure_ascii=False,
                ),
            }

        except Exception as exc:
            # Bắt mọi lỗi khác (network error, LLM provider lỗi, tool
            # exception chưa lường trước...) — KHÔNG để exception rơi ra
            # ngoài async generator, vì SSE không gửi được status code
            # sau khi đã bắt đầu stream, khiến client chỉ thấy kết nối bị
            # đóng đột ngột ("không truy cập được server").
            logger.error(f"[chat] Lỗi không lường trước khi chạy agent: {exc}")
            got_error = True
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "message": "Đã có lỗi xảy ra khi xử lý câu hỏi. Vui lòng thử lại.",
                        "code": "AGENT_ERROR",
                    },
                    ensure_ascii=False,
                ),
            }

        # Đồng bộ activities vào meta_payload trước khi lưu DB.
        if meta_payload is None and activity_items:
            meta_payload = {
                "brief": "",
                "recommended_alumni": [],
                "conversation_id": conversation_id_str,
                "activities": activity_items,
                "action_card": action_card_payload,
            }
        elif meta_payload is not None:
            meta_payload["activities"] = activity_items
            if action_card_payload and not meta_payload.get("action_card"):
                meta_payload["action_card"] = action_card_payload

        # Fallback nếu không có chunk nào (và không phải clarify/lỗi thật —
        # lỗi thật đã có event "error" riêng, không nên chồng thêm thông
        # báo fallback "chưa cấu hình API key" gây hiểu nhầm nguyên nhân)
        if not got_chunk and not got_clarify and not got_error:
            fallback = (
                f"Dựa trên câu hỏi '{query}', tôi chưa tìm được câu trả lời chính xác. "
                "Vui lòng cấu hình LLM API key (GEMINI_API_KEY / OPENAI_API_KEY) trong backend/.env "
                "để kích hoạt AI Agent."
            )
            full_answer_parts.append(fallback)
            yield {"event": "chunk", "data": fallback}

        # Lưu DB — normal assistant message (không phải clarify)
        if conversation is not None and not got_clarify and full_answer_parts:
            full_answer = "".join(full_answer_parts)
            db.add(
                ChatMessage(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_answer,
                    meta=meta_payload,
                )
            )
            conversation.updated_at = datetime.now(UTC)
            await db.commit()

        # Lưu DB — clarify message: lưu để restore form khi load lại trang.
        # content rỗng vì chưa có câu trả lời, meta chứa fields + clarify_pending + clarify_status
        # để frontend biết cần render form thay vì bubble text thông thường.
        if conversation is not None and got_clarify:
            saved_fields = (
                clarify_fields
                if (clarify_fields and len(clarify_fields) > 0)
                else _DEFAULT_CLARIFY_FIELDS
            )
            db.add(
                ChatMessage(
                    conversation_id=conversation.id,
                    role="assistant",
                    content="",
                    meta={
                        "clarify_fields": saved_fields,
                        "clarify_pending": True,
                        "clarify_status": "pending",
                        "activities": activity_items,
                    },
                )
            )
            conversation.updated_at = datetime.now(UTC)
            await db.commit()

        # Emit meta (khi có conversation_id hoặc meta_payload để frontend sync activeCid)
        if conversation_id_str:
            sync_meta = meta_payload or {
                "brief": "",
                "recommended_alumni": [],
                "conversation_id": conversation_id_str,
                "activities": activity_items,
                "action_card": action_card_payload,
            }
            if not sync_meta.get("conversation_id"):
                sync_meta["conversation_id"] = conversation_id_str
            yield {"event": "meta", "data": json.dumps(sync_meta, ensure_ascii=False)}

        yield {"event": "done", "data": json.dumps({"status": "complete"})}

    # ping=15: gửi comment giữ-kết-nối mỗi 15s trong lúc chờ agent xử lý —
    # tránh proxy/trình duyệt coi kết nối "chết" khi AI mất nhiều thời gian
    # suy luận (nhiều tool call liên tiếp) mà chưa có chunk text nào để gửi.
    return EventSourceResponse(event_generator(), ping=15)
