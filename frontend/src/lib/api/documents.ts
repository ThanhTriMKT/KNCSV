/**
 * Knowledge documents (PDF) — upload, danh sách, truy xuất (search), xoá.
 * Admin Document Pipeline: preview + confirm (SPEC §4 Module 1).
 *
 * Contract ← backend/app/routers/documents.py:
 *   POST   /api/documents/upload           (multipart, field "file")  -> KnowledgeDocument
 *   POST   /api/documents/preview          (multipart, field "file", ?doc_type) -> PreviewItem[]
 *   POST   /api/documents/confirm          (JSON body { items })       -> ConfirmResult
 *   GET    /api/documents                                              -> KnowledgeDocument[]
 *   GET    /api/documents/search?q=&limit=                            -> DocumentChunkResult[]
 *   DELETE /api/documents/:id                                         -> { status, document_id }
 */

import { getToken } from "@/hooks/use-auth";
import { API_URL } from "@/lib/config";
import { apiClient } from "./client";

export type DocumentStatus = "PROCESSING" | "READY" | "FAILED";
export type DocumentType =
  | "grade_sheet"
  | "internship_list"
  | "course_enrollment"
  | "general";

export interface KnowledgeDocument {
  id: string;
  filename: string;
  title: string;
  status: DocumentStatus;
  char_count: number;
  chunk_count: number;
  error: string | null;
  created_at: string;
}

export interface DocumentChunkResult {
  document_id: string;
  document_title: string;
  chunk_index: number;
  content: string;
}

/** Một record trong kết quả preview — thông tin 1 sinh viên trích xuất từ PDF. */
export interface PreviewRecord {
  student_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  extra: Record<string, unknown>;
}

/** Một item trong danh sách preview do backend trả về. */
export interface PreviewItem {
  status: "new" | "update";
  record: PreviewRecord;
  /** Chỉ có khi status="update" và có thay đổi thực — map field -> {old, new} */
  diff: Record<string, { old: unknown; new: unknown }> | null;
}

export interface ConfirmResult {
  created: number;
  updated: number;
  skipped: number;
  skip_reasons: string[];
}

/**
 * POST /api/documents/upload — tải lên 1 file PDF, trích xuất + chia chunk
 * + sinh embedding ở backend. Trả về ngay record document (có thể là
 * status "FAILED" nếu PDF không có text trích xuất được — kiểm tra field
 * `status`/`error` thay vì chỉ dựa vào việc promise resolve thành công).
 */
export function uploadDocument(file: File): Promise<KnowledgeDocument> {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient
    .post("documents/upload", { body: formData })
    .json<KnowledgeDocument>();
}

/** GET /api/documents — danh sách tài liệu đã tải lên, mới nhất lên đầu */
export function listDocuments(): Promise<KnowledgeDocument[]> {
  return apiClient.get("documents").json<KnowledgeDocument[]>();
}

/** GET /api/documents/search — truy xuất (semantic search) đoạn tài liệu liên quan tới `query` */
export function searchDocuments(
  query: string,
  limit = 5,
): Promise<DocumentChunkResult[]> {
  return apiClient
    .get("documents/search", { searchParams: { q: query, limit } })
    .json<DocumentChunkResult[]>();
}

/** DELETE /api/documents/:id */
export function deleteDocument(
  id: string,
): Promise<{ status: string; document_id: string }> {
  return apiClient
    .delete(`documents/${id}`)
    .json<{ status: string; document_id: string }>();
}

/**
 * POST /api/documents/preview — [Admin only]
 * Upload PDF tài liệu trường, AI trích xuất danh sách sinh viên.
 * KHÔNG lưu DB — trả về preview list để Admin xem trước.
 */
export async function previewStudentDocument(
  file: File,
  docType: DocumentType = "general",
): Promise<PreviewItem[]> {
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/documents/preview?doc_type=${docType}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      typeof body?.detail === "string" ? body.detail : `HTTP ${res.status}`,
    );
  }
  return res.json() as Promise<PreviewItem[]>;
}

/**
 * POST /api/documents/confirm — [Admin only]
 * Xác nhận import danh sách records đã review vào DB (upsert alumni_profiles).
 */
export async function confirmStudentDocument(
  items: PreviewRecord[],
): Promise<ConfirmResult> {
  const token = getToken();
  const res = await fetch(`${API_URL}/documents/confirm`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ items }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      typeof body?.detail === "string" ? body.detail : `HTTP ${res.status}`,
    );
  }
  return res.json() as Promise<ConfirmResult>;
}
