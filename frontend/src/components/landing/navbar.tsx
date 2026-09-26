import { GraduationCap } from "lucide-react";
import { ButtonLink } from "@/components/motion/button";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-[var(--glass-bg)] backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        <div className="flex items-center gap-2 font-semibold text-foreground">
          <GraduationCap className="size-5 text-accent" />
          AI Alumni
        </div>
        <ButtonLink href="/app" variant="primary" size="sm">
          Trò chuyện ngay
        </ButtonLink>
      </div>
    </header>
  );
}
