/**
 * Conversations CRUD — dùng ky (tự xử lý non-2xx + auth header).
 */

import type { AlumniCard } from "./chat";
import { apiClient } from "./client";

export interface ConversationSummary {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageOut {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta: { brief?: string; recommended_alumni?: AlumniCard[] } | null;
  created_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: ChatMessageOut[];
}

/** GET /api/conversations — danh sách hội thoại, mới nhất lên đầu */
export function listConversations(): Promise<ConversationSummary[]> {
  return apiClient.get("conversations").json<ConversationSummary[]>();
}

/** GET /api/conversations/:id — chi tiết kèm messages */
export function getConversation(id: string): Promise<ConversationDetail> {
  return apiClient.get(`conversations/${id}`).json<ConversationDetail>();
}

/** DELETE /api/conversations/:id */
export function deleteConversation(id: string): Promise<{ status: string }> {
  return apiClient.delete(`conversations/${id}`).json<{ status: string }>();
}

/** PATCH /api/conversations/:id — đổi tên, body JSON */
export function renameConversation(
  id: string,
  title: string,
): Promise<{ status: string; title: string }> {
  return apiClient
    .patch(`conversations/${id}`, { json: { title } })
    .json<{ status: string; title: string }>();
}
