"use client";

import {
  AlertCircle,
  Briefcase,
  Building,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Clock,
  DollarSign,
  FileText,
  Filter,
  MapPin,
  Plus,
  Send,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Footer } from "@/components/footer";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/hooks/use-auth";
import {
  type JobApplicationRead,
  type JobPostCreate,
  type JobPostRead,
  applyJob,
  createJob,
  getMyApplications,
  listJobs,
} from "@/lib/api/jobs";

export default function JobsPage() {
  const { user, isAuthenticated } = useAuth();
  const [jobs, setJobs] = useState<JobPostRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [jobType, setJobType] = useState<string>("");
  const [selectedJob, setSelectedJob] = useState<JobPostRead | null>(null);

  // Post Job Dialog
  const [showPostModal, setShowPostModal] = useState(false);
  const [postFormData, setPostFormData] = useState<JobPostCreate>({
    title: "",
    job_type: "full_time",
    description: "",
    requirements: "",
    benefits: "",
    location: "",
    company_name: "",
    salary_min: undefined,
    salary_max: undefined,
  });
  const [posting, setPosting] = useState(false);
  const [postSuccess, setPostSuccess] = useState(false);

  // Apply Dialog
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [applyingJob, setApplyingJob] = useState<JobPostRead | null>(null);
  const [coverLetter, setCoverLetter] = useState("");
  const [cvUrl, setCvUrl] = useState("");
  const [applying, setApplying] = useState(false);
  const [applySuccess, setApplySuccess] = useState(false);

  // My Applications Tab
  const [activeTab, setActiveTab] = useState<"all" | "my-applications">("all");
  const [myApplications, setMyApplications] = useState<JobApplicationRead[]>([]);
  const [loadingApps, setLoadingApps] = useState(false);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listJobs({
        search: search || undefined,
        job_type: jobType || undefined,
        limit: 50,
      });
      setJobs(res.items);
    } catch (err) {
      console.error(err);
      setError("Không thể tải danh sách việc làm.");
    } finally {
      setLoading(false);
    }
  };

  const fetchMyApplications = async () => {
    if (!isAuthenticated) return;
    try {
      setLoadingApps(true);
      const res = await getMyApplications();
      setMyApplications(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingApps(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [jobType]);

  useEffect(() => {
    if (activeTab === "my-applications") {
      fetchMyApplications();
    }
  }, [activeTab]);

  const handlePostJob = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setPosting(true);
      await createJob(postFormData);
      setPostSuccess(true);
      setTimeout(() => {
        setPostSuccess(false);
        setShowPostModal(false);
        fetchJobs();
      }, 1500);
    } catch (err) {
      alert("Đăng tin không thành công. Hãy đảm bảo bạn đã đăng nhập tài khoản Cựu sinh viên/Admin.");
    } finally {
      setPosting(false);
    }
  };

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!applyingJob) return;
    try {
      setApplying(true);
      await applyJob(applyingJob.id, { cover_letter: coverLetter, cv_url: cvUrl });
      setApplySuccess(true);
      setTimeout(() => {
        setApplySuccess(false);
        setShowApplyModal(false);
        setCoverLetter("");
        setCvUrl("");
        fetchJobs();
      }, 1500);
    } catch (err) {
      alert("Ứng tuyển thất bại. Vui lòng đăng nhập tài khoản sinh viên và thử lại.");
    } finally {
      setApplying(false);
    }
  };

  const formatVND = (amount?: number | null) => {
    if (!amount) return null;
    return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(amount);
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <main className="flex-1 py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-600 mb-3">
              <Briefcase className="size-4" />
              Cầu nối Việc làm & Thực tập
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
              Cơ hội Nghề nghiệp từ Cựu sinh viên
            </h1>
            <p className="mt-2 text-sm text-muted-foreground max-w-2xl">
              Các vị trí tuyển dụng thực tập, việc làm chính thức từ mạng lưới cựu sinh viên và doanh nghiệp liên kết uy tín.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {isAuthenticated && (user?.role === "alumni" || user?.role === "admin") && (
              <button
                type="button"
                onClick={() => setShowPostModal(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-xs font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
              >
                <Plus className="size-4" />
                Đăng tin tuyển dụng
              </button>
            )}
          </div>
        </div>

        {/* Tab switch */}
        {isAuthenticated && user?.role === "student" && (
          <div className="flex items-center gap-2 mb-6 border-b border-border pb-3">
            <button
              onClick={() => setActiveTab("all")}
              className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                activeTab === "all" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Tất cả vị trí tuyển dụng
            </button>
            <button
              onClick={() => setActiveTab("my-applications")}
              className={`rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                activeTab === "my-applications" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Đơn đã nộp của tôi ({myApplications.length})
            </button>
          </div>
        )}

        {activeTab === "my-applications" ? (
          /* My Applications List */
          <div className="space-y-4">
            {loadingApps ? (
              <p className="text-xs text-muted-foreground">Đang tải danh sách đơn ứng tuyển...</p>
            ) : myApplications.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-border p-12 text-center">
                <FileText className="mx-auto size-10 text-muted-foreground mb-3" />
                <h3 className="text-sm font-semibold text-foreground">Bạn chưa nộp đơn ứng tuyển nào</h3>
                <p className="text-xs text-muted-foreground mt-1">Duyệt qua danh sách việc làm để tìm cơ hội phù hợp.</p>
              </div>
            ) : (
              myApplications.map((app) => (
                <div key={app.id} className="rounded-2xl border border-border bg-card p-5 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-foreground">Đơn ứng tuyển #{app.id.slice(0, 8)}</h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      Ngày nộp: {new Date(app.created_at).toLocaleDateString("vi-VN")}
                    </p>
                    {app.cv_url && (
                      <a href={app.cv_url} target="_blank" rel="noreferrer" className="text-xs text-primary underline mt-1 inline-block">
                        Xem liên kết CV
                      </a>
                    )}
                  </div>
                  <span className="rounded-full bg-blue-500/10 text-blue-600 font-semibold px-3 py-1 text-xs">
                    {app.status === "submitted" ? "Đã nộp" : app.status}
                  </span>
                </div>
              ))
            )}
          </div>
        ) : (
          <>
            {/* Filter */}
            <div className="rounded-2xl border border-border bg-card p-4 sm:p-5 shadow-xs mb-8 flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder="Tìm theo vị trí, kỹ năng, công ty..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && fetchJobs()}
                  className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
              </div>

              <div className="sm:w-56">
                <select
                  value={jobType}
                  onChange={(e) => setJobType(e.target.value)}
                  className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">Tất cả hình thức</option>
                  <option value="full_time">Toàn thời gian (Full-time)</option>
                  <option value="part_time">Bán thời gian (Part-time)</option>
                  <option value="internship">Thực tập sinh (Internship)</option>
                </select>
              </div>

              <button
                type="button"
                onClick={fetchJobs}
                className="rounded-xl bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs shrink-0"
              >
                Tìm kiếm
              </button>
            </div>

            {/* Jobs Grid */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-56 rounded-2xl border border-border bg-card/60 animate-pulse p-6" />
                ))}
              </div>
            ) : jobs.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-border p-12 text-center">
                <Briefcase className="mx-auto size-10 text-muted-foreground mb-3" />
                <h3 className="text-sm font-semibold text-foreground">Chưa có tin tuyển dụng nào phù hợp</h3>
                <p className="text-xs text-muted-foreground mt-1">Các cơ hội mới sẽ liên tục được cựu sinh viên cập nhật.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {jobs.map((job) => (
                  <div
                    key={job.id}
                    className="rounded-2xl border border-border/80 bg-card p-6 shadow-xs hover:shadow-md hover:border-primary/40 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                            job.job_type === "internship"
                              ? "bg-purple-500/10 text-purple-600 border border-purple-500/20"
                              : job.job_type === "full_time"
                                ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20"
                                : "bg-amber-500/10 text-amber-600 border border-amber-500/20"
                          }`}
                        >
                          {job.job_type === "internship"
                            ? "Thực tập sinh"
                            : job.job_type === "full_time"
                              ? "Toàn thời gian"
                              : "Bán thời gian"}
                        </span>
                        {job.status === "PENDING" && (
                          <span className="rounded-full bg-amber-500/10 text-amber-600 px-2 py-0.5 text-[10px] font-semibold">
                            Chờ duyệt
                          </span>
                        )}
                      </div>

                      <h3
                        onClick={() => setSelectedJob(job)}
                        className="font-bold text-base text-foreground hover:text-primary transition-colors cursor-pointer line-clamp-1"
                      >
                        {job.title}
                      </h3>

                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-medium mt-1">
                        <Building className="size-3.5" />
                        <span className="truncate">{job.company_name || "Doanh nghiệp đối tác"}</span>
                      </div>

                      <div className="mt-4 space-y-2 text-xs text-muted-foreground">
                        {job.location && (
                          <div className="flex items-center gap-2">
                            <MapPin className="size-3.5 shrink-0 text-muted-foreground" />
                            <span className="truncate">{job.location}</span>
                          </div>
                        )}
                        {(job.salary_min || job.salary_max) ? (
                          <div className="flex items-center gap-2 text-emerald-600 font-semibold">
                            <DollarSign className="size-3.5 shrink-0" />
                            <span>
                              {job.salary_min ? formatVND(job.salary_min) : "Từ"} - {job.salary_max ? formatVND(job.salary_max) : "Thương lượng"}
                            </span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <DollarSign className="size-3.5 shrink-0" />
                            <span>Lương: Thỏa thuận</span>
                          </div>
                        )}
                        {job.deadline && (
                          <div className="flex items-center gap-2">
                            <Clock className="size-3.5 shrink-0" />
                            <span>Hạn nộp: {new Date(job.deadline).toLocaleDateString("vi-VN")}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-border/60 flex items-center justify-between gap-2">
                      <button
                        type="button"
                        onClick={() => setSelectedJob(job)}
                        className="text-xs font-semibold text-muted-foreground hover:text-foreground"
                      >
                        Xem chi tiết
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setApplyingJob(job);
                          setShowApplyModal(true);
                        }}
                        className="rounded-xl bg-primary px-3.5 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs"
                      >
                        Ứng tuyển
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Modal Chi tiết Job */}
        {selectedJob && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="relative w-full max-w-2xl rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setSelectedJob(null)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <h2 className="text-xl font-extrabold text-foreground">{selectedJob.title}</h2>
              <p className="text-xs font-semibold text-primary mt-1">{selectedJob.company_name || "Doanh nghiệp"}</p>

              <div className="mt-6 space-y-4 text-xs">
                <div>
                  <h4 className="font-bold uppercase text-muted-foreground tracking-wider mb-1.5">Mô tả công việc</h4>
                  <div className="rounded-xl bg-muted/30 p-3.5 border border-border/60 text-foreground whitespace-pre-line leading-relaxed">
                    {selectedJob.description}
                  </div>
                </div>

                {selectedJob.requirements && (
                  <div>
                    <h4 className="font-bold uppercase text-muted-foreground tracking-wider mb-1.5">Yêu cầu ứng viên</h4>
                    <div className="rounded-xl bg-muted/30 p-3.5 border border-border/60 text-foreground whitespace-pre-line leading-relaxed">
                      {selectedJob.requirements}
                    </div>
                  </div>
                )}

                {selectedJob.benefits && (
                  <div>
                    <h4 className="font-bold uppercase text-muted-foreground tracking-wider mb-1.5">Quyền lợi</h4>
                    <div className="rounded-xl bg-muted/30 p-3.5 border border-border/60 text-foreground whitespace-pre-line leading-relaxed">
                      {selectedJob.benefits}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-8 pt-4 border-t border-border flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedJob(null)}
                  className="rounded-xl border border-border px-4 py-2 text-xs font-semibold"
                >
                  Đóng
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setApplyingJob(selectedJob);
                    setSelectedJob(null);
                    setShowApplyModal(true);
                  }}
                  className="rounded-xl bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground"
                >
                  Ứng tuyển vị trí này
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Ứng tuyển */}
        {showApplyModal && applyingJob && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
            <div className="relative w-full max-w-lg rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl">
              <button
                onClick={() => setShowApplyModal(false)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <h2 className="text-lg font-bold text-foreground">Ứng tuyển: {applyingJob.title}</h2>
              <p className="text-xs text-muted-foreground mt-1">Đơn vị: {applyingJob.company_name}</p>

              {applySuccess ? (
                <div className="my-8 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 p-6 text-center text-emerald-600">
                  <CheckCircle2 className="mx-auto size-12 mb-2" />
                  <h3 className="font-bold text-sm">Nộp đơn thành công!</h3>
                  <p className="text-xs mt-1">Hồ sơ của bạn đã được chuyển tới nhà tuyển dụng.</p>
                </div>
              ) : (
                <form onSubmit={handleApply} className="space-y-4 mt-6">
                  <div>
                    <label className="text-xs font-semibold text-foreground block mb-1">
                      Link CV (Google Drive / Notion / PDF) *
                    </label>
                    <input
                      type="url"
                      required
                      placeholder="https://drive.google.com/file/d/..."
                      value={cvUrl}
                      onChange={(e) => setCvUrl(e.target.value)}
                      className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-foreground block mb-1">
                      Thư giới thiệu / Lời nhắn ngắn
                    </label>
                    <textarea
                      rows={4}
                      placeholder="Giới thiệu bản thân và lý do bạn phù hợp với vị trí này..."
                      value={coverLetter}
                      onChange={(e) => setCoverLetter(e.target.value)}
                      className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div className="pt-2 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setShowApplyModal(false)}
                      className="rounded-xl border border-border px-4 py-2 text-xs font-semibold"
                    >
                      Hủy
                    </button>
                    <button
                      type="submit"
                      disabled={applying}
                      className="rounded-xl bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                      {applying ? "Đang gửi..." : "Gửi hồ sơ"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Modal Đăng tin */}
        {showPostModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="relative w-full max-w-xl rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setShowPostModal(false)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <h2 className="text-lg font-bold text-foreground">Đăng tin tuyển dụng / Thực tập</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Tin tuyển dụng sẽ được hiển thị công khai tới toàn thể sinh viên sau khi duyệt.
              </p>

              {postSuccess ? (
                <div className="my-8 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 p-6 text-center text-emerald-600">
                  <CheckCircle2 className="mx-auto size-12 mb-2" />
                  <h3 className="font-bold text-sm">Đăng tin thành công!</h3>
                  <p className="text-xs mt-1">Tin tuyển dụng đã được lưu vào hệ thống.</p>
                </div>
              ) : (
                <form onSubmit={handlePostJob} className="space-y-4 mt-6 text-xs">
                  <div>
                    <label className="font-semibold text-foreground block mb-1">Tiêu đề vị trí tuyển dụng *</label>
                    <input
                      type="text"
                      required
                      placeholder="VD: Frontend React Developer (Fresher / Junior)"
                      value={postFormData.title}
                      onChange={(e) => setPostFormData({ ...postFormData, title: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="font-semibold text-foreground block mb-1">Hình thức *</label>
                      <select
                        value={postFormData.job_type}
                        onChange={(e) => setPostFormData({ ...postFormData, job_type: e.target.value as any })}
                        className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                      >
                        <option value="full_time">Toàn thời gian</option>
                        <option value="part_time">Bán thời gian</option>
                        <option value="internship">Thực tập</option>
                      </select>
                    </div>

                    <div>
                      <label className="font-semibold text-foreground block mb-1">Tên Công ty / Đơn vị *</label>
                      <input
                        type="text"
                        required
                        placeholder="VD: VNG, FPT, Viettel..."
                        value={postFormData.company_name}
                        onChange={(e) => setPostFormData({ ...postFormData, company_name: e.target.value })}
                        className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="font-semibold text-foreground block mb-1">Địa điểm làm việc</label>
                      <input
                        type="text"
                        placeholder="VD: Hà Nội / TP.HCM / Remote"
                        value={postFormData.location}
                        onChange={(e) => setPostFormData({ ...postFormData, location: e.target.value })}
                        className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                      />
                    </div>

                    <div>
                      <label className="font-semibold text-foreground block mb-1">Mức lương tối đa (VNĐ)</label>
                      <input
                        type="number"
                        placeholder="VD: 15000000"
                        value={postFormData.salary_max || ""}
                        onChange={(e) => setPostFormData({ ...postFormData, salary_max: Number(e.target.value) || undefined })}
                        className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="font-semibold text-foreground block mb-1">Mô tả công việc *</label>
                    <textarea
                      rows={4}
                      required
                      placeholder="Trách nhiệm công việc, công nghệ sử dụng..."
                      value={postFormData.description}
                      onChange={(e) => setPostFormData({ ...postFormData, description: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div>
                    <label className="font-semibold text-foreground block mb-1">Yêu cầu ứng viên</label>
                    <textarea
                      rows={3}
                      placeholder="Kỹ năng, năm sinh viên, chứng chỉ..."
                      value={postFormData.requirements}
                      onChange={(e) => setPostFormData({ ...postFormData, requirements: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div className="pt-3 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setShowPostModal(false)}
                      className="rounded-xl border border-border px-4 py-2 text-xs font-semibold"
                    >
                      Hủy
                    </button>
                    <button
                      type="submit"
                      disabled={posting}
                      className="rounded-xl bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                      {posting ? "Đang đăng..." : "Đăng tin"}
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
