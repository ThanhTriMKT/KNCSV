/**
 * Mentorship request — dùng ky (tự xử lý non-2xx + auth header).
 *
 * Contract POST /api/mentorship/request ← backend/app/routers/mentorship.py:
 *   Request:  { alumni_identifier: string, brief: string, channel: "email" | "meet" }
 *   Response: { status, message, session_id, channel, meet_link, brief }
 *
 * alumni_identifier ở đây là AlumniProfile.id (UUID) mà agent trả về qua
 * ActionCardEvent — KHÔNG phải email/SĐT thật của CSV. Backend tự tra
 * AlumniProfile.email/phone thật từ id này trước khi gửi (xem
 * app/routers/mentorship.py::request_mentorship) — đúng nguyên tắc Privacy
 * Proxy, frontend không bao giờ thấy thông tin liên hệ thật.
 */

import { apiClient } from "./client";

export type MentorshipChannel = "meet" | "email";

export interface RequestMentorshipInput {
  alumniIdentifier: string;
  brief: string;
  channel: MentorshipChannel;
  conversationId?: string | null;
  messageId?: string | null;
}

export interface RequestMentorshipResult {
  status: string;
  message: string;
  session_id: string;
  channel: MentorshipChannel;
  meet_link: string | null;
  brief: string;
}

/** POST /api/mentorship/request */
export function requestMentorship(
  input: RequestMentorshipInput,
): Promise<RequestMentorshipResult> {
  return apiClient
    .post("mentorship/request", {
      json: {
        alumni_identifier: input.alumniIdentifier,
        brief: input.brief,
        channel: input.channel,
        conversation_id: input.conversationId || undefined,
        message_id: input.messageId || undefined,
      },
    })
    .json<RequestMentorshipResult>();
}

/** POST /api/mentorship/action-card/reject */
export function rejectActionCard(input: {
  conversationId: string;
  messageId?: string | null;
}): Promise<{ status: string }> {
  return apiClient
    .post("mentorship/action-card/reject", {
      json: {
        conversation_id: input.conversationId,
        message_id: input.messageId || undefined,
      },
    })
    .json<{ status: string }>();
}
