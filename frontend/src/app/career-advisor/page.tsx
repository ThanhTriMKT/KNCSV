"use client";

import {
  Award,
  BookOpen,
  BriefcaseBusiness,
  Building2,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  Code2,
  FileText,
  GraduationCap,
  Lightbulb,
  MapPin,
  MessageCircleQuestion,
  Rocket,
  Shield,
  Sparkles,
  Star,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  type CVTemplate,
  type CareerStats,
  type CareerTrack,
  type InterviewCategory,
  fetchCVTemplates,
  fetchCareerStats,
  fetchCareerTracks,
  fetchInterviewBank,
} from "@/lib/api/career-advisor";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Tab Definitions
// ---------------------------------------------------------------------------

type TabKey = "overview" | "roadmap" | "interview" | "cv";

const TABS: { key: TabKey; label: string; icon: React.ElementType }[] = [
  { key: "overview", label: "Tổng quan", icon: TrendingUp },
  { key: "roadmap", label: "Lộ trình nghề nghiệp", icon: Rocket },
  { key: "interview", label: "Ngân hàng phỏng vấn", icon: MessageCircleQuestion },
  { key: "cv", label: "Mẫu CV & Cover Letter", icon: FileText },
];

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function CareerAdvisorPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [tracks, setTracks] = useState<CareerTrack[]>([]);
  const [interviewBank, setInterviewBank] = useState<InterviewCategory[]>([]);
  const [cvTemplates, setCvTemplates] = useState<CVTemplate[]>([]);
  const [stats, setStats] = useState<CareerStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [t, ib, cv, s] = await Promise.all([
          fetchCareerTracks(),
          fetchInterviewBank(),
          fetchCVTemplates(),
          fetchCareerStats(),
        ]);
        setTracks(t);
        setInterviewBank(ib);
        setCvTemplates(cv);
        setStats(s);
      } catch {
        // If API not available, use empty defaults
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-blue-50/30 dark:to-blue-950/10">
      {/* Hero Section */}
      <div className="relative overflow-hidden border-b border-border/60 bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0djZoLTZWMzRoNnptMCAwdi02aDZWMzRoLTZ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-30" />
        <div className="relative mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex items-center gap-4 mb-4">
            <div className="flex size-14 items-center justify-center rounded-2xl bg-white/15 backdrop-blur-sm shadow-lg">
              <GraduationCap className="size-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                Trợ lý Hướng nghiệp DLU
              </h1>
              <p className="text-sm text-white/80 mt-0.5">
                Khoa Công nghệ Thông tin — Trường Đại học Đà Lạt
              </p>
            </div>
          </div>
          <p className="max-w-2xl text-sm sm:text-base text-white/90 leading-relaxed">
            Công cụ tư vấn nghề nghiệp toàn diện cho sinh viên & cựu sinh viên CNTT.
            Lộ trình phát triển chuyên ngành, ngân hàng câu hỏi phỏng vấn, và mẫu CV chuyên nghiệp.
          </p>

          {/* Quick Stats */}
          {stats && (
            <div className="mt-6 flex flex-wrap gap-3">
              {[
                { label: "Cựu sinh viên", value: stats.total_alumni, icon: Users },
                { label: "Doanh nghiệp", value: stats.total_companies, icon: Building2 },
                { label: "Việc làm", value: stats.total_jobs, icon: BriefcaseBusiness },
              ].map((s) => (
                <div
                  key={s.label}
                  className="flex items-center gap-2.5 rounded-xl bg-white/10 backdrop-blur-sm px-4 py-2.5 border border-white/10"
                >
                  <s.icon className="size-4 text-white/70" />
                  <div>
                    <span className="text-lg font-bold text-white">{s.value}</span>
                    <span className="ml-1.5 text-xs text-white/60">{s.label}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="sticky top-16 z-30 border-b border-border/60 bg-background/95 backdrop-blur-md">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <nav className="flex gap-1 overflow-x-auto py-2 scrollbar-none">
            {TABS.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                type="button"
                onClick={() => setActiveTab(key)}
                className={cn(
                  "flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-medium transition-all",
                  activeTab === key
                    ? "bg-primary/10 text-primary shadow-sm"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="size-4" />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="size-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="text-sm text-muted-foreground">Đang tải dữ liệu...</p>
          </div>
        ) : (
          <>
            {activeTab === "overview" && (
              <OverviewTab tracks={tracks} stats={stats} onTabChange={setActiveTab} />
            )}
            {activeTab === "roadmap" && <RoadmapTab tracks={tracks} />}
            {activeTab === "interview" && (
              <InterviewTab categories={interviewBank} />
            )}
            {activeTab === "cv" && <CVTab templates={cvTemplates} />}
          </>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Overview Tab
// ---------------------------------------------------------------------------

function OverviewTab({
  tracks,
  stats,
  onTabChange,
}: {
  tracks: CareerTrack[];
  stats: CareerStats | null;
  onTabChange: (tab: TabKey) => void;
}) {
  const trackIcons: Record<string, React.ElementType> = {
    software_engineering: Code2,
    data_science: TrendingUp,
    network_security: Shield,
  };

  return (
    <div className="space-y-8">
      {/* Career Tracks Cards */}
      <section>
        <div className="flex items-center gap-2 mb-5">
          <Rocket className="size-5 text-primary" />
          <h2 className="text-lg font-bold text-foreground">
            Chuyên ngành & Lộ trình Nghề nghiệp
          </h2>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {tracks.map((track) => {
            const Icon = trackIcons[track.id] ?? GraduationCap;
            return (
              <div
                key={track.id}
                className="group relative overflow-hidden rounded-2xl border border-border/60 bg-card p-6 shadow-sm hover:shadow-lg hover:border-primary/30 transition-all duration-300"
              >
                <div className="absolute top-0 right-0 w-24 h-24 rounded-bl-[4rem] bg-gradient-to-br from-primary/5 to-primary/10 -mr-2 -mt-2" />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                      <Icon className="size-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-foreground text-sm">
                        {track.name}
                      </h3>
                      <span className="text-xl">{track.icon}</span>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed mb-4">
                    {track.description}
                  </p>

                  {/* Salary Range Preview */}
                  <div className="mb-4 rounded-xl bg-gradient-to-r from-emerald-50 to-emerald-100/50 dark:from-emerald-950/30 dark:to-emerald-900/20 p-3 border border-emerald-200/50 dark:border-emerald-800/30">
                    <div className="flex items-center gap-1.5 mb-2">
                      <TrendingUp className="size-3.5 text-emerald-600 dark:text-emerald-400" />
                      <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">
                        Mức lương tham khảo
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-1">
                      {Object.entries(track.salary_range)
                        .slice(0, 4)
                        .map(([level, salary]) => (
                          <div
                            key={level}
                            className="flex justify-between text-[10px]"
                          >
                            <span className="text-muted-foreground capitalize">
                              {level}:
                            </span>
                            <span className="font-medium text-emerald-700 dark:text-emerald-300">
                              {salary}
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>

                  {/* Top Skills */}
                  <div className="flex flex-wrap gap-1.5">
                    {track.skills.core.slice(0, 3).map((skill) => (
                      <span
                        key={skill}
                        className="rounded-md bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
                      >
                        {skill}
                      </span>
                    ))}
                    {track.skills.core.length > 3 && (
                      <span className="rounded-md bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                        +{track.skills.core.length - 3}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Quick Actions */}
      <section>
        <div className="flex items-center gap-2 mb-5">
          <Sparkles className="size-5 text-amber-500" />
          <h2 className="text-lg font-bold text-foreground">
            Công cụ hữu ích
          </h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              icon: Target,
              title: "Lộ trình chuyên ngành",
              desc: "Kế hoạch học tập 4 năm chi tiết",
              color: "text-blue-600 bg-blue-100 dark:bg-blue-900/30",
              tab: "roadmap" as TabKey,
            },
            {
              icon: MessageCircleQuestion,
              title: "Câu hỏi phỏng vấn",
              desc: "Ngân hàng 20+ câu hỏi có gợi ý trả lời",
              color: "text-violet-600 bg-violet-100 dark:bg-violet-900/30",
              tab: "interview" as TabKey,
            },
            {
              icon: FileText,
              title: "Mẫu CV chuyên nghiệp",
              desc: "Template CV & Cover Letter cho IT",
              color: "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30",
              tab: "cv" as TabKey,
            },
            {
              icon: BriefcaseBusiness,
              title: "Tìm Việc Làm",
              desc: "Xem cơ hội tuyển dụng & thực tập",
              color: "text-amber-600 bg-amber-100 dark:bg-amber-900/30",
              href: "/jobs",
            },
          ].map((item) => (
            <button
              key={item.title}
              type="button"
              onClick={() => {
                if ("href" in item && item.href) {
                  window.location.href = item.href;
                } else if ("tab" in item && item.tab) {
                  onTabChange(item.tab);
                }
              }}
              className="flex items-start gap-3 rounded-xl border border-border/60 bg-card p-4 text-left hover:shadow-md hover:border-primary/20 transition-all group"
            >
              <div
                className={cn(
                  "flex size-10 shrink-0 items-center justify-center rounded-lg",
                  item.color
                )}
              >
                <item.icon className="size-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {item.desc}
                </p>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Top Skills & Companies from Data */}
      {stats && (stats.top_skills.length > 0 || stats.top_companies.length > 0) && (
        <section className="grid gap-6 lg:grid-cols-2">
          {stats.top_skills.length > 0 && (
            <div className="rounded-2xl border border-border/60 bg-card p-6">
              <div className="flex items-center gap-2 mb-4">
                <Star className="size-4 text-amber-500" />
                <h3 className="text-sm font-bold text-foreground">
                  Kỹ năng được yêu cầu nhiều nhất
                </h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {stats.top_skills.map((skill, i) => (
                  <span
                    key={skill}
                    className={cn(
                      "rounded-lg px-3 py-1.5 text-xs font-medium border",
                      i < 3
                        ? "bg-primary/10 text-primary border-primary/20"
                        : "bg-muted text-muted-foreground border-border/60"
                    )}
                  >
                    {i < 3 && "🔥 "}
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
          {stats.top_companies.length > 0 && (
            <div className="rounded-2xl border border-border/60 bg-card p-6">
              <div className="flex items-center gap-2 mb-4">
                <Building2 className="size-4 text-blue-500" />
                <h3 className="text-sm font-bold text-foreground">
                  Doanh nghiệp có nhiều cựu sinh viên DLU
                </h3>
              </div>
              <div className="space-y-2.5">
                {stats.top_companies.map((c, i) => (
                  <div
                    key={c.name}
                    className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="flex size-6 items-center justify-center rounded-md bg-blue-100 dark:bg-blue-900/30 text-xs font-bold text-blue-600">
                        {i + 1}
                      </span>
                      <span className="text-sm font-medium text-foreground">
                        {c.name}
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {c.alumni_count} cựu SV
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* CTA */}
      <section className="rounded-2xl border border-primary/20 bg-gradient-to-r from-primary/5 via-primary/10 to-violet-500/5 p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-primary/15 text-primary">
            <Lightbulb className="size-6" />
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-foreground">
              Kết nối với Cựu sinh viên DLU
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              Tìm hiểu kinh nghiệm thực tế từ các anh chị cựu sinh viên đang làm việc
              tại TMA, FPT, VNG, Viettel và nhiều công ty công nghệ hàng đầu.
            </p>
          </div>
          <Link
            href="/alumni"
            className="shrink-0 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
          >
            Xem danh sách CSV
          </Link>
        </div>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Roadmap Tab
// ---------------------------------------------------------------------------

function RoadmapTab({ tracks }: { tracks: CareerTrack[] }) {
  const [selectedTrack, setSelectedTrack] = useState<string>(
    tracks[0]?.id ?? ""
  );
  const track = tracks.find((t) => t.id === selectedTrack);

  const trackIcons: Record<string, React.ElementType> = {
    software_engineering: Code2,
    data_science: TrendingUp,
    network_security: Shield,
  };

  return (
    <div className="space-y-6">
      {/* Track Selector */}
      <div className="flex flex-wrap gap-2">
        {tracks.map((t) => {
          const Icon = trackIcons[t.id] ?? GraduationCap;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setSelectedTrack(t.id)}
              className={cn(
                "flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium border transition-all",
                selectedTrack === t.id
                  ? "bg-primary text-primary-foreground border-primary shadow-md"
                  : "bg-card text-muted-foreground border-border/60 hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="size-4" />
              {t.icon} {t.name}
            </button>
          );
        })}
      </div>

      {track && (
        <div className="space-y-6">
          {/* Track Description */}
          <div className="rounded-2xl border border-border/60 bg-card p-6">
            <h3 className="text-lg font-bold text-foreground mb-2">
              {track.icon} {track.name}
            </h3>
            <p className="text-sm text-muted-foreground">{track.description}</p>
          </div>

          {/* Roadmap Timeline */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <MapPin className="size-4 text-primary" />
              <h3 className="font-bold text-foreground">
                Lộ trình phát triển 4 năm
              </h3>
            </div>
            <div className="relative space-y-0">
              {/* Timeline line */}
              <div className="absolute left-[1.375rem] top-6 bottom-6 w-0.5 bg-gradient-to-b from-primary via-primary/50 to-primary/20 hidden sm:block" />

              {track.roadmap.map((phase, i) => (
                <div key={phase.year} className="relative flex gap-4 pb-6">
                  {/* Timeline dot */}
                  <div className="hidden sm:flex relative z-10 mt-1">
                    <div
                      className={cn(
                        "size-11 rounded-xl flex items-center justify-center shadow-sm border",
                        i === 0
                          ? "bg-primary text-white border-primary"
                          : i === track.roadmap.length - 1
                            ? "bg-emerald-500 text-white border-emerald-500"
                            : "bg-card text-primary border-primary/30"
                      )}
                    >
                      <span className="text-xs font-bold">{i + 1}</span>
                    </div>
                  </div>

                  <div className="flex-1 rounded-2xl border border-border/60 bg-card p-5 hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="rounded-md bg-primary/10 px-2 py-0.5 text-[11px] font-bold text-primary">
                        {phase.year}
                      </span>
                      <span className="text-xs text-muted-foreground">•</span>
                      <span className="text-sm font-semibold text-foreground">
                        {phase.focus}
                      </span>
                    </div>
                    <ul className="mt-3 space-y-2">
                      {phase.tasks.map((task) => (
                        <li
                          key={task}
                          className="flex items-start gap-2 text-sm text-muted-foreground"
                        >
                          <ChevronRight className="size-4 shrink-0 text-primary/50 mt-0.5" />
                          <span>{task}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Skills Grid */}
          <div className="grid gap-4 sm:grid-cols-3">
            {(
              [
                {
                  key: "core" as const,
                  title: "Kỹ năng nền tảng",
                  icon: BookOpen,
                  color: "text-blue-600 bg-blue-100 dark:bg-blue-900/30",
                },
                {
                  key: "specialized" as const,
                  title: "Kỹ năng chuyên sâu",
                  icon: Code2,
                  color: "text-violet-600 bg-violet-100 dark:bg-violet-900/30",
                },
                {
                  key: "soft" as const,
                  title: "Kỹ năng mềm",
                  icon: Users,
                  color: "text-emerald-600 bg-emerald-100 dark:bg-emerald-900/30",
                },
              ] as const
            ).map(({ key, title, icon: Icon, color }) => (
              <div
                key={key}
                className="rounded-2xl border border-border/60 bg-card p-5"
              >
                <div className="flex items-center gap-2 mb-3">
                  <div
                    className={cn(
                      "flex size-8 items-center justify-center rounded-lg",
                      color
                    )}
                  >
                    <Icon className="size-4" />
                  </div>
                  <h4 className="text-sm font-bold text-foreground">{title}</h4>
                </div>
                <ul className="space-y-1.5">
                  {track.skills[key].map((skill) => (
                    <li
                      key={skill}
                      className="flex items-center gap-2 text-xs text-muted-foreground"
                    >
                      <div className="size-1.5 rounded-full bg-primary/40" />
                      {skill}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Target Companies + Salary */}
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-border/60 bg-card p-5">
              <div className="flex items-center gap-2 mb-3">
                <Building2 className="size-4 text-blue-500" />
                <h4 className="text-sm font-bold text-foreground">
                  Công ty mục tiêu
                </h4>
              </div>
              <div className="space-y-2">
                {track.target_companies.map((c) => (
                  <div
                    key={c}
                    className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2 text-sm text-foreground"
                  >
                    <BriefcaseBusiness className="size-3.5 text-muted-foreground" />
                    {c}
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-border/60 bg-card p-5">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="size-4 text-emerald-500" />
                <h4 className="text-sm font-bold text-foreground">
                  Mức lương tham khảo
                </h4>
              </div>
              <div className="space-y-2.5">
                {Object.entries(track.salary_range).map(([level, salary]) => (
                  <div
                    key={level}
                    className="flex items-center justify-between rounded-lg bg-gradient-to-r from-emerald-50/80 to-transparent dark:from-emerald-950/20 dark:to-transparent px-3 py-2"
                  >
                    <span className="text-sm font-medium text-foreground capitalize">
                      {level}
                    </span>
                    <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                      {salary}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Interview Tab
// ---------------------------------------------------------------------------

function InterviewTab({
  categories,
}: {
  categories: InterviewCategory[];
}) {
  const [expandedQ, setExpandedQ] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-amber-200/60 dark:border-amber-800/30 bg-gradient-to-r from-amber-50 to-amber-100/30 dark:from-amber-950/20 dark:to-amber-900/10 p-5">
        <div className="flex items-start gap-3">
          <Award className="size-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-amber-800 dark:text-amber-300 text-sm">
              Mẹo phỏng vấn thành công
            </h3>
            <p className="text-xs text-amber-700/80 dark:text-amber-400/70 mt-1 leading-relaxed">
              Chuẩn bị kỹ trước 24h: nghiên cứu công ty, ôn lại kiến thức kỹ thuật, chuẩn bị
              2-3 project demo. Trả lời theo mô hình STAR (Situation → Task → Action → Result).
              Luôn hỏi ngược lại nhà tuyển dụng ít nhất 1-2 câu.
            </p>
          </div>
        </div>
      </div>

      {categories.map((cat) => (
        <div
          key={cat.category}
          className="rounded-2xl border border-border/60 bg-card overflow-hidden"
        >
          <div className="flex items-center gap-2.5 border-b border-border/40 bg-muted/30 px-5 py-4">
            <span className="text-lg">{cat.icon}</span>
            <h3 className="font-bold text-foreground text-sm">
              {cat.category}
            </h3>
            <span className="ml-auto rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary">
              {cat.questions.length} câu
            </span>
          </div>
          <div className="divide-y divide-border/40">
            {cat.questions.map((q, i) => {
              const qId = `${cat.category}-${i}`;
              const isOpen = expandedQ === qId;
              return (
                <div key={qId}>
                  <button
                    type="button"
                    onClick={() => setExpandedQ(isOpen ? null : qId)}
                    className="flex w-full items-start gap-3 px-5 py-4 text-left hover:bg-muted/30 transition-colors"
                  >
                    <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-primary/10 text-[11px] font-bold text-primary mt-0.5">
                      {i + 1}
                    </span>
                    <span className="flex-1 text-sm font-medium text-foreground leading-relaxed">
                      {q.q}
                    </span>
                    <ChevronDown
                      className={cn(
                        "size-4 shrink-0 text-muted-foreground transition-transform mt-1",
                        isOpen && "rotate-180"
                      )}
                    />
                  </button>
                  {isOpen && (
                    <div className="px-5 pb-4 pl-14">
                      <div className="rounded-xl bg-gradient-to-r from-emerald-50 to-emerald-100/30 dark:from-emerald-950/20 dark:to-emerald-900/10 border border-emerald-200/50 dark:border-emerald-800/30 p-4">
                        <div className="flex items-center gap-1.5 mb-2">
                          <Lightbulb className="size-3.5 text-emerald-600 dark:text-emerald-400" />
                          <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">
                            Gợi ý trả lời
                          </span>
                        </div>
                        <p className="text-xs text-emerald-800/80 dark:text-emerald-300/80 leading-relaxed">
                          {q.tip}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// CV Tab
// ---------------------------------------------------------------------------

function CVTab({ templates }: { templates: CVTemplate[] }) {
  const [expandedTemplate, setExpandedTemplate] = useState<string | null>(
    templates[0]?.id ?? null
  );

  return (
    <div className="space-y-6">
      {/* Tips Banner */}
      <div className="rounded-2xl border border-blue-200/60 dark:border-blue-800/30 bg-gradient-to-r from-blue-50 to-blue-100/30 dark:from-blue-950/20 dark:to-blue-900/10 p-5">
        <div className="flex items-start gap-3">
          <ClipboardCheck className="size-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-blue-800 dark:text-blue-300 text-sm">
              Nguyên tắc viết CV hiệu quả
            </h3>
            <ul className="mt-2 space-y-1 text-xs text-blue-700/80 dark:text-blue-400/70">
              <li>✅ Giữ 1 trang A4 — nhà tuyển dụng chỉ dành 6-10 giây lướt CV</li>
              <li>✅ Customize CV cho TỪNG vị trí — không dùng CV "one-size-fits-all"</li>
              <li>✅ Bắt đầu mỗi bullet bằng Action Verb: Xây dựng, Triển khai, Tối ưu...</li>
              <li>✅ Đính kèm GitHub, portfolio và demo video cho mỗi dự án</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Template Cards */}
      <div className="space-y-4">
        {templates.map((tpl) => {
          const isOpen = expandedTemplate === tpl.id;
          return (
            <div
              key={tpl.id}
              className="rounded-2xl border border-border/60 bg-card overflow-hidden hover:shadow-md transition-shadow"
            >
              <button
                type="button"
                onClick={() =>
                  setExpandedTemplate(isOpen ? null : tpl.id)
                }
                className="flex w-full items-center gap-4 px-6 py-5 text-left hover:bg-muted/30 transition-colors"
              >
                <div className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-violet-100 dark:bg-violet-900/30 text-violet-600">
                  <FileText className="size-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-bold text-foreground text-sm">
                    {tpl.name}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {tpl.target}
                  </p>
                </div>
                <ChevronDown
                  className={cn(
                    "size-4 shrink-0 text-muted-foreground transition-transform",
                    isOpen && "rotate-180"
                  )}
                />
              </button>

              {isOpen && (
                <div className="px-6 pb-6 border-t border-border/40 pt-4">
                  <div className="grid gap-5 lg:grid-cols-2">
                    {/* Sections */}
                    <div>
                      <h4 className="text-xs font-bold text-foreground uppercase tracking-wider mb-3">
                        Cấu trúc các mục
                      </h4>
                      <ol className="space-y-2">
                        {tpl.sections.map((section, i) => (
                          <li
                            key={section}
                            className="flex items-start gap-2.5"
                          >
                            <span className="flex size-5 shrink-0 items-center justify-center rounded-md bg-primary/10 text-[10px] font-bold text-primary mt-0.5">
                              {i + 1}
                            </span>
                            <span className="text-sm text-muted-foreground">
                              {section}
                            </span>
                          </li>
                        ))}
                      </ol>
                    </div>

                    {/* Tips */}
                    <div>
                      <h4 className="text-xs font-bold text-foreground uppercase tracking-wider mb-3">
                        Lưu ý quan trọng
                      </h4>
                      <div className="space-y-2">
                        {tpl.tips.map((tip) => (
                          <div
                            key={tip}
                            className="flex items-start gap-2 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-200/50 dark:border-amber-800/30 p-3"
                          >
                            <Lightbulb className="size-3.5 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
                            <span className="text-xs text-amber-800/80 dark:text-amber-300/80">
                              {tip}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
