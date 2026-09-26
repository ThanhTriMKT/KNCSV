"""
File DUY NHẤT được phép import LangGraph/LangChain trong dự án.

Chịu trách nhiệm:
  - Build đúng 1 lần `create_agent` (model + tools + HITL middleware +
    checkpointer Postgres) lúc FastAPI khởi động — xem init_agent()/
    close_agent() và app/main.py::lifespan.
  - Stream câu trả lời + suy luận chọn tool sang ChatEvent (schemas.py) để
    app/services/llm_service.py tiêu thụ. llm_service.py không biết gì về
    LangGraph — chỉ nhận ChatEvent.
  - Xử lý resume sau khi bị interrupt (SV điền form còn thiếu thông tin).

KHÔNG import module này ở đâu khác ngoài app/services/llm_service.py.

LƯU Ý VỀ VERSION: dùng astream_events(version="v3") với typed projections
(stream.tool_calls, stream.messages). Hai projections được consume song song
qua asyncio.Queue để emit ChatEvent theo đúng thứ tự thời gian thực.
Nếu ClarifyEvent rỗng, in state.tasks ra log để kiểm tra Interrupt.value.
"""

import asyncio
import json
import os
import uuid
import warnings
from collections.abc import AsyncGenerator
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import MemorySaver

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
except (ImportError, Exception):
    AsyncPostgresSaver = None

from langgraph.types import Command
from loguru import logger
from sqlalchemy import select

from app.ai.schemas import (
    ActionCardEvent,
    ActivityEvent,
    ChatEvent,
    ChunkEvent,
    ClarifyEvent,
    DoneEvent,
    MetaEvent,
)
from app.ai.tools import ALL_TOOLS, INTERRUPT_TOOL_NAMES
from app.config import settings
from app.database.models import ChatMessage

