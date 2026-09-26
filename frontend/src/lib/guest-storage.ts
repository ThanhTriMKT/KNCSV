/**
 * Guest conversations storage — lưu trữ lịch sử chat cục bộ cho người dùng chưa đăng nhập.
 * Cho phép tạo nhiều cuộc hội thoại mới, xem lại lịch sử cũ và tìm kiếm mà không bị mất.
 */

export interface GuestMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta?: Record<string, unknown> | null;
  created_at: string;
}

export interface GuestConversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: GuestMessage[];
}

const STORAGE_KEY = "alumni_guest_conversations_v1";

function getStorage(): GuestConversation[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

function setStorage(items: GuestConversation[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch (e) {
    console.error("Failed to save guest conversations to localStorage", e);
  }
}

export function getGuestConversations() {
  const items = getStorage();
  return items.map((c) => ({
    id: c.id,
    title: c.title,
    created_at: c.created_at,
    updated_at: c.updated_at,
  }));
}

export function getGuestConversationDetail(
  id: string,
): GuestConversation | null {
  const items = getStorage();
  return items.find((c) => c.id === id) ?? null;
}

export function saveGuestConversationMessage(
  conversationId: string,
  message: {
    id: string;
    role: "user" | "assistant";
    content: string;
    meta?: Record<string, unknown> | null;
  },
): GuestConversation {
  const items = getStorage();
  let conv = items.find((c) => c.id === conversationId);
  const now = new Date().toISOString();

  const msgObj: GuestMessage = {
    id: message.id,
    role: message.role,
    content: message.content,
    meta: message.meta ?? null,
    created_at: now,
  };

  if (!conv) {
    // Generate title from first user query
    const title =
      message.role === "user"
        ? message.content.slice(0, 45) +
          (message.content.length > 45 ? "…" : "")
        : "Hội thoại mới";

    conv = {
      id: conversationId,
      title,
      created_at: now,
      updated_at: now,
      messages: [msgObj],
    };
    items.unshift(conv);
  } else {
    // Cập nhật messages
    const existingIdx = conv.messages.findIndex((m) => m.id === message.id);
    if (existingIdx >= 0) {
      conv.messages[existingIdx] = msgObj;
    } else {
      conv.messages.push(msgObj);
    }
    conv.updated_at = now;
    // Nếu chưa có title có nghĩa mà có user message
    if (conv.title === "Hội thoại mới" && message.role === "user") {
      conv.title =
        message.content.slice(0, 45) + (message.content.length > 45 ? "…" : "");
    }
    // Đưa lên đầu danh sách
    const idx = items.findIndex((c) => c.id === conversationId);
    if (idx > 0) {
      items.splice(idx, 1);
      items.unshift(conv);
    }
  }

  setStorage(items);
  return conv;
}

export function deleteGuestConversation(id: string): void {
  const items = getStorage().filter((c) => c.id !== id);
  setStorage(items);
}
