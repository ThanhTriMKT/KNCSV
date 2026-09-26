"use client";

import {
  BarChart3,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  ClipboardList,
  Clock,
  GraduationCap,
  HelpCircle,
  Plus,
  Send,
  Star,
  Trash2,
  Users,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Footer } from "@/components/footer";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/hooks/use-auth";
import {
  type QuestionType,
  type SurveyAnswerCreate,
  type SurveyCreate,
  type SurveyQuestionCreate,
  type SurveyRead,
  type SurveyStats,
  createSurvey,
  getSurveyDetail,
  getSurveyStats,
  listSurveys,
  submitSurveyResponse,
} from "@/lib/api/surveys";

export default function SurveysPage() {
  const { user, isAuthenticated } = useAuth();
  const [surveys, setSurveys] = useState<SurveyRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fill survey modal
  const [activeSurvey, setActiveSurvey] = useState<SurveyRead | null>(null);
  const [answers, setAnswers] = useState<Record<string, { text?: string; selected?: string[]; scale?: number }>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Stats modal
  const [selectedStats, setSelectedStats] = useState<SurveyStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);

  // Create survey modal (Admin)
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSurveyTitle, setNewSurveyTitle] = useState("");
  const [newSurveyDesc, setNewSurveyDesc] = useState("");
  const [targetGradYear, setTargetGradYear] = useState<number | undefined>();
  const [questions, setQuestions] = useState<SurveyQuestionCreate[]>([
    {
      question_text: "Bạn đã có việc làm sau khi tốt nghiệp chưa?",
      question_type: "single_choice",
      options: { items: ["Đã có việc làm", "Đang học tiếp bậc cao hơn", "Đang tìm kiếm việc làm"] },
      is_required: true,
      order_index: 0,
    },
    {
      question_text: "Công việc hiện tại có đúng chuyên ngành đào tạo không?",
      question_type: "single_choice",
      options: { items: ["Đúng chuyên ngành", "Liên quan đến ngành", "Trái ngành hoàn toàn"] },
      is_required: true,
      order_index: 1,
    },
    {
      question_text: "Mức thu nhập trung bình hàng tháng (VNĐ)?",
      question_type: "single_choice",
      options: { items: ["Dưới 10 triệu", "10 - 15 triệu", "15 - 25 triệu", "Trên 25 triệu"] },
      is_required: true,
      order_index: 2,
    },
    {
      question_text: "Đánh giá mức độ hài lòng về chương trình đào tạo của Khoa (1 - 5 sao)",
      question_type: "scale",
      is_required: true,
      order_index: 3,
    },
  ]);
  const [creating, setCreating] = useState(false);

  const fetchSurveys = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listSurveys();
      setSurveys(res.items);
    } catch (err) {
      console.error(err);
      setError("Không thể tải danh sách khảo sát.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSurveys();
  }, []);

  const openFillSurvey = async (survey: SurveyRead) => {
    try {
      const detail = await getSurveyDetail(survey.id);
      setActiveSurvey(detail);
      setAnswers({});
      setSubmitSuccess(false);
    } catch (err) {
      alert("Không thể tải chi tiết khảo sát.");
    }
  };

  const openStats = async (surveyId: string) => {
    try {
      setLoadingStats(true);
      const stats = await getSurveyStats(surveyId);
      setSelectedStats(stats);
    } catch (err) {
      alert("Không thể tải thống kê khảo sát. Chỉ quản trị viên mới xem được thống kê chi tiết.");
    } finally {
      setLoadingStats(false);
    }
  };

  const handleAnswerChange = (qId: string, value: { text?: string; selected?: string[]; scale?: number }) => {
    setAnswers((prev) => ({
      ...prev,
      [qId]: { ...prev[qId], ...value },
    }));
  };

  const handleSubmitSurvey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSurvey) return;

    try {
      setSubmitting(true);
      const payload: SurveyAnswerCreate[] = activeSurvey.questions.map((q) => {
        const a = answers[q.id] || {};
        return {
          question_id: q.id,
          answer_text: a.text,
          answer_choices: a.selected ? { selected: a.selected } : undefined,
          answer_scale: a.scale,
        };
      });

      await submitSurveyResponse(activeSurvey.id, payload);
      setSubmitSuccess(true);
      setTimeout(() => {
        setActiveSurvey(null);
        fetchSurveys();
      }, 1500);
    } catch (err) {
      alert("Gửi khảo sát thất bại. Vui lòng đăng nhập tài khoản cựu sinh viên trước khi điền khảo sát.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddQuestion = () => {
    setQuestions([
      ...questions,
      {
        question_text: "Câu hỏi mới...",
        question_type: "text",
        is_required: true,
        order_index: questions.length,
      },
    ]);
  };

  const handleRemoveQuestion = (idx: number) => {
    setQuestions(questions.filter((_, i) => i !== idx));
  };

  const handleCreateSurvey = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreating(true);
      await createSurvey({
        title: newSurveyTitle,
        description: newSurveyDesc,
        target_graduation_year: targetGradYear,
        questions,
      });
      setShowCreateModal(false);
      setNewSurveyTitle("");
      setNewSurveyDesc("");
      fetchSurveys();
    } catch (err) {
      alert("Tạo khảo sát thất bại.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <main className="flex-1 py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs font-semibold text-blue-600 mb-3">
              <ClipboardList className="size-4" />
              Khảo sát Việc làm Sau Tốt nghiệp
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
              Khảo sát Tình trạng Việc làm & Đánh giá
            </h1>
            <p className="mt-2 text-sm text-muted-foreground max-w-2xl">
              Thu thập ý kiến đóng góp, tỷ lệ có việc làm và mức độ phù hợp của chương trình đào tạo để không ngừng nâng cao chất lượng giáo dục.
            </p>
          </div>

          {isAuthenticated && user?.role === "admin" && (
            <button
              type="button"
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-xs font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
            >
              <Plus className="size-4" />
              Tạo biểu mẫu khảo sát
            </button>
          )}
        </div>

        {/* Survey Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-56 rounded-2xl border border-border bg-card/60 animate-pulse p-6" />
            ))}
          </div>
        ) : surveys.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border p-12 text-center">
            <ClipboardList className="mx-auto size-10 text-muted-foreground mb-3" />
            <h3 className="text-sm font-semibold text-foreground">Chưa có khảo sát nào đang mở</h3>
            <p className="text-xs text-muted-foreground mt-1">Các đợt khảo sát định kỳ sẽ được thông báo qua email cựu sinh viên.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {surveys.map((sv) => (
              <div
                key={sv.id}
                className="rounded-2xl border border-border/80 bg-card p-6 shadow-xs hover:shadow-md hover:border-primary/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                        sv.status === "ACTIVE"
                          ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20"
                          : sv.status === "DRAFT"
                            ? "bg-amber-500/10 text-amber-600"
                            : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {sv.status === "ACTIVE" ? "Đang mở khảo sát" : sv.status === "DRAFT" ? "Bản nháp" : "Đã đóng"}
                    </span>

                    {sv.target_graduation_year && (
                      <span className="text-[11px] font-semibold text-muted-foreground">
                        Khóa {sv.target_graduation_year}
                      </span>
                    )}
                  </div>

                  <h3 className="font-bold text-base text-foreground line-clamp-2">{sv.title}</h3>
                  {sv.description && <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{sv.description}</p>}

                  <div className="mt-4 flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1.5 font-medium text-foreground">
                      <Users className="size-3.5 text-primary" />
                      {sv.response_count} lượt phản hồi
                    </span>
                    <span className="flex items-center gap-1.5">
                      <HelpCircle className="size-3.5" />
                      {sv.questions?.length || 4} câu hỏi
                    </span>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-border/60 flex items-center justify-between gap-2">
                  {isAuthenticated && user?.role === "admin" && (
                    <button
                      type="button"
                      onClick={() => openStats(sv.id)}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
                    >
                      <BarChart3 className="size-3.5" />
                      Xem thống kê
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() => openFillSurvey(sv)}
                    className="ml-auto rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs"
                  >
                    Điền khảo sát
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal Điền khảo sát */}
        {activeSurvey && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="relative w-full max-w-2xl rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setActiveSurvey(null)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <h2 className="text-xl font-bold text-foreground">{activeSurvey.title}</h2>
              {activeSurvey.description && <p className="text-xs text-muted-foreground mt-1">{activeSurvey.description}</p>}

              {submitSuccess ? (
                <div className="my-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 p-8 text-center text-emerald-600">
                  <CheckCircle2 className="mx-auto size-14 mb-2" />
                  <h3 className="font-bold text-base">Cảm ơn bạn đã gửi khảo sát!</h3>
                  <p className="text-xs mt-1">Ý kiến đóng góp của bạn rất quan trọng đối với Khoa.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmitSurvey} className="space-y-6 mt-6">
                  {activeSurvey.questions.map((q, idx) => (
                    <div key={q.id} className="rounded-2xl border border-border/70 bg-muted/20 p-4 text-xs">
                      <div className="font-bold text-foreground mb-3 flex items-start gap-2">
                        <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-[10px]">
                          {idx + 1}
                        </span>
                        <span>
                          {q.question_text} {q.is_required && <span className="text-destructive">*</span>}
                        </span>
                      </div>

                      {/* Single Choice */}
                      {q.question_type === "single_choice" && q.options?.items && (
                        <div className="space-y-2 pl-7">
                          {q.options.items.map((opt, oIdx) => (
                            <label key={oIdx} className="flex items-center gap-2 cursor-pointer text-foreground/90 hover:text-foreground">
                              <input
                                type="radio"
                                name={`q_${q.id}`}
                                required={q.is_required}
                                checked={answers[q.id]?.selected?.[0] === opt}
                                onChange={() => handleAnswerChange(q.id, { selected: [opt] })}
                                className="accent-primary"
                              />
                              <span>{opt}</span>
                            </label>
                          ))}
                        </div>
                      )}

                      {/* Multiple Choice */}
                      {q.question_type === "multiple_choice" && q.options?.items && (
                        <div className="space-y-2 pl-7">
                          {q.options.items.map((opt, oIdx) => {
                            const cur = answers[q.id]?.selected || [];
                            return (
                              <label key={oIdx} className="flex items-center gap-2 cursor-pointer text-foreground/90 hover:text-foreground">
                                <input
                                  type="checkbox"
                                  checked={cur.includes(opt)}
                                  onChange={(e) => {
                                    const next = e.target.checked ? [...cur, opt] : cur.filter((x) => x !== opt);
                                    handleAnswerChange(q.id, { selected: next });
                                  }}
                                  className="accent-primary rounded"
                                />
                                <span>{opt}</span>
                              </label>
                            );
                          })}
                        </div>
                      )}

                      {/* Scale 1-5 */}
                      {q.question_type === "scale" && (
                        <div className="flex items-center gap-3 pl-7">
                          {[1, 2, 3, 4, 5].map((val) => (
                            <button
                              key={val}
                              type="button"
                              onClick={() => handleAnswerChange(q.id, { scale: val })}
                              className={`flex size-9 items-center justify-center rounded-xl border text-xs font-bold transition-all ${
                                answers[q.id]?.scale === val
                                  ? "border-amber-500 bg-amber-500 text-white shadow-xs"
                                  : "border-border hover:bg-muted text-foreground"
                              }`}
                            >
                              <Star className={`size-3.5 mr-0.5 ${answers[q.id]?.scale === val ? "fill-white" : ""}`} />
                              {val}
                            </button>
                          ))}
                          <span className="text-[11px] text-muted-foreground ml-2">(1: Kém - 5: Xuất sắc)</span>
                        </div>
                      )}

                      {/* Text input */}
                      {q.question_type === "text" && (
                        <div className="pl-7">
                          <textarea
                            rows={3}
                            placeholder="Nhập ý kiến đóng góp của bạn..."
                            value={answers[q.id]?.text || ""}
                            onChange={(e) => handleAnswerChange(q.id, { text: e.target.value })}
                            className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                          />
                        </div>
                      )}
                    </div>
                  ))}

                  <div className="pt-3 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setActiveSurvey(null)}
                      className="rounded-xl border border-border px-4 py-2 text-xs font-semibold"
                    >
                      Hủy
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="rounded-xl bg-primary px-6 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                      {submitting ? "Đang gửi..." : "Hoàn thành & Gửi khảo sát"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Modal Thống kê Khảo sát */}
        {selectedStats && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="relative w-full max-w-2xl rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setSelectedStats(null)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <h2 className="text-xl font-bold text-foreground">Báo cáo Thống kê Khảo sát</h2>
              <p className="text-xs text-muted-foreground mt-0.5">{selectedStats.title}</p>

              <div className="mt-4 rounded-2xl bg-primary/10 border border-primary/20 p-4 text-xs flex items-center justify-between">
                <span className="font-semibold text-primary">Tổng số cựu sinh viên đã phản hồi:</span>
                <span className="text-base font-extrabold text-primary">{selectedStats.total_responses} lượt</span>
              </div>

              <div className="space-y-4 mt-6">
                {selectedStats.questions.map((q) => (
                  <div key={q.id} className="rounded-2xl border border-border bg-muted/20 p-4 text-xs">
                    <h4 className="font-bold text-foreground mb-3">{q.text}</h4>

                    {q.counts && (
                      <div className="space-y-2">
                        {Object.entries(q.counts).map(([choice, count]) => {
                          const pct = selectedStats.total_responses > 0
                            ? Math.round((count / selectedStats.total_responses) * 100)
                            : 0;
                          return (
                            <div key={choice}>
                              <div className="flex justify-between text-[11px] mb-1">
                                <span className="font-medium text-foreground">{choice}</span>
                                <span className="text-muted-foreground">
                                  {count} ({pct}%)
                                </span>
                              </div>
                              <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                                <div
                                  className="h-full bg-primary rounded-full transition-all duration-500"
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {q.average !== undefined && (
                      <div className="flex items-center gap-2 text-amber-500 font-bold text-sm">
                        <Star className="size-4 fill-amber-500" />
                        <span>Điểm trung bình: {q.average} / 5</span>
                      </div>
                    )}

                    {q.text_samples && q.text_samples.length > 0 && (
                      <div className="space-y-1.5 mt-2">
                        <span className="text-[11px] font-semibold text-muted-foreground">Trích đoạn ý kiến:</span>
                        {q.text_samples.slice(0, 5).map((txt, tIdx) => (
                          <div key={tIdx} className="rounded-lg bg-background p-2 border border-border text-[11px] text-foreground italic">
                            "{txt}"
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  type="button"
                  onClick={() => setSelectedStats(null)}
                  className="rounded-xl border border-border px-5 py-2 text-xs font-semibold"
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Tạo khảo sát */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="relative w-full max-w-xl rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setShowCreateModal(false)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <h2 className="text-lg font-bold text-foreground">Tạo đợt khảo sát mới</h2>
              <p className="text-xs text-muted-foreground mt-0.5">Khảo sát sẽ gửi tới các cựu sinh viên theo bộ lọc đối tượng.</p>

              <form onSubmit={handleCreateSurvey} className="space-y-4 mt-6 text-xs">
                <div>
                  <label className="font-semibold text-foreground block mb-1">Tiêu đề khảo sát *</label>
                  <input
                    type="text"
                    required
                    placeholder="VD: Khảo sát Tình hình Việc làm Cựu sinh viên Khóa 2024"
                    value={newSurveyTitle}
                    onChange={(e) => setNewSurveyTitle(e.target.value)}
                    className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div>
                  <label className="font-semibold text-foreground block mb-1">Mô tả ngắn</label>
                  <textarea
                    rows={2}
                    placeholder="Mục đích khảo sát và lời cảm ơn..."
                    value={newSurveyDesc}
                    onChange={(e) => setNewSurveyDesc(e.target.value)}
                    className="w-full rounded-xl border border-border bg-background p-2.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div>
                  <label className="font-semibold text-foreground block mb-1">Khóa tốt nghiệp mục tiêu (để trống nếu gửi tất cả)</label>
                  <input
                    type="number"
                    placeholder="VD: 2024"
                    value={targetGradYear || ""}
                    onChange={(e) => setTargetGradYear(Number(e.target.value) || undefined)}
                    className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>

                <div className="pt-2">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-foreground">Danh sách câu hỏi ({questions.length})</span>
                    <button
                      type="button"
                      onClick={handleAddQuestion}
                      className="text-primary text-[11px] font-semibold hover:underline flex items-center gap-1"
                    >
                      <Plus className="size-3" /> Thêm câu hỏi
                    </button>
                  </div>

                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {questions.map((q, idx) => (
                      <div key={idx} className="flex items-center justify-between gap-2 rounded-xl border border-border bg-muted/30 p-2.5">
                        <span className="text-foreground truncate flex-1">{idx + 1}. {q.question_text}</span>
                        <span className="text-[10px] text-muted-foreground uppercase">{q.question_type}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveQuestion(idx)}
                          className="text-destructive hover:opacity-80 p-1"
                        >
                          <Trash2 className="size-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="pt-3 flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="rounded-xl border border-border px-4 py-2 text-xs font-semibold"
                  >
                    Hủy
                  </button>
                  <button
                    type="submit"
                    disabled={creating}
                    className="rounded-xl bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
                  >
                    {creating ? "Đang tạo..." : "Phát hành khảo sát"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