SYSTEM_PROMPT = """Bạn là AI Broker kết nối Cựu sinh viên (CSV) và Sinh viên (SV).

⚠️ QUY TẮC TUYỆT ĐỐI — KHÔNG BAO GIỜ ĐƯỢC VI PHẠM:
   Khi sinh viên yêu cầu tìm kiếm cựu sinh viên mà THIẾU thông tin, TUYỆT ĐỐI KHÔNG được:
   - Tự viết câu hỏi ra dưới dạng văn bản/text.
   - Liệt kê các câu hỏi dạng bullet points trong phần trả lời.
   BẮT BUỘC phải GỌI TOOL `request_more_info_form` để hiển thị form tương tác cho sinh viên.

QUY TẮC SỬ DỤNG TOOLS:
1. Trò chuyện thông thường:
   - Nếu sinh viên chỉ chào hỏi, cảm ơn, hỏi thăm hoặc hỏi kiến thức chung mà không yêu cầu tìm kiếm cựu sinh viên:
     Trả lời tự nhiên, thân thiện bằng tiếng Việt, TUYỆT ĐỐI KHÔNG gọi bất kỳ tool nào.

2. Tìm kiếm cựu sinh viên:
   - ĐỦ THÔNG TIN: Nếu câu hỏi đã nêu rõ ngành nghề, chuyên môn, vị trí, công ty hoặc kỹ năng (ví dụ: "tìm CSV ngành Khoa học máy tính làm AI", "anh chị làm backend", "có ai làm ở Shopee ko", "tư vấn thực tập kiểm thử"):
     -> GỌI NGAY `search_alumni_pgvector`. TUYỆT ĐỐI KHÔNG gọi `request_more_info_form`.
   - THIẾU THÔNG TIN: Khi câu hỏi mơ hồ, không rõ lĩnh vực (ví dụ: "tìm cho em cựu sinh viên", "em muốn tìm mentor", "tìm cựu sinh viên"):
     -> BẮT BUỘC GỌI TOOL `request_more_info_form`. KHÔNG được tự hỏi bằng text.

3. QUY TẮC VỀ `request_more_info_form`:
   - LUÔN LUÔN cung cấp `options` cho mỗi field (type: "select" hoặc "multiselect").
     Ví dụ options lĩnh vực: ["Backend/API", "Frontend/UI", "Mobile App", "AI/Machine Learning", "DevOps/Cloud", "Bảo mật", "Data Engineer", "Game Dev", "Embedded/IoT", "Product Management"]
     Ví dụ options giai đoạn: ["Năm 1-2 (định hướng)", "Năm 3 (tìm thực tập)", "Năm 4 (chuẩn bị tốt nghiệp)", "Mới ra trường (tìm việc)"]
   - KHÔNG dùng type "text" — luôn dùng "select" hoặc "multiselect" với options cụ thể.
   - Hỏi tối đa 2-3 câu hỏi cốt lõi (ngành quan tâm, giai đoạn học, mục tiêu tư vấn).

4. Sau khi tìm kiếm bằng `search_alumni_pgvector`:
   - NẾU TÌM THẤY CSV: Trả lời bằng văn bản giới thiệu ngắn gọn các anh/chị phù hợp nhất (tên ẩn danh, chức danh/công ty, chuyên môn chính). Hỏi sinh viên xem có muốn AI hỗ trợ kết nối, xin tư vấn hoặc soạn brief gửi email / hẹn Google Meet với anh/chị nào không.
   - NẾU KHÔNG TÌM THẤY (danh sách rỗng []): Thông báo lịch sự, gợi ý thử từ khóa khác.
   - ⚠️ TUYỆT ĐỐI KHÔNG GỌI `render_connection_action_card` ở bước này! Khi chỉ đang tìm kiếm hoặc hỏi thông tin, KHÔNG ĐƯỢC tự ý mở form soạn email kết nối.

5. QUY TẮC SOẠN BRIEF & MỞ FORM GỬI EMAIL/MEET (`render_connection_action_card`):
   - CHỈ GỌI TOOL NÀY KHI: Sinh viên có yêu cầu rõ ràng muốn kết nối/soạn email/xin tư vấn (ví dụ: "soạn email giúp mình", "kết nối với anh/chị H.N.M", "gửi brief", "xin tư vấn anh H.N.M", "hẹn meet") HOẶC khi sinh viên xác nhận đồng ý kết nối sau khi được gợi ý (ví dụ: "có", "đồng ý", "kết nối giúp em nhé", "ok").
   - KHI ĐÓ: Chọn cựu sinh viên phù hợp mà sinh viên muốn kết nối, soạn brief tư vấn súc tích (mục tiêu, chủ đề, 2 câu hỏi chuẩn bị), rồi GỌI `render_connection_action_card(alumni_id=..., brief_content=...)`.
     * `alumni_id`: Truyền ID (UUID) hoặc tên ẩn danh (ví dụ "Anh/Chị L.T.H.V" hoặc "L.T.H.V") của cựu sinh viên được chọn.
     * `brief_content`: Nội dung brief tư vấn ngắn gọn, chuyên nghiệp.
   - Sinh viên chưa đồng ý hoặc chưa yêu cầu kết nối -> TUYỆT ĐỐI KHÔNG GỌI.

Luôn trả lời bằng tiếng Việt, giọng thân thiện, ngắn gọn, đi thẳng vào trọng tâm.
An toàn: KHÔNG bao giờ tự bịa hoặc tiết lộ SĐT/email/Zalo thật của CSV ngoài những gì tool cung cấp."""

_ACTIVITY_LABELS: dict[str, str] = {
    "search_alumni_pgvector": "Đang tìm cựu sinh viên phù hợp…",
    "request_more_info_form": "Đang chuẩn bị câu hỏi bổ sung…",
    "render_connection_action_card": "Đang soạn đề xuất kết nối…",
}

