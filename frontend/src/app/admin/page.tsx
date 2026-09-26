"use client";

import {
  AlertTriangle,
  Briefcase,
  Building,
  Check,
  CheckCircle2,
  Clock,
  DollarSign,
  FileSpreadsheet,
  FileText,
  GraduationCap,
  HeartHandshake,
  Layers,
  ShieldAlert,
  ShieldCheck,
  Upload,
  UserCheck,
  Users,
  X,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Footer } from "@/components/footer";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/hooks/use-auth";
import {
  type ImportPreviewResult,
  confirmAlumniImport,
  uploadAlumniImport,
} from "@/lib/api/alumni";
import {
  type AidApplicationRead,
  confirmContribution,
  listAidApplications,
  reviewAidApplication,
} from "@/lib/api/financial-aid";
import {
  type JobPostRead,
  approveJob,
  listJobs,
} from "@/lib/api/jobs";

export default function AdminDashboardPage() {
  const { user, isAuthenticated } = useAuth();

  // Active Admin Tab
  const [adminTab, setAdminTab] = useState<"import" | "jobs" | "scholarships">("import");

  // --- MODULE 1: EXCEL / CSV IMPORT ---
  const [file, setFile] = useState<File | null>(null);
  const [importPreview, setImportPreview] = useState<ImportPreviewResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [importResult, setImportResult] = useState<string | null>(null);

  // --- MODULE 3: JOB APPROVAL ---
  const [pendingJobs, setPendingJobs] = useState<JobPostRead[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [rejectingJobId, setRejectingJobId] = useState<string | null>(null);
  const [rejectNote, setRejectNote] = useState("");

  // --- MODULE 4: SCHOLARSHIP REVIEW ---
  const [aidApps, setAidApps] = useState<AidApplicationRead[]>([]);
  const [loadingAid, setLoadingAid] = useState(false);
  const [reviewingApp, setReviewingApp] = useState<AidApplicationRead | null>(null);
  const [approvedAmount, setApprovedAmount] = useState<number>(5000000);
  const [reviewNote, setReviewNote] = useState("");

  // Load Pending Jobs
  const fetchPendingJobs = async () => {
    try {
      setLoadingJobs(true);
      const res = await listJobs({ status: "PENDING", limit: 50 });
      setPendingJobs(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingJobs(false);
    }
  };

  // Load Aid Applications
  const fetchAidApps = async () => {
    try {
      setLoadingAid(true);
      const res = await listAidApplications();
      setAidApps(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingAid(false);
    }
  };

  useEffect(() => {
    if (adminTab === "jobs") fetchPendingJobs();
    if (adminTab === "scholarships") fetchAidApps();
  }, [adminTab]);

  // Handle File Upload Preview
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUploadPreview = async () => {
    if (!file) return;
    try {
      setUploading(true);
      setImportResult(null);
      const res = await uploadAlumniImport(file);
      setImportPreview(res);
    } catch (err) {
      alert("Đọc file thất bại. Vui lòng kiểm tra định dạng .xlsx hoặc .csv.");
    } finally {
      setUploading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!importPreview) return;
    try {
      setConfirming(true);
      const res = await confirmAlumniImport(importPreview.session_id);
      setImportResult(`Đã import thành công: ${res.new_count} hồ sơ mới, cập nhật ${res.update_count} hồ sơ.`);
      setImportPreview(null);
      setFile(null);
    } catch (err) {
      alert("Import thất bại.");
    } finally {
      setConfirming(false);
    }
  };

  // Handle Job Approve / Reject
  const handleApproveJob = async (jobId: string) => {
    try {
      await approveJob(jobId, { status: "APPROVED" });
      fetchPendingJobs();
    } catch (err) {
      alert("Phê duyệt tin thất bại.");
    }
  };

  const handleRejectJob = async (jobId: string) => {
    try {
      await approveJob(jobId, { status: "REJECTED", rejection_note: rejectNote });
      setRejectingJobId(null);
      setRejectNote("");
      fetchPendingJobs();
    } catch (err) {
      alert("Từ chối tin thất bại.");
    }
  };

  // Handle Aid Review
  const handleReviewAid = async (status: "APPROVED" | "REJECTED" | "DISBURSED") => {
    if (!reviewingApp) return;
    try {
      await reviewAidApplication(reviewingApp.id, {
        status,
        amount_approved: status === "APPROVED" ? approvedAmount : undefined,
        review_note: reviewNote,
      });
      setReviewingApp(null);
      setReviewNote("");
      fetchAidApps();
    } catch (err) {
      alert("Xét duyệt thất bại.");
    }
  };

  if (!isAuthenticated || user?.role !== "admin") {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Navbar />
        <main className="flex-1 flex items-center justify-center p-6 text-center">
          <div className="max-w-md rounded-3xl border border-destructive/20 bg-destructive/5 p-8">
            <ShieldAlert className="mx-auto size-12 text-destructive mb-3" />
            <h2 className="text-lg font-bold text-foreground">Khu vực Giới hạn</h2>
            <p className="text-xs text-muted-foreground mt-2">
              Trang này chỉ dành riêng cho Ban Quản trị Khoa Công nghệ Thông tin. Vui lòng đăng nhập với tài khoản Admin.
            </p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <main className="flex-1 py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-xs font-semibold text-amber-600 mb-3">
            <ShieldCheck className="size-4" />
            Ban Quản trị Cổng thông tin Cựu sinh viên
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
            Bảng điều khiển Quản trị Hệ thống
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Quản lý đồng bộ dữ liệu sinh viên tốt nghiệp, phê duyệt tin tuyển dụng, và xét duyệt quỹ hỗ trợ học bổng.
          </p>
        </div>

        {/* Admin Navigation Tabs */}
        <div className="flex border-b border-border gap-2 mb-8 overflow-x-auto">
          <button
            onClick={() => setAdminTab("import")}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-bold border-b-2 transition-all shrink-0 ${
              adminTab === "import"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileSpreadsheet className="size-4" />
            Import Excel Cựu sinh viên
          </button>

          <button
            onClick={() => setAdminTab("jobs")}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-bold border-b-2 transition-all shrink-0 ${
              adminTab === "jobs"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Briefcase className="size-4" />
            Duyệt tin tuyển dụng ({pendingJobs.length})
          </button>

          <button
            onClick={() => setAdminTab("scholarships")}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-bold border-b-2 transition-all shrink-0 ${
              adminTab === "scholarships"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <HeartHandshake className="size-4" />
            Xét duyệt Quỹ học bổng ({aidApps.filter((a) => a.status === "PENDING").length})
          </button>
        </div>

        {/* TAB 1: IMPORT EXCEL / CSV */}
        {adminTab === "import" && (
          <div className="space-y-6">
            <div className="rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-xs">
              <h3 className="text-base font-bold text-foreground">Import Dữ liệu Cựu sinh viên từ Excel / CSV</h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-2xl leading-relaxed">
                Hệ thống tự động so khớp cột (MSSV, Họ tên, Email, Năm tốt nghiệp, Chuyên ngành, Nơi công tác) và hiển thị xem trước (preview) danh sách các dòng thêm mới hoặc cập nhật.
              </p>

              <div className="mt-6 flex flex-col sm:flex-row items-center gap-4">
                <input
                  type="file"
                  accept=".xlsx, .xls, .csv"
                  onChange={handleFileChange}
                  className="block w-full text-xs text-muted-foreground file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
                />

                <button
                  type="button"
                  disabled={!file || uploading}
                  onClick={handleUploadPreview}
                  className="rounded-xl bg-primary px-6 py-2.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all shrink-0 shadow-xs flex items-center gap-2"
                >
                  <Upload className="size-4" />
                  {uploading ? "Đang đọc file..." : "Tải lên & Xem trước"}
                </button>
              </div>

              {importResult && (
                <div className="mt-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 p-4 text-xs font-medium text-emerald-600 flex items-center gap-2">
                  <CheckCircle2 className="size-5 shrink-0" />
                  <span>{importResult}</span>
                </div>
              )}
            </div>

            {/* Preview Section */}
            {importPreview && (
              <div className="rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-md">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border">
                  <div>
                    <h3 className="text-sm font-bold text-foreground">Kết quả Đọc trước File: {importPreview.filename}</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Tổng số: <span className="font-bold text-foreground">{importPreview.total_records}</span> dòng — Thêm mới:{" "}
                      <span className="font-bold text-emerald-600">{importPreview.new_count}</span>, Cập nhật:{" "}
                      <span className="font-bold text-blue-600">{importPreview.update_count}</span>
                    </p>
                  </div>

                  <button
                    type="button"
                    disabled={confirming}
                    onClick={handleConfirmImport}
                    className="rounded-xl bg-emerald-600 px-6 py-2.5 text-xs font-bold text-white hover:bg-emerald-700 shadow-sm transition-all"
                  >
                    {confirming ? "Đang lưu..." : "Xác nhận Import vào Hệ thống"}
                  </button>
                </div>

                <div className="overflow-x-auto mt-6">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-border bg-muted/30">
                        <th className="p-3 font-semibold text-muted-foreground">Thao tác</th>
                        <th className="p-3 font-semibold text-muted-foreground">MSSV</th>
                        <th className="p-3 font-semibold text-muted-foreground">Họ và tên</th>
                        <th className="p-3 font-semibold text-muted-foreground">Email</th>
                        <th className="p-3 font-semibold text-muted-foreground">Năm TN</th>
                        <th className="p-3 font-semibold text-muted-foreground">Ngành</th>
                        <th className="p-3 font-semibold text-muted-foreground">Nơi công tác</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {importPreview.preview.map((rec, i) => (
                        <tr key={i} className="hover:bg-muted/20">
                          <td className="p-3">
                            <span
                              className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                                rec.action === "create"
                                  ? "bg-emerald-500/10 text-emerald-600"
                                  : "bg-blue-500/10 text-blue-600"
                              }`}
                            >
                              {rec.action === "create" ? "Thêm mới" : "Cập nhật"}
                            </span>
                          </td>
                          <td className="p-3 font-mono font-medium">{rec.student_id}</td>
                          <td className="p-3 font-medium text-foreground">{rec.full_name}</td>
                          <td className="p-3 text-muted-foreground">{rec.email}</td>
                          <td className="p-3">{rec.graduation_year || "—"}</td>
                          <td className="p-3">{rec.major || "—"}</td>
                          <td className="p-3">{rec.company_name || rec.current_job_title || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: DUYỆT TIN TUYỂN DỤNG */}
        {adminTab === "jobs" && (
          <div className="space-y-4">
            {loadingJobs ? (
              <p className="text-xs text-muted-foreground">Đang tải tin tuyển dụng chờ duyệt...</p>
            ) : pendingJobs.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-border p-12 text-center">
                <CheckCircle2 className="mx-auto size-10 text-emerald-500 mb-3" />
                <h3 className="text-sm font-semibold text-foreground">Không có tin tuyển dụng nào đang chờ duyệt</h3>
                <p className="text-xs text-muted-foreground mt-1">Tất cả các tin mới đã được xử lý.</p>
              </div>
            ) : (
              pendingJobs.map((job) => (
                <div key={job.id} className="rounded-2xl border border-border bg-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="rounded-full bg-purple-500/10 text-purple-600 px-2.5 py-0.5 text-[10px] font-bold">
                        {job.job_type}
                      </span>
                      <h3 className="font-bold text-sm text-foreground">{job.title}</h3>
                    </div>
                    <p className="text-xs font-semibold text-primary">{job.company_name || "Doanh nghiệp"}</p>
                    <p className="text-xs text-muted-foreground mt-2 line-clamp-2 max-w-2xl">{job.description}</p>
                    <p className="text-[11px] text-muted-foreground mt-2">
                      Ngày đăng: {new Date(job.created_at).toLocaleDateString("vi-VN")}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleApproveJob(job.id)}
                      className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-700 flex items-center gap-1.5"
                    >
                      <Check className="size-4" />
                      Phê duyệt
                    </button>

                    <button
                      type="button"
                      onClick={() => setRejectingJobId(job.id)}
                      className="rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-2 text-xs font-semibold text-destructive hover:bg-destructive/20 flex items-center gap-1.5"
                    >
                      <X className="size-4" />
                      Từ chối
                    </button>
                  </div>
                </div>
              ))
            )}

            {/* Modal Từ chối tin */}
            {rejectingJobId && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
                <div className="w-full max-w-md rounded-3xl border border-border bg-card p-6 shadow-2xl">
                  <h3 className="font-bold text-sm text-foreground mb-2">Lý do từ chối tin tuyển dụng</h3>
                  <textarea
                    rows={3}
                    placeholder="VD: Thông tin tuyển dụng chưa đầy đủ hoặc không phù hợp..."
                    value={rejectNote}
                    onChange={(e) => setRejectNote(e.target.value)}
                    className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                  <div className="mt-4 flex justify-end gap-2">
                    <button
                      onClick={() => setRejectingJobId(null)}
                      className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold"
                    >
                      Hủy
                    </button>
                    <button
                      onClick={() => handleRejectJob(rejectingJobId)}
                      className="rounded-xl bg-destructive px-4 py-1.5 text-xs font-semibold text-white"
                    >
                      Xác nhận từ chối
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: XÉT DUYỆT HỌC BỔNG */}
        {adminTab === "scholarships" && (
          <div className="space-y-4">
            {loadingAid ? (
              <p className="text-xs text-muted-foreground">Đang tải danh sách đơn xin học bổng...</p>
            ) : aidApps.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-border p-12 text-center">
                <HeartHandshake className="mx-auto size-10 text-muted-foreground mb-3" />
                <h3 className="text-sm font-semibold text-foreground">Không có hồ sơ nào</h3>
              </div>
            ) : (
              aidApps.map((app) => (
                <div key={app.id} className="rounded-2xl border border-border bg-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                          app.status === "APPROVED"
                            ? "bg-emerald-500/10 text-emerald-600"
                            : app.status === "DISBURSED"
                              ? "bg-blue-500/10 text-blue-600"
                              : app.status === "REJECTED"
                                ? "bg-destructive/10 text-destructive"
                                : "bg-amber-500/10 text-amber-600"
                        }`}
                      >
                        {app.status}
                      </span>
                      <h3 className="font-bold text-sm text-foreground">{app.title}</h3>
                    </div>

                    <p className="text-xs text-muted-foreground mt-1">
                      Sinh viên: <span className="font-semibold text-foreground">{app.applicant_name}</span> (MSSV: {app.applicant_student_id}) — Email: {app.applicant_email}
                    </p>

                    <p className="text-xs text-foreground mt-2 bg-muted/20 p-3 rounded-xl border border-border/40 max-w-2xl">
                      {app.reason}
                    </p>

                    <div className="mt-2 text-xs flex items-center gap-3">
                      <span>Đề xuất: <strong className="text-foreground">{new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(app.amount_requested || 0)}</strong></span>
                      {app.amount_approved && (
                        <span>Đã duyệt: <strong className="text-emerald-600">{new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(app.amount_approved)}</strong></span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        setReviewingApp(app);
                        setApprovedAmount(app.amount_requested || 5000000);
                      }}
                      className="rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                      Xét duyệt
                    </button>
                  </div>
                </div>
              ))
            )}

            {/* Modal Xét duyệt */}
            {reviewingApp && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
                <div className="w-full max-w-md rounded-3xl border border-border bg-card p-6 shadow-2xl text-xs space-y-4">
                  <h3 className="font-bold text-sm text-foreground">Xét duyệt hồ sơ học bổng</h3>
                  <p className="text-muted-foreground">{reviewingApp.title}</p>

                  <div>
                    <label className="font-semibold block mb-1">Số tiền duyệt cấp (VNĐ)</label>
                    <input
                      type="number"
                      value={approvedAmount}
                      onChange={(e) => setApprovedAmount(Number(e.target.value))}
                      className="w-full rounded-xl border border-border bg-background p-2"
                    />
                  </div>

                  <div>
                    <label className="font-semibold block mb-1">Ghi chú xét duyệt</label>
                    <textarea
                      rows={3}
                      value={reviewNote}
                      onChange={(e) => setReviewNote(e.target.value)}
                      placeholder="Nhận xét từ Hội đồng xét duyệt..."
                      className="w-full rounded-xl border border-border bg-background p-2"
                    />
                  </div>

                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      onClick={() => setReviewingApp(null)}
                      className="rounded-xl border border-border px-3 py-1.5 font-semibold"
                    >
                      Đóng
                    </button>
                    <button
                      onClick={() => handleReviewAid("REJECTED")}
                      className="rounded-xl bg-destructive px-3 py-1.5 font-semibold text-white"
                    >
                      Từ chối
                    </button>
                    <button
                      onClick={() => handleReviewAid("APPROVED")}
                      className="rounded-xl bg-emerald-600 px-4 py-1.5 font-semibold text-white"
                    >
                      Phê duyệt cấp
                    </button>
                    <button
                      onClick={() => handleReviewAid("DISBURSED")}
                      className="rounded-xl bg-blue-600 px-4 py-1.5 font-semibold text-white"
                    >
                      Giải ngân
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
