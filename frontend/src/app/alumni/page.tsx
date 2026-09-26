"use client";

import {
  Briefcase,
  Building,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  GraduationCap,
  Mail,
  MapPin,
  Phone,
  Search,
  SlidersHorizontal,
  UserCheck,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Footer } from "@/components/footer";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/hooks/use-auth";
import {
  type AlumniProfileRead,
  getAlumniDetail,
  listAlumni,
  listCompanies,
} from "@/lib/api/alumni";

export default function AlumniDirectoryPage() {
  const { user } = useAuth();
  const [alumniList, setAlumniList] = useState<AlumniProfileRead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [major, setMajor] = useState("");
  const [graduationYear, setGraduationYear] = useState<string>("");
  const [company, setCompany] = useState("");
  const [selectedAlumni, setSelectedAlumni] = useState<AlumniProfileRead | null>(null);

  const fetchAlumni = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listAlumni({
        search: search || undefined,
        major: major || undefined,
        graduation_year: graduationYear ? Number(graduationYear) : undefined,
        company: company || undefined,
        limit: 50,
      });
      setAlumniList(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
      setError("Không thể tải danh sách cựu sinh viên. Vui lòng thử lại sau.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlumni();
  }, [major, graduationYear]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchAlumni();
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <main className="flex-1 py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs font-semibold text-blue-600 mb-3">
            <GraduationCap className="size-4" />
            Cơ sở dữ liệu Cựu sinh viên
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
            Mạng lưới Cựu sinh viên Khoa CNTT
          </h1>
          <p className="mt-2 text-sm text-muted-foreground max-w-2xl">
            Tra cứu thông tin, kết nối nghề nghiệp và tìm kiếm cựu sinh viên các thế hệ qua chuyên ngành, niên khóa và đơn vị công tác.
          </p>
        </div>

        {/* Filter & Search Bar */}
        <div className="rounded-2xl border border-border bg-card p-4 sm:p-6 shadow-xs mb-8">
          <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Tìm theo Tên hoặc MSSV..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-xl border border-border bg-background py-2 pl-9 pr-4 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>

            <div>
              <select
                value={major}
                onChange={(e) => setMajor(e.target.value)}
                aria-label="Chọn chuyên ngành"
                className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">Tất cả chuyên ngành</option>
                <option value="Công nghệ thông tin">Công nghệ thông tin</option>
                <option value="Khoa học máy tính">Khoa học máy tính</option>
                <option value="Kỹ thuật phần mềm">Kỹ thuật phần mềm</option>
                <option value="Hệ thống thông tin">Hệ thống thông tin</option>
                <option value="An toàn thông tin">An toàn thông tin</option>
                <option value="Trí tuệ nhân tạo">Trí tuệ nhân tạo & Data</option>
              </select>
            </div>

            <div>
              <select
                value={graduationYear}
                onChange={(e) => setGraduationYear(e.target.value)}
                aria-label="Chọn năm tốt nghiệp"
                className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="">Tất cả năm tốt nghiệp</option>
                {[2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015].map((y) => (
                  <option key={y} value={y}>
                    Khóa tốt nghiệp {y}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Công ty / Đơn vị..."
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="flex-1 rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
              <button
                type="submit"
                className="rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shrink-0 shadow-xs"
              >
                Lọc
              </button>
            </div>
          </form>
        </div>

        {/* Results Info */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs text-muted-foreground">
            Hiển thị <span className="font-semibold text-foreground">{alumniList.length}</span> / {total} hồ sơ cựu sinh viên
          </p>
        </div>

        {/* Alumni Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 rounded-2xl border border-border bg-card/60 animate-pulse p-6" />
            ))}
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-destructive/20 bg-destructive/5 p-8 text-center">
            <p className="text-sm text-destructive font-medium">{error}</p>
            <button
              onClick={fetchAlumni}
              className="mt-4 px-4 py-2 rounded-xl bg-primary text-xs font-semibold text-primary-foreground"
            >
              Thử lại
            </button>
          </div>
        ) : alumniList.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border p-12 text-center">
            <GraduationCap className="mx-auto size-10 text-muted-foreground mb-3" />
            <h3 className="text-sm font-semibold text-foreground">Không tìm thấy cựu sinh viên phù hợp</h3>
            <p className="text-xs text-muted-foreground mt-1">
              Thử điều chỉnh lại bộ lọc hoặc từ khóa tìm kiếm.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {alumniList.map((alumnus) => (
              <div
                key={alumnus.id}
                onClick={() => setSelectedAlumni(alumnus)}
                className="group relative rounded-2xl border border-border/80 bg-card p-6 shadow-xs hover:shadow-md hover:border-primary/40 transition-all cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3">
                      <div className="flex size-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/10 to-indigo-500/10 text-primary font-bold text-base border border-primary/20">
                        {alumnus.full_name ? alumnus.full_name.charAt(0) : "A"}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <h3 className="font-bold text-sm text-foreground group-hover:text-primary transition-colors">
                            {alumnus.full_name}
                          </h3>
                          {alumnus.is_verified && (
                            <CheckCircle2 className="size-4 text-emerald-500 shrink-0" />
                          )}
                        </div>
                        <span className="text-[11px] text-muted-foreground font-mono">
                          MSSV: {alumnus.student_id}
                        </span>
                      </div>
                    </div>
                    {alumnus.graduation_year && (
                      <span className="rounded-full bg-muted px-2.5 py-0.5 text-[11px] font-semibold text-foreground/80 shrink-0">
                        Khóa {alumnus.graduation_year}
                      </span>
                    )}
                  </div>

                  <div className="space-y-2 text-xs text-muted-foreground">
                    {alumnus.current_job_title && (
                      <div className="flex items-center gap-2 text-foreground font-medium">
                        <Briefcase className="size-3.5 text-primary shrink-0" />
                        <span className="truncate">{alumnus.current_job_title}</span>
                      </div>
                    )}
                    {alumnus.company_name && (
                      <div className="flex items-center gap-2">
                        <Building className="size-3.5 text-muted-foreground shrink-0" />
                        <span className="truncate">{alumnus.company_name}</span>
                      </div>
                    )}
                    {alumnus.major && (
                      <div className="flex items-center gap-2">
                        <GraduationCap className="size-3.5 text-muted-foreground shrink-0" />
                        <span className="truncate">Ngành: {alumnus.major}</span>
                      </div>
                    )}
                  </div>

                  {alumnus.skills?.items && alumnus.skills.items.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-1.5">
                      {alumnus.skills.items.slice(0, 4).map((skill, idx) => (
                        <span
                          key={idx}
                          className="rounded-md bg-muted px-2 py-0.5 text-[10px] font-medium text-foreground/70"
                        >
                          {skill}
                        </span>
                      ))}
                      {alumnus.skills.items.length > 4 && (
                        <span className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                          +{alumnus.skills.items.length - 4}
                        </span>
                      )}
                    </div>
                  )}
                </div>

                <div className="mt-5 pt-4 border-t border-border/60 flex items-center justify-between text-xs text-primary font-semibold">
                  <span>Xem hồ sơ chi tiết</span>
                  <ChevronRight className="size-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal Chi tiết Cựu sinh viên */}
        {selectedAlumni && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="relative w-full max-w-2xl rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl">
              <button
                onClick={() => setSelectedAlumni(null)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <X className="size-5" />
              </button>

              <div className="flex items-start gap-4 mb-6">
                <div className="flex size-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white font-extrabold text-2xl shadow-md">
                  {selectedAlumni.full_name ? selectedAlumni.full_name.charAt(0) : "A"}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold text-foreground">{selectedAlumni.full_name}</h2>
                    {selectedAlumni.is_verified && (
                      <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[11px] font-semibold text-emerald-600">
                        <CheckCircle2 className="size-3" /> Đã xác thực
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">MSSV: {selectedAlumni.student_id}</p>
                  <p className="text-xs font-semibold text-primary mt-1">
                    {selectedAlumni.current_job_title || "Cựu sinh viên"}
                    {selectedAlumni.company_name ? ` — ${selectedAlumni.company_name}` : ""}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 rounded-2xl border border-border/80 bg-muted/30 p-4 text-xs mb-6">
                <div>
                  <span className="text-muted-foreground">Chuyên ngành:</span>
                  <p className="font-semibold text-foreground mt-0.5">{selectedAlumni.major || "Chưa cập nhật"}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Năm tốt nghiệp:</span>
                  <p className="font-semibold text-foreground mt-0.5">{selectedAlumni.graduation_year || "Chưa cập nhật"}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Địa điểm công tác:</span>
                  <p className="font-semibold text-foreground mt-0.5">{selectedAlumni.work_location || "Chưa cập nhật"}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Lĩnh vực:</span>
                  <p className="font-semibold text-foreground mt-0.5">{selectedAlumni.job_field || "Công nghệ thông tin"}</p>
                </div>
              </div>

              {selectedAlumni.bio && (
                <div className="mb-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">Giới thiệu bản thân</h4>
                  <p className="text-xs text-foreground leading-relaxed bg-muted/20 p-3 rounded-xl border border-border/40">
                    {selectedAlumni.bio}
                  </p>
                </div>
              )}

              {selectedAlumni.achievements && (
                <div className="mb-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">Thành tích & Đóng góp</h4>
                  <p className="text-xs text-foreground leading-relaxed bg-muted/20 p-3 rounded-xl border border-border/40">
                    {selectedAlumni.achievements}
                  </p>
                </div>
              )}

              {selectedAlumni.skills?.items && selectedAlumni.skills.items.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Kỹ năng chuyên môn</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedAlumni.skills.items.map((skill, idx) => (
                      <span key={idx} className="rounded-lg bg-primary/10 border border-primary/20 px-2.5 py-1 text-xs font-medium text-primary">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-4 border-t border-border flex flex-wrap items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-4 text-muted-foreground">
                  {selectedAlumni.email && (
                    <div className="flex items-center gap-1.5">
                      <Mail className="size-3.5 text-primary" />
                      <span>{selectedAlumni.email}</span>
                    </div>
                  )}
                  {selectedAlumni.phone && (
                    <div className="flex items-center gap-1.5">
                      <Phone className="size-3.5 text-primary" />
                      <span>{selectedAlumni.phone}</span>
                    </div>
                  )}
                </div>

                {selectedAlumni.linkedin_url && (
                  <a
                    href={selectedAlumni.linkedin_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-xl bg-blue-600 px-3 py-1.5 font-semibold text-white hover:bg-blue-700 transition-colors"
                  >
                    <ExternalLink className="size-3.5" />
                    LinkedIn
                  </a>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