# Fields mặc định dùng khi LLM không gọi request_more_info_form mà tự hỏi
# bằng text (fallback để đảm bảo form luôn hiển thị).
_DEFAULT_CLARIFY_FIELDS: list[dict] = [
    {
        "name": "industry",
        "label": "Lĩnh vực bạn quan tâm?",
        "type": "multiselect",
        "required": True,
        "placeholder": "Chọn một hoặc nhiều lĩnh vực",
        "options": [
            "Backend/API",
            "Frontend/UI",
            "Mobile App",
            "AI/Machine Learning",
            "DevOps/Cloud",
            "Data Engineer",
            "Bảo mật",
            "Game Dev",
            "Embedded/IoT",
            "Product Management",
        ],
    },
    {
        "name": "stage",
        "label": "Bạn đang ở giai đoạn nào?",
        "type": "select",
        "required": True,
        "placeholder": "Chọn giai đoạn học tập",
        "options": [
            "Năm 1-2 (định hướng)",
            "Năm 3 (tìm thực tập)",
            "Năm 4 (chuẩn bị tốt nghiệp)",
            "Mới ra trường (tìm việc)",
        ],
    },
    {
        "name": "goal",
        "label": "Bạn muốn được tư vấn điều gì?",
        "type": "multiselect",
        "required": False,
        "placeholder": "Chọn mục tiêu tư vấn",
        "options": [
            "Lộ trình học tập",
            "Tìm nơi thực tập",
            "Review CV",
            "Kinh nghiệm tìm việc",
            "Định hướng nghề nghiệp",
        ],
    },
]


def _activity_label(tool_name: str) -> str:
    return _ACTIVITY_LABELS.get(tool_name, f"Đang xử lý ({tool_name})…")


# ---------------------------------------------------------------------------
# Model selection — chọn provider theo API key nào đang có trong .env.
# Ưu tiên Gemini (rẻ, nhanh) > OpenAI > Anthropic.
# ---------------------------------------------------------------------------


def _select_model() -> str:
    if settings.openrouter_api_key:
        os.environ.setdefault("OPENROUTER_API_KEY", settings.openrouter_api_key)
        return "openrouter:google/gemma-4-31b-it"
    if settings.gemini_api_key:
        os.environ.setdefault("GOOGLE_API_KEY", settings.gemini_api_key)
        return "google_genai:gemini-2.5-flash"
    if settings.openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
        return "openai:gpt-4o-mini"
    if settings.anthropic_api_key:
        os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)
        return "anthropic:claude-3-5-haiku-20241022"
    raise RuntimeError(
        "Không có LLM API key nào được cấu hình "
        "(GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY) trong backend/.env"
    )


def _psycopg_dsn() -> str:
    """AsyncPostgresSaver dùng driver psycopg (v3), không phải asyncpg.

    settings.database_url đang ở dạng "postgresql+asyncpg://..." (cho
    SQLAlchemy) — bỏ "+asyncpg" để có DSN chuẩn psycopg cho checkpointer.
    """
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://")


# ---------------------------------------------------------------------------
# Agent singleton — build 1 lần lúc FastAPI startup, dùng lại cho mọi request.
# ---------------------------------------------------------------------------

_checkpointer_cm: Any = None
_agent: Any = None


async def init_agent() -> None:
    """Gọi 1 lần lúc FastAPI startup — xem app/main.py::lifespan."""
    global _checkpointer_cm, _agent

    checkpointer = None
    if AsyncPostgresSaver is not None:
        try:
            saver_cm = AsyncPostgresSaver.from_conn_string(_psycopg_dsn())
            checkpointer = await saver_cm.__aenter__()
            await checkpointer.setup()  # tạo bảng checkpoint nếu chưa có
            _checkpointer_cm = saver_cm
            logger.info("LangGraph AsyncPostgresSaver đã kết nối thành công.")
        except Exception as e:
            logger.warning(
                f"Không thể khởi tạo AsyncPostgresSaver ({e}). "
                "Đang fallback sang MemorySaver in-memory."
            )
            checkpointer = None

    if checkpointer is None:
        checkpointer = MemorySaver()
        logger.info("Sử dụng MemorySaver in-memory cho AI agent.")

    _agent = create_agent(
        model=_select_model(),
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    name: {"allowed_decisions": ["respond", "reject"]}
                    for name in INTERRUPT_TOOL_NAMES
                },
                description_prefix="Cần thông tin bổ sung từ sinh viên",
            ),
        ],
        checkpointer=checkpointer,
    )
    logger.info("AI agent (create_agent) đã sẵn sàng.")


async def close_agent() -> None:
    """Gọi lúc FastAPI shutdown — đóng connection pool Postgres."""
    global _checkpointer_cm, _agent
    if _checkpointer_cm is not None:
        await _checkpointer_cm.__aexit__(None, None, None)
    _checkpointer_cm = None
    _agent = None


