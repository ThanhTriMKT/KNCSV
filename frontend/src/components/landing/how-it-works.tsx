import { MessageCircleQuestion, ShieldCheck, Users } from "lucide-react";

const STEPS = [
  {
    icon: MessageCircleQuestion,
    title: "1. Hỏi AI",
    desc: "Đặt câu hỏi tự nhiên về môn học, thực tập, công ty bạn quan tâm.",
  },
  {
    icon: Users,
    title: "2. AI gợi ý Cựu sinh viên",
    desc: "AI tìm 2-3 Cựu sinh viên phù hợp nhất, hiển thị ẩn danh.",
  },
  {
    icon: ShieldCheck,
    title: "3. Kết nối an toàn",
    desc: "Chọn Email hoặc Google Meet — hệ thống tự gửi yêu cầu, không lộ SĐT/email thật.",
  },
];

export function HowItWorks() {
  return (
    <section className="mx-auto max-w-5xl px-6 py-16">
      <h2 className="mb-10 text-center text-2xl font-semibold text-foreground">
        Hoạt động như thế nào?
      </h2>
      <div className="grid gap-4 sm:grid-cols-3">
        {STEPS.map((step) => (
          <div
            key={step.title}
            className="rounded-xl border border-border bg-card p-5 text-left"
          >
            <step.icon className="mb-3 size-6 text-accent" />
            <h3 className="mb-1.5 font-medium text-foreground">{step.title}</h3>
            <p className="text-sm text-muted-foreground">{step.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
