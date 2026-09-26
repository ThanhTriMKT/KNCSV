/**
 * SSE chat streaming — dùng fetch thuần (không phải apiClient/ky) vì cần
 * truy cập ReadableStream của response.body, thứ ky không expose.
 *
 * Contract POST /api/chat  ← backend/app/routers/chat.py:
 *   Request:  { query: string, conversation_id: string | null,
 *               clarification_data: Record<string, unknown> | null }
 *   SSE events: activity | clarify | chunk | action_card | meta | done
 *
 * Luồng 2 lượt (giống Claude.ai hỏi lại + Gemini compose preview):
 *   Lượt 1 — SV hỏi mơ hồ  → server bắn "clarify" kèm field list
 *          → FE render inline form (xem ConnectionActionCard/ApprovalCard)
 *   Lượt 2 — SV điền form  → FE gọi lại sendChatMessage với clarificationData
 *          → server search + bắn "action_card" (đề xuất kết nối) + "meta"
 */

import { getToken } from "@/hooks/use-auth";
import { API_URL } from "@/lib/config";

export class ChatRequestError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
    this.name = "ChatRequestError";
  }
}

export interface AlumniCard {
  id: string;
  anonymized_name: string;
  current_job: string;
  company: string;
  skills: string[];
  courses_taken: string[];
}

export interface ChatMeta {
  brief: string;
  recommended_alumni: AlumniCard[];
  conversation_id: string | null;
}

/** 1 trường trong form "clarify" — khớp app/ai/schemas.py::ClarifyEvent */
export interface ClarifyField {
  name: string;
  label: string;
  type: "text" | "select" | "multiselect" | "textarea";
  required?: boolean;
  placeholder?: string;
  options?: string[];
}

/** Payload "action_card" — khớp app/ai/schemas.py::ActionCardEvent */
export interface ActionCardPayload {
  alumniId: string;
  brief: string;
  alumniCards: AlumniCard[];
}

export interface SendChatMessageOptions {
  /** conversation_id để tiếp tục hội thoại cũ; null = tạo mới */
  conversationId?: string | null;
  /** Dữ liệu SV điền sau khi nhận event "clarify" ở lượt trước */
  clarificationData?: Record<string, unknown> | null;
  onChunk: (text: string) => void;
  onActivityItem?: (item: Record<string, unknown>) => void;
  /** AI cần thêm thông tin — render form, gọi lại sendChatMessage kèm clarificationData */
  onClarify?: (fields: ClarifyField[], conversationId?: string) => void;
  /** AI đề xuất kết nối — render card preview kèm nút gửi */
  onActionCard?: (card: ActionCardPayload) => void;
  /** Gọi 1 lần khi nhận event "meta" — chứa brief + alumni cards + conversation_id */
  onMeta?: (meta: ChatMeta) => void;
  /**
   * Backend gặp lỗi khi xử lý (timeout AI, lỗi provider...) — SSE event
   * "error" mới thêm để tránh kết nối treo vô thời hạn không rõ nguyên nhân.
   */
  onServerError?: (message: string, code?: string) => void;
  /**
   * Số mili-giây không nhận được BẤT KỲ dữ liệu nào (kể cả ping keep-alive
   * từ sse-starlette) trước khi tự abort và báo lỗi "server không phản
   * hồi". Mặc định 45s — dài hơn chu kỳ ping 15s của backend nhiều lần để
   * tránh false-positive, nhưng vẫn đủ ngắn để không để người dùng chờ vô
   * thời hạn nếu kết nối thực sự đã chết (mất mạng, proxy cắt...).
   */
  stallTimeoutMs?: number;
  signal?: AbortSignal;
}

/**
 * POST /api/chat và stream reply về qua SSE.
 * Dùng fetch thuần vì cần ReadableStream (ky không expose body stream).
 */
export async function sendChatMessage(
  text: string,
  {
    conversationId,
    clarificationData,
    onChunk,
    onActivityItem,
    onClarify,
    onActionCard,
    onMeta,
    onServerError,
    stallTimeoutMs = 45_000,
    signal,
  }: SendChatMessageOptions,
): Promise<void> {
  const token = getToken();
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      query: text,
      conversation_id: conversationId ?? null,
      clarification_data: clarificationData ?? null,
    }),
    signal,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail =
        typeof body?.detail === "string"
          ? body.detail
          : JSON.stringify(body?.detail ?? body);
    } catch {
      // không phải JSON — giữ statusText
    }
    throw new ChatRequestError(detail, response.status);
  }

  if (!response.body) {
    throw new ChatRequestError("Response had no readable body");
  }

  await parseSseStream(response.body, {
    onChunk,
    onActivityItem,
    onClarify,
    onActionCard,
    onMeta,
    onServerError,
    stallTimeoutMs,
  });
}

