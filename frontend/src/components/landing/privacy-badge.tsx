import { Lock } from "lucide-react";

export function PrivacyBadge() {
  return (
    <section className="mx-auto max-w-3xl px-6 pb-20">
      <div className="flex items-start gap-3 rounded-xl border border-border bg-muted/20 p-5">
        <Lock className="mt-0.5 size-5 shrink-0 text-accent" />
        <div>
          <p className="font-medium text-foreground">
            Không bao giờ lộ số điện thoại/email thật
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            AI Alumni là một lớp trung gian ẩn danh (Privacy Proxy) — mọi kết
            nối giữa Sinh viên và Cựu sinh viên đều đi qua hệ thống, không phải
            một mạng xã hội công khai.
          </p>
        </div>
      </div>
    </section>
  );
}
