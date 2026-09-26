"use client";

import {
  ArrowRight,
  Award,
  CheckCircle2,
  Eye,
  EyeOff,
  GraduationCap,
  Loader2,
  Lock,
  Mail,
  ShieldCheck,
  Sparkles,
  User,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/motion/button";
import { Input } from "@/components/motion/input";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { translateAuthError, useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Tab types
// ---------------------------------------------------------------------------

type Tab = "login" | "register" | "forgot" | "guest";
type Role = "student" | "alumni";

// ---------------------------------------------------------------------------
// Shared Field Component
// ---------------------------------------------------------------------------

function FormField({
  label,
  error,
  required,
  children,
}: {
  label: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="text-xs font-semibold text-foreground flex items-center justify-between">
        <span>
          {label} {required && <span className="text-red-500">*</span>}
        </span>
      </div>
      {children}
      {error && <p className="text-[11px] text-red-500 font-medium">{error}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Login Form
// ---------------------------------------------------------------------------

function LoginForm({
  onSuccess,
  onSwitchTab,
}: {
  onSuccess: () => void;
  onSwitchTab: (tab: Tab) => void;
}) {
  const { login, loginPending, loginError } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>(
    {},
  );

  const validate = () => {
    const e: typeof errors = {};
    if (!email.trim() || !email.includes("@")) {
      e.email = "Vui lòng nhập địa chỉ email hợp lệ.";
    }
    if (!password) {
      e.password = "Vui lòng nhập mật khẩu.";
    } else if (password.length < 8) {
      e.password = "Mật khẩu phải có ít nhất 8 ký tự.";
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!validate()) return;
    try {
      await login({ email, password });
      onSuccess();
    } catch {
      // loginError được quản lý qua hook
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <FormField label="Email" error={errors.email} required>
        <Input
          type="email"
          leftIcon={<Mail className="size-4 text-muted-foreground" />}
          placeholder="1234567@dlu.edu.vn"
          value={email}
          onChange={(value) => setEmail(value)}
          disabled={loginPending}
          autoComplete="email"
        />
      </FormField>

      <FormField label="Mật khẩu" error={errors.password} required>
        <Input
          type={showPassword ? "text" : "password"}
          placeholder="••••••••"
          value={password}
          onChange={(value) => setPassword(value)}
          disabled={loginPending}
          autoComplete="current-password"
          leftIcon={<Lock className="size-4 text-muted-foreground" />}
          rightIcon={
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="pointer-events-auto"
            >
              {showPassword ? (
                <EyeOff className="size-4" />
              ) : (
                <Eye className="size-4" />
              )}
            </button>
          }
        />
      </FormField>

      <div className="flex items-center justify-end">
        <button
          type="button"
          onClick={() => onSwitchTab("forgot")}
          className="text-xs text-primary hover:underline font-medium"
        >
          Quên mật khẩu?
        </button>
      </div>

      {loginError && (
        <div className="rounded-xl bg-destructive/10 border border-destructive/20 p-3 text-xs text-destructive font-medium flex items-center gap-2">
          <span>⚠️ {translateAuthError(loginError)}</span>
        </div>
      )}

      <Button
        type="submit"
        disabled={loginPending}
        className="w-full font-semibold"
      >
        {loginPending && <Loader2 className="mr-2 size-4 animate-spin" />}
        Đăng nhập
      </Button>

      <div className="text-center text-xs text-muted-foreground">
        Chưa có tài khoản?{" "}
        <button
          type="button"
          onClick={() => onSwitchTab("register")}
          className="text-primary font-semibold hover:underline"
        >
          Đăng ký ngay
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Register Form
// ---------------------------------------------------------------------------

function RegisterForm({
  onSuccess,
  onSwitchTab,
}: {
  onSuccess: () => void;
  onSwitchTab: (tab: Tab) => void;
}) {
  const { register: registerUser, registerPending, registerError } = useAuth();
  const [role, setRole] = useState<Role>("student");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [errors, setErrors] = useState<{
    fullName?: string;
    email?: string;
    password?: string;
  }>({});

  const validate = () => {
    const e: typeof errors = {};
    if (!fullName.trim()) e.fullName = "Vui lòng nhập họ và tên.";
    if (!email.trim() || !email.includes("@")) e.email = "Email không hợp lệ.";
    if (!password) {
      e.password = "Vui lòng nhập mật khẩu.";
    } else if (password.length < 8) {
      e.password = "Mật khẩu tối thiểu 8 ký tự.";
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!validate()) return;
    try {
      await registerUser({
        role,
        full_name: fullName,
        email,
        password,
      });
      onSuccess();
    } catch {
      // registerError quản lý bởi hook
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
      {/* Role Picker */}
      <div className="space-y-1.5">
        <span className="text-xs font-semibold text-foreground">Bạn là:</span>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setRole("student")}
            className={cn(
              "flex flex-col items-start gap-1 p-2.5 rounded-xl border text-left transition-all",
              role === "student"
                ? "border-primary bg-primary/10 text-primary shadow-xs ring-1 ring-primary"
                : "border-border text-muted-foreground hover:border-foreground/30",
            )}
          >
            <div className="flex items-center gap-1.5 font-bold text-xs">
              <GraduationCap className="size-4" />
              <span>Sinh viên (SV)</span>
            </div>
            <span className="text-[10px] text-muted-foreground leading-tight">
              Hỏi đáp & xin tư vấn ẩn danh
            </span>
          </button>

          <button
            type="button"
            onClick={() => setRole("alumni")}
            className={cn(
              "flex flex-col items-start gap-1 p-2.5 rounded-xl border text-left transition-all",
              role === "alumni"
                ? "border-primary bg-primary/10 text-primary shadow-xs ring-1 ring-primary"
                : "border-border text-muted-foreground hover:border-foreground/30",
            )}
          >
            <div className="flex items-center gap-1.5 font-bold text-xs">
              <Award className="size-4" />
              <span>Cựu sinh viên (CSV)</span>
            </div>
            <span className="text-[10px] text-muted-foreground leading-tight">
              Chia sẻ kinh nghiệm & nhận điểm
            </span>
          </button>
        </div>
      </div>

      <FormField label="Họ và tên" error={errors.fullName} required>
        <Input
          placeholder="Nguyễn Văn A"
          value={fullName}
          leftIcon={<User className="size-4 text-muted-foreground" />}
          onChange={(value) => setFullName(value)}
          disabled={registerPending}
          autoComplete="name"
        />
      </FormField>

      <FormField label="Email trường" error={errors.email} required>
        <Input
          type="email"
          placeholder="ban@sinhvien.edu.vn"
          value={email}
          leftIcon={<Mail className="size-4 text-muted-foreground" />}
          onChange={(value) => setEmail(value)}
          disabled={registerPending}
          autoComplete="email"
        />
      </FormField>

      <FormField label="Mật khẩu" error={errors.password} required>
        <Input
          leftIcon={<Lock className="size-4 text-muted-foreground" />}
          type={showPassword ? "text" : "password"}
          placeholder="Tối thiểu 8 ký tự"
          value={password}
          onChange={(value) => setPassword(value)}
          disabled={registerPending}
          autoComplete="new-password"
          rightIcon={
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="pointer-events-auto"
            >
              {showPassword ? (
                <EyeOff className="size-4" />
              ) : (
                <Eye className="size-4" />
              )}
            </button>
          }
        />
      </FormField>

      <div className="flex items-start gap-1.5 rounded-lg bg-muted/60 p-2.5 text-[11px] text-muted-foreground">
        <ShieldCheck className="size-4 shrink-0 text-emerald-500 mt-0.5" />
        <span>
          <strong>Bảo mật riêng tư:</strong> Email trường của bạn không bao giờ
          bị lộ khi tư vấn — chúng tôi chỉ hiển thị thông tin ẩn danh.
        </span>
      </div>

      {registerError && (
        <div className="rounded-xl bg-destructive/10 border border-destructive/20 p-3 text-xs text-destructive font-medium flex items-center gap-2">
          <span>⚠️ {translateAuthError(registerError)}</span>
        </div>
      )}

      <Button
        type="submit"
        disabled={registerPending}
        className="w-full font-semibold"
      >
        {registerPending && <Loader2 className="mr-2 size-4 animate-spin" />}
        Tạo tài khoản & Đăng nhập
      </Button>

      <div className="text-center text-xs text-muted-foreground">
        Đã có tài khoản?{" "}
        <button
          type="button"
          onClick={() => onSwitchTab("login")}
          className="text-primary font-semibold hover:underline"
        >
          Đăng nhập
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Forgot Password Form
// ---------------------------------------------------------------------------

function ForgotPasswordForm({
  onSwitchTab,
}: {
  onSwitchTab: (tab: Tab) => void;
}) {
  const { forgotPassword, forgotPasswordPending, forgotPasswordError } =
    useAuth();
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!email.trim() || !email.includes("@")) {
      setError("Vui lòng nhập địa chỉ email hợp lệ.");
      return;
    }
    setError("");
    try {
      await forgotPassword({ email });
      setSubmitted(true);
    } catch {
      // Error handled
    }
  };

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-4 space-y-4">
        <div className="size-12 rounded-full bg-emerald-500/10 text-emerald-500 grid place-items-center">
          <CheckCircle2 className="size-6" />
        </div>
        <div className="space-y-1">
          <h4 className="font-bold text-foreground text-sm">
            Đã gửi hướng dẫn khôi phục
          </h4>
          <p className="text-xs text-muted-foreground max-w-xs">
            Nếu email <strong>{email}</strong> tồn tại trong hệ thống, bạn sẽ
            nhận được đường dẫn đặt lại mật khẩu.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => onSwitchTab("login")}
          className="w-full"
        >
          Quay lại Đăng nhập
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <FormField label="Email tài khoản" error={error} required>
        <div className="relative">
          <Input
            leftIcon={<Mail className="size-4 text-muted-foreground" />}
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(value) => setEmail(value)}
            disabled={forgotPasswordPending}
            autoComplete="email"
            className="pl-9"
          />
        </div>
      </FormField>

      {forgotPasswordError && (
        <div className="rounded-xl bg-destructive/10 border border-destructive/20 p-3 text-xs text-destructive font-medium">
          ⚠️ {translateAuthError(forgotPasswordError)}
        </div>
      )}

      <Button
        type="submit"
        disabled={forgotPasswordPending}
        className="w-full font-semibold"
      >
        {forgotPasswordPending && (
          <Loader2 className="mr-2 size-4 animate-spin" />
        )}
        Gửi yêu cầu khôi phục
      </Button>

      <div className="text-center text-xs text-muted-foreground">
        <button
          type="button"
          onClick={() => onSwitchTab("login")}
          className="text-primary font-semibold hover:underline"
        >
          Quay lại Đăng nhập
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Guest Option Form
// ---------------------------------------------------------------------------

function GuestForm({
  onContinue,
  onSwitchTab,
}: {
  onContinue: () => void;
  onSwitchTab: (tab: Tab) => void;
}) {
  const router = useRouter();

  const handleGuest = () => {
    onContinue();
    router.push("/chat");
  };

  return (
    <div className="flex flex-col items-center justify-center text-center py-4 space-y-4">
      <div className="size-14 rounded-2xl bg-gradient-to-br from-accent/20 to-violet/20 text-accent grid place-items-center border border-accent/20 shadow-xs">
        <Sparkles className="size-7 text-primary" />
      </div>
      <div className="space-y-1.5">
        <h4 className="font-bold text-foreground text-sm">
          Tiếp tục với tư cách Khách
        </h4>
        <p className="text-xs text-muted-foreground max-w-xs leading-relaxed">
          Trải nghiệm ngay khả năng trò chuyện thông minh với AI Alumni, tra cứu
          gợi ý cựu sinh viên phù hợp mà không cần tài khoản.
        </p>
      </div>

      <div className="w-full space-y-2 pt-2">
        <Button
          type="button"
          onClick={handleGuest}
          className="w-full font-bold bg-foreground text-background hover:opacity-90 py-3 rounded-xl text-sm shadow-md flex items-center justify-center gap-2"
        >
          <span>Vào ứng dụng ngay</span>
          <ArrowRight className="size-4" />
        </Button>
      </div>

      <div className="text-center text-xs text-muted-foreground pt-1">
        Bạn muốn lưu lịch sử tư vấn?{" "}
        <button
          type="button"
          onClick={() => onSwitchTab("login")}
          className="text-primary font-semibold hover:underline"
        >
          Đăng nhập
        </button>
        {" hoặc "}
        <button
          type="button"
          onClick={() => onSwitchTab("register")}
          className="text-primary font-semibold hover:underline"
        >
          Đăng ký
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// AuthDialog — Main Export
// ---------------------------------------------------------------------------

interface AuthDialogProps {
  /** Custom trigger element — Mặc định là nút "Đăng nhập" */
  trigger?: React.ReactElement;
  /** Tab mở mặc định */
  defaultTab?: Tab;
  /** Controlled open state */
  open?: boolean;
  /** Controlled open state change */
  onOpenChange?: (open: boolean) => void;
  /** Custom redirect on success */
  redirectUrl?: string;
  /** Thông báo bắt buộc đăng nhập */
  notice?: string;
  /** Chi tiết giải thích vì sao cần đăng nhập */
  noticeDescription?: string;
}

export function AuthDialog({
  trigger,
  defaultTab = "login",
  open: controlledOpen,
  onOpenChange: setControlledOpen,
  redirectUrl = "/chat",
  notice,
  noticeDescription,
}: AuthDialogProps) {
  const router = useRouter();
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false);
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : uncontrolledOpen;
  const setOpen = isControlled
    ? (setControlledOpen ?? (() => {}))
    : setUncontrolledOpen;

  const [tab, setTab] = useState<Tab>(defaultTab);

  useEffect(() => {
    if (defaultTab) {
      setTab(defaultTab);
    }
  }, [defaultTab]);

  const handleSuccess = () => {
    setOpen(false);
    if (redirectUrl) {
      router.push(redirectUrl);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {trigger && <DialogTrigger render={trigger} />}

      <DialogContent className="sm:max-w-md p-6">
        <DialogHeader className="space-y-1.5 pb-2">
          <div className="flex items-center gap-2 text-primary">
            <div className="grid size-8 place-items-center rounded-xl bg-primary/10 text-primary">
              <GraduationCap className="size-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight text-foreground flex items-center gap-1.5">
                AI Alumni Platform
                <span className="rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                  Privacy Proxy
                </span>
              </span>
            </div>
          </div>
          <DialogTitle className="text-lg font-bold">
            {notice
              ? notice
              : tab === "login"
                ? "Đăng nhập tài khoản"
                : tab === "register"
                  ? "Đăng ký thành viên mới"
                  : tab === "guest"
                    ? "Tiếp tục với tư cách Khách"
                    : "Khôi phục mật khẩu"}
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            {noticeDescription
              ? noticeDescription
              : tab === "login"
                ? "Nhập email và mật khẩu trường cấp của bạn để tiếp tục."
                : tab === "register"
                  ? "Tạo tài khoản sinh viên hoặc cựu sinh viên để lưu lịch sử và nhận tư vấn."
                  : tab === "guest"
                    ? "Trải nghiệm nhanh trò chuyện với AI và khám phá mạng lưới mà không cần đăng ký."
                    : "Nhập email đã đăng ký để nhận liên kết thiết lập lại mật khẩu."}
          </DialogDescription>
        </DialogHeader>

        {notice && (
          <div className="mb-3 flex items-start gap-2.5 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
            <Lock className="size-4 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
            <div className="space-y-0.5">
              <p className="text-xs font-bold text-amber-800 dark:text-amber-200">
                {notice}
              </p>
              {noticeDescription && (
                <p className="text-[11px] text-amber-700 dark:text-amber-300 leading-relaxed">
                  {noticeDescription}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Tab switcher */}
        {tab !== "forgot" && (
          <div className="flex rounded-xl bg-muted p-1 text-xs mb-3">
            {(notice
              ? (["login", "register"] as const)
              : (["login", "register", "guest"] as const)
            ).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={cn(
                  "flex-1 rounded-lg py-1.5 font-semibold transition-all",
                  tab === t
                    ? "bg-background text-foreground shadow-xs"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {t === "login"
                  ? "Đăng nhập"
                  : t === "register"
                    ? "Đăng ký"
                    : "Khách"}
              </button>
            ))}
          </div>
        )}

        {tab === "login" && (
          <LoginForm onSuccess={handleSuccess} onSwitchTab={setTab} />
        )}
        {tab === "register" && (
          <RegisterForm onSuccess={handleSuccess} onSwitchTab={setTab} />
        )}
        {tab === "guest" && (
          <GuestForm onContinue={handleSuccess} onSwitchTab={setTab} />
        )}
        {tab === "forgot" && <ForgotPasswordForm onSwitchTab={setTab} />}

        <DialogClose />
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// ProfileDialog — Xem & Chỉnh sửa thông tin cá nhân
// ---------------------------------------------------------------------------

export function ProfileDialog({ trigger }: { trigger?: React.ReactElement }) {
  const { user, updateProfile, updateProfilePending, updateProfileError } =
    useAuth();
  const [open, setOpen] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Sync state with user data when dialog opens
  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (isOpen && user) {
      setFullName(user.full_name ?? "");
      setSaveSuccess(false);
    }
  };

  const handleSubmit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    try {
      await updateProfile({
        full_name: fullName.trim() || undefined,
        // phone / zalo_id: admin-only, not editable by users (SPEC §7)
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch {
      // Error is handled in hook
    }
  };

  if (!user) return null;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger
        render={
          trigger ?? (
            <Button variant="outline" size="sm">
              Tài khoản
            </Button>
          )
        }
      />
      <DialogContent className="sm:max-w-md p-6">
        <DialogHeader className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="grid size-10 place-items-center rounded-xl bg-primary/10 text-primary font-bold text-base">
              {user.full_name?.[0]?.toUpperCase() ??
                user.email[0].toUpperCase()}
            </div>
            <div>
              <DialogTitle className="text-base font-bold text-foreground">
                {user.full_name || "Tài khoản người dùng"}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground">
                {user.email}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <Link
          href="/documents"
          className="text-xs text-primary bg-foreground/5 px-2 py-1 rounded-lg font-semibold hover:bg-foreground/10 flex items-center gap-1.5 w-fit"
        >
          Quản lý tài liệu đã tải lên
        </Link>
        {/* Thông tin vai trò & Điểm cống hiến */}
        <div className="grid grid-cols-2 gap-2 my-2">
          <div className="rounded-xl border border-border/80 bg-muted/40 p-3 flex flex-col gap-1">
            <span className="text-[11px] font-medium text-muted-foreground">
              Vai trò
            </span>
            <span className="text-xs font-bold text-foreground capitalize flex items-center gap-1.5">
              {user.role === "student" && (
                <GraduationCap className="size-3.5 text-primary" />
              )}
              {user.role === "alumni" && (
                <Award className="size-3.5 text-amber-500" />
              )}
              {user.role === "admin" && (
                <ShieldCheck className="size-3.5 text-emerald-500" />
              )}
              {user.role === "student"
                ? "Sinh viên"
                : user.role === "alumni"
                  ? "Cựu sinh viên"
                  : "Quản trị viên"}
            </span>
          </div>

          <div className="rounded-xl border border-border/80 bg-muted/40 p-3 flex flex-col gap-1">
            <span className="text-[11px] font-medium text-muted-foreground">
              Mã sinh viên / MSSV
            </span>
            <span className="text-xs font-bold text-foreground">
              {user.student_id || "Chưa cập nhật"}
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3 pt-1">
          <FormField label="Họ và tên">
            <Input
              value={fullName}
              onChange={(value) => setFullName(value)}
              disabled={updateProfilePending}
              leftIcon={<User className="size-4 text-muted-foreground" />}
            />
          </FormField>

          {saveSuccess && (
            <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-2.5 text-xs text-emerald-600 font-medium flex items-center gap-2">
              <CheckCircle2 className="size-4 shrink-0" />
              <span>Đã lưu thông tin cá nhân thành công!</span>
            </div>
          )}

          {updateProfileError && (
            <div className="rounded-xl bg-destructive/10 border border-destructive/20 p-2.5 text-xs text-destructive font-medium">
              ⚠️ {translateAuthError(updateProfileError)}
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <Button
              type="submit"
              disabled={updateProfilePending}
              className="flex-1 font-semibold"
            >
              {updateProfilePending && (
                <Loader2 className="mr-2 size-4 animate-spin" />
              )}
              Lưu thay đổi
            </Button>
          </div>
        </form>

        <DialogClose />
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// LogoutButton
// ---------------------------------------------------------------------------

export function LogoutButton({ className }: { className?: string }) {
  const { logout, logoutPending } = useAuth();

  return (
    <Button
      variant="ghost"
      size="sm"
      disabled={logoutPending}
      onClick={() => logout()}
      className={cn(
        "text-muted-foreground hover:text-destructive hover:bg-destructive/10 text-xs",
        className,
      )}
    >
      {logoutPending && <Loader2 className="mr-1.5 size-3.5 animate-spin" />}
      Đăng xuất
    </Button>
  );
}
