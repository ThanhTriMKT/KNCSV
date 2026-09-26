/**
 * useAuth — Quản lý trạng thái đăng nhập, đăng ký, quên mật khẩu, cập nhật tài khoản.
 *
 * Endpoints (fastapi-users):
 *   POST  /api/auth/jwt/login        { username: email, password } → { access_token }
 *   POST  /api/auth/jwt/logout       (bearer)
 *   POST  /api/auth/register         { email, password, role, full_name?, phone?, zalo_id? } → UserRead
 *   POST  /api/auth/forgot-password  { email }
 *   POST  /api/auth/reset-password   { token, password }
 *   GET   /api/users/me              (bearer) → UserRead
 *   PATCH /api/users/me              (bearer, body) → UserRead
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_URL } from "@/lib/config";

// ---------------------------------------------------------------------------
// Types — Giữ khớp với backend auth_schemas.py
// ---------------------------------------------------------------------------

export type UserRole = "student" | "alumni" | "admin";

export interface UserRead {
  id: string;
  email: string;
  role: UserRole;
  full_name: string | null;
  student_id: string | null;
  graduation_year: number | null;
  major: string | null;
  phone: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  role: "student" | "alumni";
  full_name?: string;
  student_id?: string;
  graduation_year?: number;
  major?: string;
}

export interface UpdateProfileInput {
  full_name?: string;
  phone?: string;
  graduation_year?: number;
  major?: string;
}

export interface ForgotPasswordInput {
  email: string;
}

export interface ResetPasswordInput {
  token: string;
  password: string;
}

// ---------------------------------------------------------------------------
// Error Translator Helper
// ---------------------------------------------------------------------------

export function translateAuthError(error: unknown): string {
  if (!error) return "Đã có lỗi xảy ra.";
  if (typeof error === "string") return error;

  const err = error as { message?: string; detail?: unknown };
  const raw = err.message || (typeof err.detail === "string" ? err.detail : "");

  if (raw.includes("LOGIN_BAD_CREDENTIALS")) {
    return "Email hoặc mật khẩu không chính xác.";
  }
  if (raw.includes("LOGIN_USER_NOT_VERIFIED")) {
    return "Tài khoản chưa được xác thực.";
  }
  if (raw.includes("REGISTER_USER_ALREADY_EXISTS")) {
    return "Email này đã được đăng ký tài khoản trong hệ thống.";
  }
  if (raw.includes("RESET_PASSWORD_BAD_TOKEN")) {
    return "Mã khôi phục mật khẩu không hợp lệ hoặc đã hết hạn.";
  }
  if (raw.includes("InvalidPasswordException") || raw.includes("Mật khẩu")) {
    return "Mật khẩu phải có tối thiểu 8 ký tự.";
  }

  return raw || "Yêu cầu xác thực không thành công. Vui lòng thử lại.";
}

// ---------------------------------------------------------------------------
// Token helpers — localStorage (stateless JWT)
// ---------------------------------------------------------------------------

const TOKEN_KEY = "alumni_access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// ---------------------------------------------------------------------------
// Fetch helper
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...init.headers,
  };
  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    let detailMsg = `HTTP ${res.status}`;
    if (typeof body?.detail === "string") {
      detailMsg = body.detail;
    } else if (body?.detail?.reason) {
      detailMsg = body.detail.reason;
    } else if (Array.isArray(body?.detail) && body.detail.length > 0) {
      detailMsg = body.detail[0]?.msg || "Dữ liệu không hợp lệ.";
    }
    throw new Error(detailMsg);
  }
  // 204 No Content (logout / forgot-password)
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Hook: useAuth
// ---------------------------------------------------------------------------

export function useAuth() {
  const queryClient = useQueryClient();

  // ── 1. me (Current active user) ───────────────────────────────────────────
  const {
    data: user,
    isLoading: userLoading,
    error: userError,
  } = useQuery<UserRead | null>({
    queryKey: ["me"],
    queryFn: async () => {
      if (!getToken()) return null;
      try {
        return await apiFetch<UserRead>("/users/me");
      } catch {
        // Token expired or invalid -> clear token
        clearToken();
        return null;
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  // ── 2. login ─────────────────────────────────────────────────────────────
  const loginMutation = useMutation({
    mutationFn: async ({ email, password }: LoginInput) => {
      // fastapi-users /auth/jwt/login nhận form-data (OAuth2PasswordRequestForm)
      const form = new URLSearchParams();
      form.append("username", email.trim());
      form.append("password", password);
      const res = await fetch(`${API_URL}/auth/jwt/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail =
          typeof body?.detail === "string"
            ? body.detail
            : "LOGIN_BAD_CREDENTIALS";
        throw new Error(detail);
      }
      const { access_token } = await res.json();
      return access_token as string;
    },
    onSuccess: (token) => {
      setToken(token);
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  // ── 3. register ──────────────────────────────────────────────────────────
  const registerMutation = useMutation({
    mutationFn: (input: RegisterInput) => {
      const payload: Record<string, unknown> = {
        email: input.email.trim(),
        password: input.password,
        role: input.role,
      };
      if (input.full_name?.trim()) payload.full_name = input.full_name.trim();
      // phone / zalo_id not sent — admin-only fields (SPEC §7)

      return apiFetch<UserRead>("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    // Sau khi đăng ký thành công → tự động đăng nhập luôn
    onSuccess: async (_, input) => {
      await loginMutation.mutateAsync({
        email: input.email,
        password: input.password,
      });
    },
  });

  // ── 4. update profile ────────────────────────────────────────────────────
  const updateProfileMutation = useMutation({
    mutationFn: (input: UpdateProfileInput) =>
      apiFetch<UserRead>("/users/me", {
        method: "PATCH",
        body: JSON.stringify(input),
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["me"], updated);
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  // ── 5. forgot password ───────────────────────────────────────────────────
  const forgotPasswordMutation = useMutation({
    mutationFn: ({ email }: ForgotPasswordInput) =>
      apiFetch<void>("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email: email.trim() }),
      }),
  });

  // ── 6. reset password ────────────────────────────────────────────────────
  const resetPasswordMutation = useMutation({
    mutationFn: ({ token, password }: ResetPasswordInput) =>
      apiFetch<void>("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      }),
  });

  // ── 7. logout ────────────────────────────────────────────────────────────
  const logoutMutation = useMutation({
    mutationFn: () => apiFetch<void>("/auth/jwt/logout", { method: "POST" }),
    onSettled: () => {
      clearToken();
      queryClient.setQueryData(["me"], null);
      queryClient.removeQueries({ queryKey: ["me"] });
    },
  });

  return {
    user: user ?? null,
    isLoading: userLoading,
    isAuthenticated: !!user,
    userError,

    // Login
    login: loginMutation.mutateAsync,
    loginPending: loginMutation.isPending,
    loginError: loginMutation.error,

    // Register
    register: registerMutation.mutateAsync,
    registerPending: registerMutation.isPending,
    registerError: registerMutation.error,

    // Profile
    updateProfile: updateProfileMutation.mutateAsync,
    updateProfilePending: updateProfileMutation.isPending,
    updateProfileError: updateProfileMutation.error,

    // Forgot / Reset password
    forgotPassword: forgotPasswordMutation.mutateAsync,
    forgotPasswordPending: forgotPasswordMutation.isPending,
    forgotPasswordError: forgotPasswordMutation.error,

    resetPassword: resetPasswordMutation.mutateAsync,
    resetPasswordPending: resetPasswordMutation.isPending,
    resetPasswordError: resetPasswordMutation.error,

    // Logout
    logout: logoutMutation.mutate,
    logoutPending: logoutMutation.isPending,
  };
}
