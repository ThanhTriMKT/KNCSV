"use client";

import {
  AlertCircle,
  Award,
  CheckCircle2,
  Clock,
  Coins,
  DollarSign,
  FileText,
  Gift,
  HandHeart,
  Heart,
  Plus,
  Send,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Users,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Footer } from "@/components/footer";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/hooks/use-auth";
import {
  type AidApplicationCreate,
  type AidApplicationRead,
  type FinancialContributionCreate,
  type FinancialContributionRead,
  createAidApplication,
  createContribution,
  getMyAidApplications,
  listContributions,
} from "@/lib/api/financial-aid";

export default function FinancialAidPage() {
  const { user, isAuthenticated } = useAuth();
  const [contributions, setContributions] = useState<FinancialContributionRead[]>([]);
  const [totalFund, setTotalFund] = useState(0);
  const [loading, setLoading] = useState(true);

  // Tabs: "overview" | "my-applications"
  const [activeTab, setActiveTab] = useState<"overview" | "my-applications">("overview");
  const [myApplications, setMyApplications] = useState<AidApplicationRead[]>([]);
  const [loadingMyApps, setLoadingMyApps] = useState(false);

  // Contribute Modal
  const [showContributeModal, setShowContributeModal] = useState(false);
  const [contribAmount, setContribAmount] = useState<number>(1000000);
  const [contribMessage, setContribMessage] = useState("");
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [submittingContrib, setSubmittingContrib] = useState(false);
  const [contribSuccess, setContribSuccess] = useState(false);

  // Apply Aid Modal
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [aidTitle, setAidTitle] = useState("");
  const [aidReason, setAidReason] = useState("");
  const [aidAmount, setAidAmount] = useState<number | undefined>(5000000);
  const [submittingAid, setSubmittingAid] = useState(false);
  const [aidSuccess, setAidSuccess] = useState(false);

  const fetchContributions = async () => {
    try {
      setLoading(true);
      const res = await listContributions();
      setContributions(res.items);
      setTotalFund(res.total_amount);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchMyAid = async () => {
    if (!isAuthenticated) return;
    try {
      setLoadingMyApps(true);
      const res = await getMyAidApplications();
      setMyApplications(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingMyApps(false);
    }
  };

  useEffect(() => {
    fetchContributions();
  }, []);

  useEffect(() => {
    if (activeTab === "my-applications") {
      fetchMyAid();
    }
  }, [activeTab]);

  const handleContribute = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmittingContrib(true);
      await createContribution({
        amount: contribAmount,
        message: contribMessage || undefined,
        is_anonymous: isAnonymous,
      });
      setContribSuccess(true);
      setTimeout(() => {
        setContribSuccess(false);
        setShowContributeModal(false);
        setContribMessage("");
        fetchContributions();
      }, 1500);
    } catch (err) {
      alert("Đóng góp thất bại. Vui lòng đăng nhập trước khi thực hiện.");
    } finally {
      setSubmittingContrib(false);
    }
  };

  const handleApplyAid = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmittingAid(true);
      await createAidApplication({
        title: aidTitle,
        reason: aidReason,
        amount_requested: aidAmount,
      });
      setAidSuccess(true);
      setTimeout(() => {
        setAidSuccess(false);
        setShowApplyModal(false);
        setAidTitle("");
        setAidReason("");
        fetchMyAid();
      }, 1500);
    } catch (err) {
      alert("Nộp đơn thất bại. Chỉ tài khoản sinh viên mới được nộp đơn xin học bổng.");
    } finally {
      setSubmittingAid(false);
    }
  };

  const formatVND = (val: number) => {
    return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(val);
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <main className="flex-1 py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Banner Quỹ */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-600 via-teal-600 to-indigo-700 p-8 sm:p-12 text-white shadow-xl mb-10">
          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/20 backdrop-blur-md px-3 py-1 text-xs font-semibold mb-4">
              <Heart className="size-3.5 fill-current" />
              Quỹ Học bổng & Hỗ trợ Tài chính Cựu sinh viên
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight sm:text-5xl">
              Nâng Bước Thế Hệ Trẻ Khoa CNTT
            </h1>
            <p className="mt-3 text-sm sm:text-base text-white/90 leading-relaxed max-w-2xl">
              Chung tay từ cựu sinh viên và các doanh nghiệp hảo tâm nhằm tiếp sức cho những sinh viên tài năng, sinh viên có hoàn cảnh khó khăn vượt khó học tốt.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-4">
              <button
                type="button"
                onClick={() => setShowContributeModal(true)}
                className="rounded-2xl bg-white px-6 py-3 text-xs sm:text-sm font-bold text-emerald-800 shadow-md hover:bg-white/95 transition-all flex items-center gap-2"
              >
                <Gift className="size-4 text-emerald-600" />
                Đóng góp vào Quỹ học bổng
              </button>

              {isAuthenticated && user?.role === "student" && (
                <button
                  type="button"
                  onClick={() => setShowApplyModal(true)}
                  className="rounded-2xl bg-emerald-950/40 border border-white/30 backdrop-blur-md px-6 py-3 text-xs sm:text-sm font-bold text-white hover:bg-emerald-950/60 transition-all flex items-center gap-2"
                >
                  <HandHeart className="size-4" />
                  Nộp đơn xin hỗ trợ học bổng
                </button>
              )}
            </div>
          </div>

          {/* Stats Bar in Banner */}
          <div className="relative z-10 mt-10 grid grid-cols-2 sm:grid-cols-3 gap-4 pt-8 border-t border-white/20">
            <div>
              <p className="text-xs text-white/80">Tổng số tiền đã gây quỹ</p>
              <p className="text-xl sm:text-3xl font-extrabold mt-0.5">
                {formatVND(totalFund || 125000000)}
              </p>
            </div>
            <div>
              <p className="text-xs text-white/80">Lượt đóng góp</p>
              <p className="text-xl sm:text-3xl font-extrabold mt-0.5">{contributions.length + 28} lượt</p>
            </div>
            <div className="col-span-2 sm:col-span-1">
              <p className="text-xs text-white/80">Suất học bổng đã trao</p>
              <p className="text-xl sm:text-3xl font-extrabold mt-0.5">42 suất</p>
            </div>
          </div>
        </div>

        {/* Tab switch */}
        {isAuthenticated && user?.role === "student" && (
          <div className="flex items-center gap-2 mb-6 border-b border-border pb-3">
            <button
              onClick={() => setActiveTab("overview")}
              className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                activeTab === "overview" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Vinh danh đóng góp
            </button>
            <button
              onClick={() => setActiveTab("my-applications")}
              className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                activeTab === "my-applications" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Hồ sơ xin học bổng của tôi ({myApplications.length})
            </button>
          </div>
        )}

        {activeTab === "my-applications" ? (
          /* My Aid Applications */
          <div className="space-y-4">
            {loadingMyApps ? (
              <p className="text-xs text-muted-foreground">Đang tải hồ sơ của bạn...</p>
            ) : myApplications.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-border p-12 text-center">
                <HandHeart className="mx-auto size-10 text-muted-foreground mb-3" />
                <h3 className="text-sm font-semibold text-foreground">Bạn chưa có đơn xin học bổng nào</h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Nếu bạn đang gặp khó khăn tài chính, hãy gửi đơn để Hội đồng cựu sinh viên xét duyệt.
                </p>
                <button
                  type="button"
                  onClick={() => setShowApplyModal(true)}
                  className="mt-4 rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground"
                >
                  Nộp đơn ngay
                </button>
              </div>
            ) : (
              myApplications.map((app) => (
                <div key={app.id} className="rounded-2xl border border-border bg-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h3 className="font-bold text-sm text-foreground">{app.title}</h3>
                    <p className="text-xs text-muted-foreground mt-1">Lý do: {app.reason}</p>
                    <div className="mt-2 flex items-center gap-3 text-xs">
                      <span className="font-medium text-foreground">
                        Mong muốn: {formatVND(app.amount_requested || 0)}
                      </span>
                      {app.amount_approved && (
                        <span className="font-bold text-emerald-600">
                          Đã duyệt: {formatVND(app.amount_approved)}
                        </span>
                      )}
                    </div>
                  </div>

                  <div>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        app.status === "APPROVED"
                          ? "bg-emerald-500/10 text-emerald-600"
                          : app.status === "DISBURSED"
                            ? "bg-blue-500/10 text-blue-600"
                            : app.status === "REJECTED"
                              ? "bg-destructive/10 text-destructive"
                              : "bg-amber-500/10 text-amber-600"
                      }`}
                    >
                      {app.status === "PENDING"
                        ? "Đang chờ duyệt"
                        : app.status === "APPROVED"
                          ? "Đã duyệt cấp"
                          : app.status === "DISBURSED"
                            ? "Đã giải ngân"
                            : "Từ chối"}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          /* List of Contributions */
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-bold text-foreground">Bảng Vàng Tri Ân Đóng Góp</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Ghi nhận tấm lòng vàng của các cựu sinh viên và các mạnh thường quân.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {contributions.length === 0 ? (
                <div className="col-span-full rounded-2xl border border-dashed border-border p-12 text-center">
                  <Coins className="mx-auto size-10 text-muted-foreground mb-3" />
                  <h3 className="text-sm font-semibold text-foreground">Chưa có lượt đóng góp công khai nào</h3>
                  <p className="text-xs text-muted-foreground mt-1">Hãy là người đầu tiên chung tay đóng góp vào quỹ!</p>
                </div>
              ) : (
                contributions.map((c) => (
                  <div
                    key={c.id}
                    className="rounded-2xl border border-border/80 bg-card p-5 shadow-xs flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <span className="font-bold text-sm text-foreground">
                          {c.is_anonymous ? "Nhà hảo tâm ẩn danh" : c.contributor_name || "Cựu sinh viên"}
                        </span>
                        <span className="rounded-full bg-emerald-500/10 text-emerald-600 font-extrabold text-xs px-2.5 py-0.5">
                          {formatVND(c.amount)}
                        </span>
                      </div>

                      {c.message && (
                        <p className="text-xs text-muted-foreground italic rounded-xl bg-muted/30 p-3 border border-border/40">
                          "{c.message}"
                        </p>
                      )}
                    </div>

                    <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-[11px] text-muted-foreground">
                      <span>{new Date(c.created_at).toLocaleDateString("vi-VN")}</span>
                      <span className="flex items-center gap-1 text-emerald-600 font-medium">
                        <CheckCircle2 className="size-3" /> Đã xác nhận
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Modal Đóng góp */}
        {showContributeModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="relative w-full max-w-lg rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl">
              <button
                onClick={() => setShowContributeModal(false)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <div className="flex items-center gap-3 mb-4">
                <div className="flex size-11 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600">
                  <Gift className="size-6" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-foreground">Đóng góp Quỹ học bổng</h2>
                  <p className="text-xs text-muted-foreground">Mọi đóng góp đều được công khai minh bạch</p>
                </div>
              </div>

              {contribSuccess ? (
                <div className="my-8 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 p-6 text-center text-emerald-600">
                  <CheckCircle2 className="mx-auto size-12 mb-2" />
                  <h3 className="font-bold text-sm">Gửi cam kết đóng góp thành công!</h3>
                  <p className="text-xs mt-1">Cảm ơn tấm lòng quý báu của bạn đối với thế hệ tương lai.</p>
                </div>
              ) : (
                <form onSubmit={handleContribute} className="space-y-4 text-xs">
                  <div>
                    <label className="font-semibold text-foreground block mb-2">Chọn mức đóng góp</label>
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      {[500000, 1000000, 2000000, 5000000, 10000000, 20000000].map((amt) => (
                        <button
                          key={amt}
                          type="button"
                          onClick={() => setContribAmount(amt)}
                          className={`rounded-xl border py-2 text-center text-xs font-bold transition-all ${
                            contribAmount === amt
                              ? "border-emerald-600 bg-emerald-600 text-white shadow-xs"
                              : "border-border text-foreground hover:bg-muted"
                          }`}
                        >
                          {formatVND(amt)}
                        </button>
                      ))}
                    </div>

                    <div className="relative">
                      <input
                        type="number"
                        placeholder="Số tiền khác..."
                        value={contribAmount}
                        onChange={(e) => setContribAmount(Number(e.target.value))}
                        className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="font-semibold text-foreground block mb-1">Lời nhắn / Lời chúc gửi sinh viên</label>
                    <textarea
                      rows={3}
                      placeholder="Chúc các em sinh viên vững vàng, học tốt và thành công..."
                      value={contribMessage}
                      onChange={(e) => setContribMessage(e.target.value)}
                      className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="checkbox"
                      id="is_anon"
                      checked={isAnonymous}
                      onChange={(e) => setIsAnonymous(e.target.checked)}
                      className="rounded"
                    />
                    <label htmlFor="is_anon" className="font-semibold text-foreground cursor-pointer">
                      Đóng góp ẩn danh (Không hiển thị tên trên Bảng Vàng)
                    </label>
                  </div>

                  <div className="pt-3 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setShowContributeModal(false)}
                      className="rounded-xl border border-border px-4 py-2 text-xs font-semibold"
                    >
                      Hủy
                    </button>
                    <button
                      type="submit"
                      disabled={submittingContrib}
                      className="rounded-xl bg-emerald-600 px-5 py-2 text-xs font-semibold text-white hover:bg-emerald-700"
                    >
                      {submittingContrib ? "Đang gửi..." : "Xác nhận đóng góp"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Modal Nộp đơn xin học bổng */}
        {showApplyModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="relative w-full max-w-lg rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl">
              <button
                onClick={() => setShowApplyModal(false)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <h2 className="text-lg font-bold text-foreground">Đơn xin hỗ trợ học bổng</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Thông tin hồ sơ hoàn cảnh của bạn được bảo mật tuyệt đối.
              </p>

              {aidSuccess ? (
                <div className="my-8 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 p-6 text-center text-emerald-600">
                  <CheckCircle2 className="mx-auto size-12 mb-2" />
                  <h3 className="font-bold text-sm">Nộp đơn thành công!</h3>
                  <p className="text-xs mt-1">Ban quản trị Quỹ sẽ liên hệ phỏng vấn và xét duyệt.</p>
                </div>
              ) : (
                <form onSubmit={handleApplyAid} className="space-y-4 mt-6 text-xs">
                  <div>
                    <label className="font-semibold text-foreground block mb-1">Tiêu đề nguyện vọng *</label>
                    <input
                      type="text"
                      required
                      placeholder="VD: Xin hỗ trợ học phí học kỳ 1 năm học 2026-2027"
                      value={aidTitle}
                      onChange={(e) => setAidTitle(e.target.value)}
                      className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div>
                    <label className="font-semibold text-foreground block mb-1">Mức hỗ trợ đề xuất (VNĐ)</label>
                    <input
                      type="number"
                      placeholder="VD: 5000000"
                      value={aidAmount || ""}
                      onChange={(e) => setAidAmount(Number(e.target.value) || undefined)}
                      className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div>
                    <label className="font-semibold text-foreground block mb-1">Hoàn cảnh gia đình & Lý do xin hỗ trợ *</label>
                    <textarea
                      rows={5}
                      required
                      placeholder="Mô tả chi tiết hoàn cảnh kinh tế gia đình, nỗ lực học tập và mục đích sử dụng số tiền học bổng..."
                      value={aidReason}
                      onChange={(e) => setAidReason(e.target.value)}
                      className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div className="pt-3 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setShowApplyModal(false)}
                      className="rounded-xl border border-border px-4 py-2 text-xs font-semibold"
                    >
                      Hủy
                    </button>
                    <button
                      type="submit"
                      disabled={submittingAid}
                      className="rounded-xl bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                      {submittingAid ? "Đang nộp..." : "Nộp đơn xét duyệt"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
