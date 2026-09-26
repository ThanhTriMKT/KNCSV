/**
 * Thin client cho Alumni backend — chia theo domain:
 *   client.ts            ky instance dùng chung (auth header)
 *   alumni.ts            CRUD hồ sơ cựu sinh viên
 *   jobs.ts              Tuyển dụng & thực tập
 *   events.ts            Sự kiện & talkshow
 *   surveys.ts           Khảo sát việc làm
 *   financial-aid.ts     Quỹ học bổng & hỗ trợ tài chính
 *   career-advisor.ts    Trợ lý hướng nghiệp DLU
 *
 * File này chỉ re-export — mọi import hiện có dạng
 * `from "@/lib/api"` tiếp tục hoạt động không cần sửa.
 */

export * from "./alumni";
export * from "./career-advisor";
export * from "./client";
export * from "./events";
export * from "./financial-aid";
export * from "./jobs";
export * from "./surveys";