# ---------------------------------------------------------------------------
# Đọc dữ liệu interrupt / state cuối — tách riêng vì đây là phần dễ vỡ nhất
# khi langchain đổi version (xem docstring đầu file).
# ---------------------------------------------------------------------------


def _extract_clarify_fields(state: Any) -> list[dict]:
    """Đọc HITLRequest từ interrupt hiện tại để build field list cho ClarifyEvent.

    Cấu trúc kỳ vọng (Interrupt.value là 1 HITLRequest):
        {"action_requests": [{"name": "request_more_info_form",
                               "arguments": {"reason": ..., "field_configs": "[...]"}}],
         "review_configs": [...]}
    """
    try:
        interrupt = state.tasks[0].interrupts[0]
        value = interrupt.value
        action_requests = value.get("action_requests") or value.get("actionRequests") or []
        if not action_requests:
            return []
        args = action_requests[0].get("arguments") or action_requests[0].get("args") or {}
        raw_configs = args.get("field_configs", "[]")
        fields = json.loads(raw_configs) if isinstance(raw_configs, str) else raw_configs
        return fields or []
    except (IndexError, AttributeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        logger.error(
            f"Không đọc được interrupt request: {exc} | state.tasks={getattr(state, 'tasks', None)}"
        )
        return []


# ---------------------------------------------------------------------------
# Entry point chính — llm_service.py gọi hàm này.
# ---------------------------------------------------------------------------


async def run_chat_agent(
    query: str,
    conversation_id: str | None,
    clarification_data: dict | None,
    alumni_matches: list[dict],  # reserved — không dùng, agent tự search
    db: Any = None,  # AsyncSession được inject từ chat.py, tránh tạo session riêng trong hot path
) -> AsyncGenerator[ChatEvent, None]:
    if _agent is None:
        raise RuntimeError("AI agent chưa được khởi tạo — kiểm tra app/main.py::lifespan.")

    thread_id = conversation_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    state = await _agent.aget_state(config)
    is_resuming = bool(state.next) and clarification_data is not None

    # Detect sơ bộ intent tìm kiếm CSV — dùng để quyết định có fallback
    # ClarifyEvent hay không khi LLM không gọi tool (xem cuối hàm).
    _SEARCH_KEYWORDS = (
        "tìm",
        "kiếm",
        "cựu sinh viên",
        "csv",
        "mentor",
        "anh chị",
        "giới thiệu",
        "kết nối",
        "tư vấn",
    )
    has_search_intent = any(kw in query.lower() for kw in _SEARCH_KEYWORDS)

    if is_resuming:
        run_input: Any = Command(
            resume={
                "decisions": [
                    {
                        "type": "respond",
                        "message": json.dumps(clarification_data, ensure_ascii=False),
                    }
                ]
            }
        )
    elif clarification_data and not state.next:
        # Edge case: clarification_data được gửi nhưng state.next=False
        # (agent không còn ở trạng thái interrupt — có thể do timeout hoặc restart).
        # Inject context vào query để không mất thông tin SV đã điền.
        logger.warning(
            "[agent] clarification_data có nhưng state.next=False "
            f"(thread_id={thread_id}). Inject vào query thay vì Command(resume=...)."
        )
        clarify_context = json.dumps(clarification_data, ensure_ascii=False)
        run_input = {
            "messages": [
                {
                    "role": "user",
                    "content": f"{query}\n\n[Thông tin bổ sung: {clarify_context}]",
                }
            ]
        }
    else:
        run_input = {"messages": [{"role": "user", "content": query}]}

    # Mutable container dùng chung giữa 2 consumer tasks
    search_results: list[dict] = []
    tool_calls_made: set[str] = set()  # track tên tool đã gọi trong lượt này
    action_card_payload_holder: list[dict] = []

    # Queue để merge stream.tool_calls và stream.messages thành 1 chuỗi sự kiện
    queue: asyncio.Queue[ChatEvent | BaseException | None] = asyncio.Queue()

    warnings.filterwarnings("ignore", message=".*v3 streaming protocol.*")
    stream = await _agent.astream_events(run_input, config, version="v3")

    async def _consume_tools() -> None:
        """Consume stream.tool_calls — emit ActivityEvent + ActionCardEvent."""
        try:
            call_count = 0
            async for call in stream.tool_calls:
                call_count += 1
                tool_name = call.tool_name
                tool_calls_made.add(tool_name)
                logger.info(f"[agent] tool #{call_count} bắt đầu: {tool_name}")

                # Bắt đầu tool → working
                await queue.put(
                    ActivityEvent(
                        label=_activity_label(tool_name), status="working", tool=tool_name
                    )
                )

                # Drain output_deltas để call.output có giá trị khi vòng lặp kết thúc
                async for _ in call.output_deltas:
                    pass

                logger.info(f"[agent] tool #{call_count} hoàn thành: {tool_name}")

                # Kết thúc tool → complete
                await queue.put(
                    ActivityEvent(
                        label=_activity_label(tool_name), status="complete", tool=tool_name
                    )
                )

                if tool_name == "search_alumni_pgvector":
                    raw = call.output
                    try:
                        search_results[:] = json.loads(raw) if isinstance(raw, str) else (raw or [])
                    except (json.JSONDecodeError, TypeError):
                        search_results.clear()

                elif tool_name == "render_connection_action_card":
                    args: dict = call.input or {}
                    raw_alumni_id = str(args.get("alumni_id") or "").strip()
                    brief_content = str(args.get("brief_content") or "").strip()

                    matched_cards: list[dict] = []

                    # 1. Nếu có search_results từ tool search trong cùng lượt
                    if search_results:
                        if raw_alumni_id:
                            matched_cards = [
                                c
                                for c in search_results
                                if c.get("id") == raw_alumni_id
                                or raw_alumni_id.lower() in (c.get("anonymized_name") or "").lower()
                                or (c.get("anonymized_name") or "").lower() in raw_alumni_id.lower()
                            ]
                        if not matched_cards:
                            matched_cards = [search_results[0]]

                    # 2. Nếu search_results rỗng (do tìm ở lượt trước), tra cứu trong DB
                    if not matched_cards:
                        try:
                            from app.services.rag_service import find_alumni_card

                            # Ưu tiên dùng db session được inject từ chat.py;
                            # fallback tạo session mới nếu gọi từ context không có db.
                            # Truyền raw_alumni_id như tham số (không capture qua closure
                            # trong loop) để tránh lỗi B023 late-binding.
                            async def _lookup_with_db(session: Any, target_id: str) -> None:
                                nonlocal matched_cards
                                # 2a. Tra cứu theo target_id (UUID, student_id, tên ẩn danh)
                                if target_id:
                                    found = await find_alumni_card(session, target_id)
                                    if found:
                                        matched_cards = [found]

                                # 2b. Nếu vẫn chưa có và có conversation_id, lấy từ lịch sử chat gần nhất
                                if not matched_cards and conversation_id:
                                    try:
                                        conv_uuid = uuid.UUID(conversation_id)
                                        res = await session.execute(
                                            select(ChatMessage)
                                            .where(
                                                ChatMessage.conversation_id == conv_uuid,
                                                ChatMessage.role == "assistant",
                                            )
                                            .order_by(ChatMessage.created_at.desc())
                                            .limit(5)
                                        )
                                        past_msgs = res.scalars().all()
                                        for pm in past_msgs:
                                            if not pm.meta or not isinstance(pm.meta, dict):
                                                continue
                                            recs = pm.meta.get("recommended_alumni") or []
                                            if isinstance(recs, list) and recs:
                                                if target_id:
                                                    for r in recs:
                                                        if (
                                                            r.get("id") == target_id
                                                            or target_id.lower()
                                                            in (
                                                                r.get("anonymized_name") or ""
                                                            ).lower()
                                                            or (
                                                                r.get("anonymized_name") or ""
                                                            ).lower()
                                                            in target_id.lower()
                                                        ):
                                                            matched_cards = [r]
                                                            break
                                                if not matched_cards:
                                                    matched_cards = [recs[0]]
                                                if matched_cards:
                                                    break
                                    except Exception as hist_err:
                                        logger.warning(
                                            f"[agent] Tra cứu lịch sử hội thoại lỗi: {hist_err}"
                                        )

                            if db is not None:
                                await _lookup_with_db(db, raw_alumni_id)
                            else:
                                from app.database.session import async_session_factory

                                async with async_session_factory() as fallback_db:
                                    await _lookup_with_db(fallback_db, raw_alumni_id)

                        except Exception as db_err:
                            logger.error(f"[agent] Tra cứu alumni profile từ DB lỗi: {db_err}")

                    # 3. Fallback tối thiểu nếu không tìm thấy profile nhưng có thông tin
                    if not matched_cards and raw_alumni_id:
                        matched_cards = [
                            {
                                "id": raw_alumni_id,
                                "anonymized_name": (
                                    raw_alumni_id
                                    if "Anh/Chị" in raw_alumni_id
                                    else f"Anh/Chị {raw_alumni_id}"
                                ),
                                "current_job": "Cựu sinh viên",
                                "company": "",
                                "skills": [],
                            }
                        ]

                    final_id = matched_cards[0].get("id", "") if matched_cards else raw_alumni_id

                    if final_id or brief_content:
                        card_data = {
                            "alumni_id": final_id,
                            "brief": brief_content,
                            "alumni_cards": matched_cards,
                            "status": "pending",
                        }
                        action_card_payload_holder.append(card_data)
                        await queue.put(
                            ActionCardEvent(
                                alumni_id=final_id,
                                brief=brief_content,
                                alumni_cards=matched_cards,
                            )
                        )
                    else:
                        logger.warning(
                            "[agent] Bỏ qua render_connection_action_card do thiếu cả target_id và brief."
                        )

            logger.info(f"[agent] stream.tool_calls kết thúc — tổng {call_count} tool(s)")

        except Exception as exc:
            logger.error(f"[agent] _consume_tools lỗi: {exc}")
            await queue.put(exc)
        finally:
            await queue.put(None)  # sentinel

    async def _consume_messages() -> None:
        """Consume stream.messages — emit ChunkEvent cho mỗi text delta."""
        try:
            async for message in stream.messages:
                async for delta in message.text:
                    if delta:
                        await queue.put(
                            ChunkEvent(text=delta if isinstance(delta, str) else str(delta))
                        )
        except Exception as exc:
            await queue.put(exc)
        finally:
            await queue.put(None)  # sentinel

    t1 = asyncio.create_task(_consume_tools())
    t2 = asyncio.create_task(_consume_messages())

    # Yield từ queue cho đến khi cả 2 consumer báo xong (2 sentinel None)
    sentinels = 0
    try:
        while sentinels < 2:
            item = await queue.get()
            if item is None:
                sentinels += 1
            elif isinstance(item, BaseException):
                raise item
            else:
                yield item
    finally:
        t1.cancel()
        t2.cancel()
        await asyncio.gather(t1, t2, return_exceptions=True)

    # Stream đã dừng — kiểm tra vì sao: hết việc (xong) hay đang chờ SV (interrupt)?
    final_state = await _agent.aget_state(config)

    if final_state.next:
        # Còn node chưa chạy ⇒ agent đang bị chặn ở request_more_info_form,
        # chờ SV điền form rồi gửi lại clarification_data ở lượt sau.
        extracted = _extract_clarify_fields(final_state)
        yield ClarifyEvent(fields=extracted or _DEFAULT_CLARIFY_FIELDS)
        return

    # Fallback: nếu LLM không gọi tool nào (tool_calls_made rỗng) sau khi
    # stream xong bình thường → LLM đã tự hỏi bằng text thay vì gọi
    # request_more_info_form. Emit ClarifyEvent với default fields để đảm bảo
    # form luôn hiển thị thay vì text plain.
    if not tool_calls_made and not is_resuming and has_search_intent:
        logger.warning(
            "[agent] LLM không gọi tool nào — fallback emit ClarifyEvent với default fields."
        )
        yield ClarifyEvent(fields=_DEFAULT_CLARIFY_FIELDS)
        return

    action_card_obj = action_card_payload_holder[0] if action_card_payload_holder else None
    yield MetaEvent(
        brief=action_card_obj.get("brief", "") if action_card_obj else "",
        recommended_alumni=search_results,
        action_card=action_card_obj,
    )
    yield DoneEvent()
