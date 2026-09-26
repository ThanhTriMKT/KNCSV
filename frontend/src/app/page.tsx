"use client";

import {
  ArrowRight,
  Award,
  BookOpen,
  Briefcase,
  Building,
  Calendar,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Compass,
  FileSpreadsheet,
  Globe,
  GraduationCap,
  Heart,
  HeartHandshake,
  Layers,
  MapPin,
  MessageSquare,
  Mic,
  ShieldCheck,
  Sparkles,
  Star,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { AuthDialog } from "@/components/auth-dialog";
import { Footer } from "@/components/footer";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/hooks/use-auth";

function AnimatedCounter({
  target,
  suffix = "",
  duration = 1800,
}: {
  target: number;
  suffix?: string;
  duration?: number;
}) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const started = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          const start = performance.now();
          const step = (now: number) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - (1 - progress) ** 3;
            setCount(Math.floor(eased * target));
            if (progress < 1) requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
        }
      },
      { threshold: 0.3 }
    );
    const el = ref.current;
    if (el) observer.observe(el);
    return () => {
      if (el) observer.unobserve(el);
    };
  }, [target, duration]);

  return (
    <span ref={ref}>
      {count.toLocaleString()}
      {suffix}
    </span>
  );
}

export default function HomePage() {
  const { user, isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen flex flex-col bg-background selection:bg-primary/20 selection:text-primary">
      <Navbar />

      <main className="flex-1">
        {/* HERO SECTION */}
        <section className="relative overflow-hidden py-16 sm:py-24 lg:py-32">
          {/* Background Ambient Glows */}
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-gradient-to-tr from-blue-600/15 via-indigo-600/10 to-violet-600/15 rounded-full blur-3xl pointer-events-none" />

          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
            {/* Top Pill */}
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-4 py-1.5 text-xs font-semibold text-primary mb-6 shadow-xs">
              <Sparkles className="size-3.5" />
              <span>Khoa Công nghệ Thông tin — Cổng thông tin Cựu sinh viên</span>
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-foreground max-w-5xl mx-auto leading-[1.15]">
              Kết nối Các Thế hệ{" "}
              <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 bg-clip-text text-transparent">
                Cựu sinh viên & Sinh viên
              </span>
            </h1>

            {/* Description */}
            <p className="mt-6 text-base sm:text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              Hệ thống quản trị và kết nối toàn diện: Khảo sát việc làm sau tốt nghiệp, chia sẻ cơ hội việc làm & thực tập từ doanh nghiệp, quỹ học bổng tiếp sức và diễn đàn giao lưu công nghệ.
            </p>

            {/* Hero CTAs */}
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/alumni"
                className="rounded-2xl bg-primary px-7 py-3.5 text-sm font-bold text-primary-foreground shadow-lg shadow-primary/25 hover:bg-primary/90 transition-all flex items-center gap-2 group"
              >
                <GraduationCap className="size-4" />
                Tra cứu Cựu sinh viên
                <ArrowRight className="size-4 group-hover:translate-x-1 transition-transform" />
              </Link>

              <Link
                href="/jobs"
                className="rounded-2xl border border-border bg-card px-7 py-3.5 text-sm font-bold text-foreground hover:bg-muted/60 transition-all flex items-center gap-2"
              >
                <Briefcase className="size-4 text-emerald-600" />
                Việc làm & Thực tập
              </Link>

              <Link
                href="/events"
                className="rounded-2xl border border-border bg-card px-7 py-3.5 text-sm font-bold text-foreground hover:bg-muted/60 transition-all flex items-center gap-2"
              >
                <Calendar className="size-4 text-violet-600" />
                Sự kiện sắp tới
              </Link>
            </div>

            {/* Highlights Stats Bar */}
            <div className="mt-16 sm:mt-24 grid grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
              <div className="rounded-3xl border border-border/80 bg-card/60 backdrop-blur-sm p-6 text-center shadow-xs">
                <div className="text-3xl sm:text-4xl font-extrabold text-foreground tracking-tight">
                  <AnimatedCounter target={12500} suffix="+" />
                </div>
                <p className="text-xs text-muted-foreground font-medium mt-1">Cựu sinh viên qua các khóa</p>
              </div>

              <div className="rounded-3xl border border-border/80 bg-card/60 backdrop-blur-sm p-6 text-center shadow-xs">
                <div className="text-3xl sm:text-4xl font-extrabold text-emerald-600 tracking-tight">
                  <AnimatedCounter target={98} suffix="%" />
                </div>
                <p className="text-xs text-muted-foreground font-medium mt-1">Tỷ lệ có việc làm sau tốt nghiệp</p>
              </div>

              <div className="rounded-3xl border border-border/80 bg-card/60 backdrop-blur-sm p-6 text-center shadow-xs">
                <div className="text-3xl sm:text-4xl font-extrabold text-indigo-600 tracking-tight">
                  <AnimatedCounter target={280} suffix="+" />
                </div>
                <p className="text-xs text-muted-foreground font-medium mt-1">Doanh nghiệp đối tác tuyển dụng</p>
              </div>

              <div className="rounded-3xl border border-border/80 bg-card/60 backdrop-blur-sm p-6 text-center shadow-xs">
                <div className="text-3xl sm:text-4xl font-extrabold text-violet-600 tracking-tight">
                  <AnimatedCounter target={1800} suffix="tr" />
                </div>
                <p className="text-xs text-muted-foreground font-medium mt-1">Quỹ học bổng hỗ trợ sinh viên</p>
              </div>
            </div>
          </div>
        </section>

        {/* 5 MODULES SHOWCASE */}
        <section className="py-16 sm:py-24 bg-muted/20 border-y border-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 border border-primary/20 px-3 py-1 text-xs font-semibold text-primary mb-3">
                <Layers className="size-3.5" />
                Hệ Sinh Thái Phân Hệ Nghiệp Vụ
              </div>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-foreground tracking-tight">
                Giải Pháp Toàn Diện Cho Khoa & Cựu Sinh Viên
              </h2>
              <p className="mt-3 text-sm text-muted-foreground">
                Đáp ứng toàn bộ quy trình từ lưu trữ dữ liệu, khảo sát kiểm định chất lượng, cầu nối tuyển dụng cho đến gắn kết cộng đồng.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {/* Module 1 */}
              <div className="group rounded-3xl border border-border bg-card p-8 shadow-xs hover:shadow-xl hover:border-primary/40 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex size-14 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-600 mb-6 group-hover:scale-110 transition-transform">
                    <GraduationCap className="size-7" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    1. Quản lý Cơ sở dữ liệu Cựu sinh viên
                  </h3>
                  <p className="mt-3 text-xs text-muted-foreground leading-relaxed">
                    Tra cứu hồ sơ cựu sinh viên theo niên khóa, chuyên ngành, đơn vị công tác và kỹ năng. Hỗ trợ nhà trường import dữ liệu từ Excel với tính năng xem trước (preview) tự động.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-border/60">
                  <Link
                    href="/alumni"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-primary group-hover:gap-2.5 transition-all"
                  >
                    Xem danh sách Cựu sinh viên
                    <ArrowRight className="size-3.5" />
                  </Link>
                </div>
              </div>

              {/* Module 2 */}
              <div className="group rounded-3xl border border-border bg-card p-8 shadow-xs hover:shadow-xl hover:border-primary/40 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex size-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 mb-6 group-hover:scale-110 transition-transform">
                    <ClipboardList className="size-7" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    2. Khảo sát Tình trạng Việc làm
                  </h3>
                  <p className="mt-3 text-xs text-muted-foreground leading-relaxed">
                    Khảo sát tỷ lệ việc làm, mức thu nhập, tính phù hợp với chương trình đào tạo sau tốt nghiệp 1 năm, 3 năm. Báo cáo thống kê trực quan phục vụ công tác kiểm định chất lượng GD.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-border/60">
                  <Link
                    href="/surveys"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-600 group-hover:gap-2.5 transition-all"
                  >
                    Tham gia & Xem thống kê
                    <ArrowRight className="size-3.5" />
                  </Link>
                </div>
              </div>

              {/* Module 3 */}
              <div className="group rounded-3xl border border-border bg-card p-8 shadow-xs hover:shadow-xl hover:border-primary/40 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex size-14 items-center justify-center rounded-2xl bg-purple-500/10 text-purple-600 mb-6 group-hover:scale-110 transition-transform">
                    <Briefcase className="size-7" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    3. Tuyển dụng & Giới thiệu Việc làm
                  </h3>
                  <p className="mt-3 text-xs text-muted-foreground leading-relaxed">
                    Nơi cựu sinh viên đăng tin tìm kiếm nhân sự trẻ tiềm năng và hỗ trợ thực tập cho các đàn em khóa dưới. Sinh viên nộp CV ứng tuyển và theo dõi trạng thái trực tiếp.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-border/60">
                  <Link
                    href="/jobs"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-purple-600 group-hover:gap-2.5 transition-all"
                  >
                    Xem cơ hội việc làm
                    <ArrowRight className="size-3.5" />
                  </Link>
                </div>
              </div>

              {/* Module 4 */}
              <div className="group rounded-3xl border border-border bg-card p-8 shadow-xs hover:shadow-xl hover:border-primary/40 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex size-14 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-600 mb-6 group-hover:scale-110 transition-transform">
                    <HeartHandshake className="size-7" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    4. Quỹ Học bổng & Hỗ trợ Tài chính
                  </h3>
                  <p className="mt-3 text-xs text-muted-foreground leading-relaxed">
                    Huy động nguồn lực đóng góp từ cộng đồng cựu sinh viên và doanh nghiệp. Sinh viên có hoàn cảnh khó khăn có thể nộp đơn xin hỗ trợ học phí và học bổng khuyến học.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-border/60">
                  <Link
                    href="/financial-aid"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-rose-600 group-hover:gap-2.5 transition-all"
                  >
                    Đóng góp & Nộp đơn học bổng
                    <ArrowRight className="size-3.5" />
                  </Link>
                </div>
              </div>

              {/* Module 5 */}
              <div className="group rounded-3xl border border-border bg-card p-8 shadow-xs hover:shadow-xl hover:border-primary/40 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex size-14 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-600 mb-6 group-hover:scale-110 transition-transform">
                    <Calendar className="size-7" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    5. Tổ chức Sự kiện & Talkshow Giao lưu
                  </h3>
                  <p className="mt-3 text-xs text-muted-foreground leading-relaxed">
                    Không gian tổ chức các ngày lễ kỷ niệm thành lập khoa, chuỗi talkshow định hướng nghề nghiệp, workshop công nghệ. Cựu sinh viên có thể đăng ký vai trò diễn giả chia sẻ.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-border/60">
                  <Link
                    href="/events"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-600 group-hover:gap-2.5 transition-all"
                  >
                    Xem lịch sự kiện
                    <ArrowRight className="size-3.5" />
                  </Link>
                </div>
              </div>

              {/* Module 6: Career Advisor */}
              <div className="group rounded-3xl border border-border bg-card p-8 shadow-xs hover:shadow-xl hover:border-primary/40 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex size-14 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-600 mb-6 group-hover:scale-110 transition-transform">
                    <Sparkles className="size-7" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    6. Trợ lý Hướng nghiệp & Kỹ năng
                  </h3>
                  <p className="mt-3 text-xs text-muted-foreground leading-relaxed">
                    Lộ trình nghề nghiệp CNTT (Software, Data/AI, DevOps, Cybersecurity), ngân hàng câu hỏi phỏng vấn thực tế, mẫu CV/Cover Letter chuẩn và phân tích thị trường việc làm.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-border/60">
                  <Link
                    href="/career-advisor"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-cyan-600 group-hover:gap-2.5 transition-all"
                  >
                    Khám phá lộ trình & kỹ năng
                    <ArrowRight className="size-3.5" />
                  </Link>
                </div>
              </div>

              {/* Admin Portal card */}
              <div className="group rounded-3xl border border-border bg-gradient-to-br from-indigo-500/5 via-violet-500/5 to-purple-500/5 p-8 shadow-xs hover:shadow-xl hover:border-indigo-500/40 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex size-14 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-600 mb-6 group-hover:scale-110 transition-transform">
                    <ShieldCheck className="size-7" />
                  </div>
                  <h3 className="text-lg font-bold text-foreground">
                    Phân hệ Quản trị & Đồng bộ (Admin)
                  </h3>
                  <p className="mt-3 text-xs text-muted-foreground leading-relaxed">
                    Dành cho Ban chủ nhiệm Khoa và Giáo vụ: Quản lý import dữ liệu sinh viên, kiểm duyệt tin tuyển dụng, phê duyệt hồ sơ học bổng và điểm danh người tham dự sự kiện.
                  </p>
                </div>
                <div className="mt-8 pt-4 border-t border-border/60">
                  <Link
                    href="/admin"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 group-hover:gap-2.5 transition-all"
                  >
                    Vào trang Quản trị
                    <ArrowRight className="size-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* PROUD ALUMNI SECTION */}
        <section className="py-16 sm:py-24">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center max-w-2xl mx-auto mb-14">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-foreground">
                Tự Hào Cựu Sinh Viên Khoa CNTT
              </h2>
              <p className="mt-2 text-xs text-muted-foreground">
                Các thế hệ cựu sinh viên hiện đang giữ các vị trí chủ chốt tại các tập đoàn công nghệ hàng đầu trong và ngoài nước.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                {
                  name: "Nguyễn Văn Hùng",
                  grad: "K2014",
                  role: "Principal Engineer",
                  company: "VNG Corporation",
                  quote: "Khoa CNTT đã trang bị cho tôi nền tảng tư duy thuật toán vững chắc để bứt phá.",
                },
                {
                  name: "Trần Mai Anh",
                  grad: "K2016",
                  role: "Head of Data Science",
                  company: "Shopee Vietnam",
                  quote: "Rất vinh dự được quay lại trường chia sẻ tại các talkshow hướng nghiệp cho các bạn sinh viên.",
                },
                {
                  name: "Lê Hoàng Quân",
                  grad: "K2018",
                  role: "Tech Lead",
                  company: "FPT Software",
                  quote: "Cổng thông tin giúp doanh nghiệp chúng tôi tuyển dụng được nhiều bạn fresher xuất sắc.",
                },
                {
                  name: "Phạm Minh Đức",
                  grad: "K2019",
                  role: "Cloud Architect",
                  company: "Viettel Telecom",
                  quote: "Quỹ học bổng cựu sinh viên là cầu nối ý nghĩa để tri ân mái trường xưa.",
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="rounded-3xl border border-border/80 bg-card p-6 shadow-xs flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center gap-3 mb-4">
                      <div className="flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary font-bold">
                        {item.name.charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-bold text-sm text-foreground">{item.name}</h4>
                        <span className="text-[11px] text-muted-foreground font-mono">Khóa {item.grad}</span>
                      </div>
                    </div>
                    <p className="text-xs font-semibold text-primary">{item.role}</p>
                    <p className="text-xs text-muted-foreground">{item.company}</p>
                    <p className="mt-4 text-xs text-foreground/80 italic bg-muted/20 p-3 rounded-2xl border border-border/40">
                      "{item.quote}"
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* BOTTOM CTA BANNER */}
        <section className="py-16 bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-700 text-white">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Bạn là Cựu sinh viên Khoa Công nghệ Thông tin?
            </h2>
            <p className="mt-4 text-sm sm:text-base text-white/90 max-w-2xl mx-auto leading-relaxed">
              Hãy tham gia mạng lưới để cập nhật thông tin đồng môn, mở rộng cơ hội tuyển dụng và truyền cảm hứng cho các thế hệ sinh viên tương lai.
            </p>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
              <AuthDialog
                defaultTab="register"
                trigger={
                  <button
                    type="button"
                    className="rounded-2xl bg-white px-8 py-3.5 text-xs sm:text-sm font-bold text-indigo-700 shadow-md hover:bg-white/95 transition-all"
                  >
                    Đăng ký tài khoản Cựu sinh viên
                  </button>
                }
              />

              <Link
                href="/alumni"
                className="rounded-2xl bg-white/10 border border-white/20 px-8 py-3.5 text-xs sm:text-sm font-bold text-white hover:bg-white/20 transition-all"
              >
                Tìm kiếm bạn bè cùng khóa
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
