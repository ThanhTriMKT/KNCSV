/**
 * Cấu hình chung cho frontend — import từ đây thay vì hardcode.
 *
 * Biến môi trường: NEXT_PUBLIC_API_URL trong .env.local
 * Mặc định: http://localhost:8000
 *
 * Backend mount tất cả API dưới prefix /api (trừ /mcp và webhooks).
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** URL gốc của backend, không có trailing slash */
export const API_BASE = BASE_URL;

/** URL gốc của REST API (có prefix /api) */
export const API_URL = `${BASE_URL}/api`;
