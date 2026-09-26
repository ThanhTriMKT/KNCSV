"use client";

import {
  Award,
  Briefcase,
  Calendar,
  ClipboardList,
  GraduationCap,
  HeartHandshake,
  LogIn,
  LogOut,
  Menu,
  ShieldCheck,
  Sparkles,
  User,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AuthDialog, LogoutButton, ProfileDialog } from "@/components/auth-dialog";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/alumni", label: "Cựu sinh viên", icon: GraduationCap },
  { href: "/jobs", label: "Việc làm & Thực tập", icon: Briefcase },
  { href: "/events", label: "Sự kiện", icon: Calendar },
  { href: "/surveys", label: "Khảo sát", icon: ClipboardList },
  { href: "/financial-aid", label: "Quỹ học bổng", icon: HeartHandshake },
  { href: "/career-advisor", label: "Hướng nghiệp", icon: Sparkles },
];

export function Navbar() {
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/80 bg-background/80 backdrop-blur-md transition-all">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-600 text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <GraduationCap className="size-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-base tracking-tight bg-gradient-to-r from-foreground via-foreground to-foreground/80 bg-clip-text text-foreground">
              ALUMNI PORTAL
            </span>
            <span className="text-[11px] font-medium text-muted-foreground">
              Khoa Công nghệ Thông tin
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary font-semibold"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className={cn("size-4", isActive ? "text-primary" : "text-muted-foreground")} />
                {item.label}
              </Link>
            );
          })}

          {user?.role === "admin" && (
            <Link
              href="/admin"
              className={cn(
                "flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors",
                pathname.startsWith("/admin")
                  ? "bg-amber-500/10 text-amber-600 font-semibold"
                  : "text-amber-600/90 hover:bg-amber-500/10"
              )}
            >
              <ShieldCheck className="size-4" />
              Quản trị
            </Link>
          )}
        </nav>

        {/* Right Auth / Profile */}
        <div className="hidden lg:flex items-center gap-3">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <ProfileDialog
                trigger={
                  <button
                    type="button"
                    className="flex items-center gap-2.5 rounded-full border border-border/80 bg-muted/40 py-1.5 pl-2 pr-3.5 text-xs font-medium text-foreground hover:bg-muted transition-colors"
                  >
                    <div className="flex size-7 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">
                      {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex flex-col text-left">
                      <span className="font-semibold text-xs leading-none max-w-[120px] truncate">
                        {user.full_name || user.email.split("@")[0]}
                      </span>
                      <span className="text-[10px] text-muted-foreground capitalize mt-0.5">
                        {user.role === "student" ? "Sinh viên" : user.role === "alumni" ? "Cựu SV" : "Admin"}
                      </span>
                    </div>
                  </button>
                }
              />
              <LogoutButton className="h-9 px-3 rounded-lg border border-border/60 hover:bg-destructive/10 hover:text-destructive" />
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <AuthDialog
                defaultTab="login"
                trigger={
                  <button
                    type="button"
                    className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold text-foreground hover:bg-muted transition-colors"
                  >
                    <LogIn className="size-3.5" />
                    Đăng nhập
                  </button>
                }
              />
              <AuthDialog
                defaultTab="register"
                trigger={
                  <button
                    type="button"
                    className="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow-xs hover:bg-primary/90 transition-colors"
                  >
                    Đăng ký
                  </button>
                }
              />
            </div>
          )}
        </div>

        {/* Mobile menu trigger */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X className="size-6" /> : <Menu className="size-6" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-border bg-background px-4 pt-2 pb-6 space-y-3">
          <nav className="flex flex-col gap-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium",
                    isActive
                      ? "bg-primary/10 text-primary font-semibold"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="size-4" />
                  {item.label}
                </Link>
              );
            })}

            {user?.role === "admin" && (
              <Link
                href="/admin"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-amber-600 bg-amber-500/10"
              >
                <ShieldCheck className="size-4" />
                Quản trị hệ thống
              </Link>
            )}
          </nav>

          <div className="pt-3 border-t border-border">
            {isAuthenticated && user ? (
              <div className="space-y-2">
                <div className="px-3 py-1">
                  <div className="text-xs font-semibold text-foreground">{user.full_name || user.email}</div>
                  <div className="text-[11px] text-muted-foreground capitalize">
                    {user.role === "student" ? "Sinh viên" : user.role === "alumni" ? "Cựu sinh viên" : "Quản trị viên"}
                  </div>
                </div>
                <div className="flex gap-2">
                  <ProfileDialog
                    trigger={
                      <button
                        type="button"
                        className="flex-1 rounded-lg border border-border py-2 text-xs font-semibold text-center hover:bg-muted"
                      >
                        Hồ sơ cá nhân
                      </button>
                    }
                  />
                  <LogoutButton className="flex-1 rounded-lg border border-border py-2 text-xs font-semibold text-center hover:bg-destructive/10 hover:text-destructive" />
                </div>
              </div>
            ) : (
              <div className="flex gap-2">
                <AuthDialog
                  defaultTab="login"
                  trigger={
                    <button
                      type="button"
                      className="flex-1 rounded-lg border border-border py-2 text-xs font-semibold text-center hover:bg-muted"
                    >
                      Đăng nhập
                    </button>
                  }
                />
                <AuthDialog
                  defaultTab="register"
                  trigger={
                    <button
                      type="button"
                      className="flex-1 rounded-lg bg-primary py-2 text-xs font-semibold text-primary-foreground text-center"
                    >
                      Đăng ký
                    </button>
                  }
                />
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
