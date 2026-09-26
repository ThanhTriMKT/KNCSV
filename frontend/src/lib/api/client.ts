/**
 * ky instance dùng chung cho mọi module trong lib/api/ — tự đính Bearer
 * token nếu đã đăng nhập.
 *
 * ky v2: dùng `prefix` (không phải `prefixUrl`).
 * beforeRequest hook nhận BeforeRequestState — destructure {request}.
 */

import ky from "ky";
import { getToken } from "@/hooks/use-auth";
import { API_URL } from "@/lib/config";

export const apiClient = ky.create({
  prefix: API_URL,
  hooks: {
    beforeRequest: [
      ({ request }) => {
        const token = getToken();
        if (token) request.headers.set("Authorization", `Bearer ${token}`);
      },
    ],
  },
});