interface SseCallbacks {
  onChunk: (text: string) => void;
  onActivityItem?: (item: Record<string, unknown>) => void;
  onClarify?: (fields: ClarifyField[], conversationId?: string) => void;
  onActionCard?: (card: ActionCardPayload) => void;
  onMeta?: (meta: ChatMeta) => void;
  onServerError?: (message: string, code?: string) => void;
  stallTimeoutMs?: number;
}

/**
 * SSE parser tối giản: đọc stream theo record (cách nhau \n\n),
 * dispatch sang callback theo event name.
 */
async function parseSseStream(
  body: ReadableStream<Uint8Array>,
  {
    onChunk,
    onActivityItem,
    onClarify,
    onActionCard,
    onMeta,
    onServerError,
    stallTimeoutMs = 45_000,
  }: SseCallbacks,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const dispatchRecord = (record: string): boolean => {
    const trimmed = record.trim();
    if (!trimmed) return false;

    const { event, data } = parseSseRecord(record);
    if (event === "done") return true;

    if (event === "error" && data) {
      try {
        const parsed = JSON.parse(data) as { message: string; code?: string };
        onServerError?.(
          parsed.message || "Đã có lỗi xảy ra ở máy chủ.",
          parsed.code,
        );
      } catch {
        onServerError?.("Đã có lỗi xảy ra ở máy chủ.");
      }
      return true; // dừng đọc — backend đã kết thúc stream sau khi báo lỗi
    }

    if (event === "activity" && data && onActivityItem) {
      try {
        onActivityItem(JSON.parse(data) as Record<string, unknown>);
      } catch {
        /* skip bad json */
      }
    }

    if (event === "chunk" && data) onChunk(data);

    if (event === "clarify" && data && onClarify) {
      try {
        const parsed = JSON.parse(data) as {
          fields: ClarifyField[];
          conversation_id?: string;
        };
        onClarify(parsed.fields ?? [], parsed.conversation_id);
      } catch {
        /* skip bad json */
      }
    }

    if (event === "action_card" && data && onActionCard) {
      try {
        const parsed = JSON.parse(data) as {
          alumni_id: string;
          brief: string;
          alumni_cards: AlumniCard[];
        };
        onActionCard({
          alumniId: parsed.alumni_id,
          brief: parsed.brief,
          alumniCards: parsed.alumni_cards ?? [],
        });
      } catch {
        /* skip bad json */
      }
    }

    if (event === "meta" && data && onMeta) {
      try {
        onMeta(JSON.parse(data) as ChatMeta);
      } catch {
        /* skip bad json */
      }
    }

    return false;
  };

  /**
   * Đọc 1 chunk kèm "đồng hồ treo" — nếu không nhận được BẤT KỲ byte nào
   * (kể cả ping keep-alive từ backend) trong stallTimeoutMs, coi như kết
   * nối đã chết (mất mạng, proxy cắt giữa chừng...) và báo lỗi rõ ràng
   * thay vì để component chờ vô thời hạn không phản hồi gì.
   */
  const readWithStallGuard = (): Promise<
    ReadableStreamReadResult<Uint8Array>
  > => {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new ChatRequestError("STALL_TIMEOUT"));
      }, stallTimeoutMs);
      reader
        .read()
        .then((res) => {
          clearTimeout(timer);
          resolve(res);
        })
        .catch((err) => {
          clearTimeout(timer);
          reject(err);
        });
    });
  };

  try {
    while (true) {
      let done: boolean;
      let value: Uint8Array | undefined;
      try {
        ({ done, value } = await readWithStallGuard());
      } catch (err) {
        if (
          err instanceof ChatRequestError &&
          err.message === "STALL_TIMEOUT"
        ) {
          await reader.cancel().catch(() => {});
          onServerError?.(
            "Máy chủ không phản hồi trong thời gian dài. Vui lòng kiểm tra kết nối mạng và thử lại.",
            "CLIENT_STALL_TIMEOUT",
          );
          return;
        }
        throw err;
      }
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      // Hỗ trợ cả chuẩn CRLF (\r\n\r\n từ sse-starlette) lẫn LF (\n\n)
      const records = buffer.split(/\r?\n\r?\n/);
      buffer = records.pop() ?? "";

      for (const record of records) {
        const isDone = dispatchRecord(record);
        if (isDone) return;
      }
    }

    if (buffer.trim()) {
      dispatchRecord(buffer);
    }
  } finally {
    try {
      reader.releaseLock();
    } catch {
      /* đã cancel() ở trên thì releaseLock() có thể throw — bỏ qua */
    }
  }
}

function parseSseRecord(record: string): { event: string; data: string } {
  let event = "message";
  const dataLines: string[] = [];

  for (const rawLine of record.split(/\r?\n/)) {
    const line = rawLine.trimEnd();
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).replace(/^ /, ""));
    }
  }

  return { event, data: dataLines.join("\n") };
}
