"use client";

import {
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  MapPin,
  Mic,
  Plus,
  Radio,
  Tag,
  Users,
  Video,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Footer } from "@/components/footer";
import { Navbar } from "@/components/navbar";
import { useAuth } from "@/hooks/use-auth";
import {
  type EventCreate,
  type EventRead,
  type EventType,
  type RegistrationType,
  cancelEventRegistration,
  createEvent,
  listEvents,
  registerEvent,
} from "@/lib/api/events";

export default function EventsPage() {
  const { user, isAuthenticated } = useAuth();
  const [events, setEvents] = useState<EventRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [eventType, setEventType] = useState<string>("");
  const [selectedEvent, setSelectedEvent] = useState<EventRead | null>(null);

  // Register Modal
  const [registeringEvent, setRegisteringEvent] = useState<EventRead | null>(null);
  const [regType, setRegType] = useState<RegistrationType>("attendee");
  const [speakerTopic, setSpeakerTopic] = useState("");
  const [speakerBio, setSpeakerBio] = useState("");
  const [registering, setRegistering] = useState(false);
  const [regSuccess, setRegSuccess] = useState(false);

  // Create Event Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createFormData, setCreateFormData] = useState<EventCreate>({
    title: "",
    event_type: "talkshow",
    description: "",
    location: "",
    is_online: false,
    online_link: "",
    start_time: "",
    end_time: "",
    max_attendees: 100,
    agenda: "",
  });
  const [creating, setCreating] = useState(false);
  const [createSuccess, setCreateSuccess] = useState(false);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listEvents({
        event_type: eventType || undefined,
        limit: 50,
      });
      setEvents(res.items);
    } catch (err) {
      console.error(err);
      setError("Không thể tải danh sách sự kiện.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [eventType]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!registeringEvent) return;
    try {
      setRegistering(true);
      await registerEvent(registeringEvent.id, {
        registration_type: regType,
        speaker_topic: regType === "speaker" ? speakerTopic : undefined,
        speaker_bio: regType === "speaker" ? speakerBio : undefined,
      });
      setRegSuccess(true);
      setTimeout(() => {
        setRegSuccess(false);
        setRegisteringEvent(null);
        fetchEvents();
      }, 1500);
    } catch (err) {
      alert("Đăng ký thất bại. Bạn cần đăng nhập tài khoản trước khi đăng ký.");
    } finally {
      setRegistering(false);
    }
  };

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreating(true);
      await createEvent(createFormData);
      setCreateSuccess(true);
      setTimeout(() => {
        setCreateSuccess(false);
        setShowCreateModal(false);
        fetchEvents();
      }, 1500);
    } catch (err) {
      alert("Tạo sự kiện thất bại. Chỉ quản trị viên mới có quyền tạo sự kiện.");
    } finally {
      setCreating(false);
    }
  };

  const getEventTypeBadge = (type: EventType) => {
    switch (type) {
      case "anniversary":
        return <span className="bg-amber-500/10 text-amber-600 border border-amber-500/20 rounded-full px-2.5 py-0.5 text-[10px] font-semibold">Lễ kỷ niệm</span>;
      case "talkshow":
        return <span className="bg-blue-500/10 text-blue-600 border border-blue-500/20 rounded-full px-2.5 py-0.5 text-[10px] font-semibold">Talkshow chia sẻ</span>;
      case "workshop":
        return <span className="bg-purple-500/10 text-purple-600 border border-purple-500/20 rounded-full px-2.5 py-0.5 text-[10px] font-semibold">Workshop kỹ thuật</span>;
      case "seminar":
        return <span className="bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 rounded-full px-2.5 py-0.5 text-[10px] font-semibold">Hội thảo Seminar</span>;
      default:
        return <span className="bg-muted text-muted-foreground rounded-full px-2.5 py-0.5 text-[10px] font-semibold">Sự kiện khác</span>;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Navbar />

      <main className="flex-1 py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-xs font-semibold text-violet-600 mb-3">
              <Calendar className="size-4" />
              Sự kiện & Diễn đàn Giao lưu
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
              Giao lưu & Kết nối Tri thức
            </h1>
            <p className="mt-2 text-sm text-muted-foreground max-w-2xl">
              Tham gia các buổi lễ kỷ niệm, talkshow hướng nghiệp và workshop công nghệ cùng các thế hệ cựu sinh viên tài năng.
            </p>
          </div>

          {isAuthenticated && user?.role === "admin" && (
            <button
              type="button"
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-xs font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
            >
              <Plus className="size-4" />
              Tạo sự kiện mới
            </button>
          )}
        </div>

        {/* Filter */}
        <div className="rounded-2xl border border-border bg-card p-4 sm:p-5 shadow-xs mb-8 flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold text-muted-foreground mr-1">Lọc theo:</span>
            {[
              { id: "", label: "Tất cả" },
              { id: "talkshow", label: "Talkshow" },
              { id: "workshop", label: "Workshop" },
              { id: "anniversary", label: "Kỷ niệm" },
              { id: "seminar", label: "Seminar" },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setEventType(f.id)}
                className={`rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                  eventType === f.id
                    ? "bg-primary text-primary-foreground shadow-xs"
                    : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <p className="text-xs text-muted-foreground">
            Có <span className="font-semibold text-foreground">{events.length}</span> sự kiện
          </p>
        </div>

        {/* Events Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-64 rounded-2xl border border-border bg-card/60 animate-pulse p-6" />
            ))}
          </div>
        ) : events.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border p-12 text-center">
            <Calendar className="mx-auto size-10 text-muted-foreground mb-3" />
            <h3 className="text-sm font-semibold text-foreground">Chưa có sự kiện nào</h3>
            <p className="text-xs text-muted-foreground mt-1">Các sự kiện sắp tới sẽ sớm được công bố.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((ev) => (
              <div
                key={ev.id}
                className="group rounded-2xl border border-border/80 bg-card p-6 shadow-xs hover:shadow-md hover:border-primary/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    {getEventTypeBadge(ev.event_type)}
                    {ev.is_online ? (
                      <span className="flex items-center gap-1 rounded-full bg-blue-500/10 text-blue-600 px-2 py-0.5 text-[10px] font-semibold">
                        <Video className="size-3" /> Trực tuyến
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 rounded-full bg-muted text-muted-foreground px-2 py-0.5 text-[10px] font-semibold">
                        <MapPin className="size-3" /> Trực tiếp
                      </span>
                    )}
                  </div>

                  <h3
                    onClick={() => setSelectedEvent(ev)}
                    className="font-bold text-base text-foreground group-hover:text-primary transition-colors cursor-pointer line-clamp-2"
                  >
                    {ev.title}
                  </h3>

                  <div className="mt-4 space-y-2 text-xs text-muted-foreground">
                    <div className="flex items-center gap-2 text-foreground font-medium">
                      <Clock className="size-3.5 text-primary shrink-0" />
                      <span>{new Date(ev.start_time).toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" })}</span>
                    </div>

                    {ev.location && (
                      <div className="flex items-center gap-2">
                        <MapPin className="size-3.5 shrink-0 text-muted-foreground" />
                        <span className="truncate">{ev.location}</span>
                      </div>
                    )}

                    <div className="flex items-center gap-3 pt-1">
                      <span className="flex items-center gap-1 text-[11px]">
                        <Users className="size-3 text-muted-foreground" />
                        {ev.attendee_count} người tham dự
                      </span>
                      {ev.speaker_count > 0 && (
                        <span className="flex items-center gap-1 text-[11px] text-violet-600 font-semibold">
                          <Mic className="size-3" />
                          {ev.speaker_count} diễn giả
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-border/60 flex items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => setSelectedEvent(ev)}
                    className="text-xs font-semibold text-muted-foreground hover:text-foreground"
                  >
                    Xem lịch trình
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setRegisteringEvent(ev);
                    }}
                    className="rounded-xl bg-primary px-3.5 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs"
                  >
                    Đăng ký tham gia
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal Chi tiết Event */}
        {selectedEvent && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="relative w-full max-w-2xl rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setSelectedEvent(null)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <div className="mb-4">{getEventTypeBadge(selectedEvent.event_type)}</div>
              <h2 className="text-xl font-bold text-foreground">{selectedEvent.title}</h2>

              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 rounded-2xl bg-muted/30 p-4 text-xs">
                <div>
                  <span className="text-muted-foreground">Thời gian bắt đầu:</span>
                  <p className="font-semibold text-foreground mt-0.5">
                    {new Date(selectedEvent.start_time).toLocaleString("vi-VN")}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Địa điểm / Nền tảng:</span>
                  <p className="font-semibold text-foreground mt-0.5">
                    {selectedEvent.is_online ? "Trực tuyến" : selectedEvent.location || "Đang cập nhật"}
                  </p>
                </div>
              </div>

              {selectedEvent.description && (
                <div className="mt-6">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">Nội dung chi tiết</h4>
                  <div className="rounded-xl bg-muted/20 p-4 border border-border/40 text-xs text-foreground whitespace-pre-line leading-relaxed">
                    {selectedEvent.description}
                  </div>
                </div>
              )}

              {selectedEvent.agenda && (
                <div className="mt-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1.5">Lịch trình & Diễn giả</h4>
                  <div className="rounded-xl bg-muted/20 p-4 border border-border/40 text-xs text-foreground whitespace-pre-line leading-relaxed">
                    {selectedEvent.agenda}
                  </div>
                </div>
              )}

              <div className="mt-8 pt-4 border-t border-border flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedEvent(null)}
                  className="rounded-xl border border-border px-4 py-2 text-xs font-semibold"
                >
                  Đóng
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setRegisteringEvent(selectedEvent);
                    setSelectedEvent(null);
                  }}
                  className="rounded-xl bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground"
                >
                  Đăng ký tham gia
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal Đăng ký tham gia */}
        {registeringEvent && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
            <div className="relative w-full max-w-lg rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl">
              <button
                onClick={() => setRegisteringEvent(null)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <h2 className="text-lg font-bold text-foreground">Đăng ký tham gia sự kiện</h2>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{registeringEvent.title}</p>

              {regSuccess ? (
                <div className="my-8 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 p-6 text-center text-emerald-600">
                  <CheckCircle2 className="mx-auto size-12 mb-2" />
                  <h3 className="font-bold text-sm">Đăng ký thành công!</h3>
                  <p className="text-xs mt-1">Thông tin tham gia đã được ghi nhận vào danh sách.</p>
                </div>
              ) : (
                <form onSubmit={handleRegister} className="space-y-4 mt-6 text-xs">
                  <div>
                    <label className="font-semibold text-foreground block mb-2">Vai trò tham gia</label>
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => setRegType("attendee")}
                        className={`rounded-xl border p-3 text-center transition-all ${
                          regType === "attendee"
                            ? "border-primary bg-primary/10 text-primary font-bold shadow-xs"
                            : "border-border text-muted-foreground hover:bg-muted"
                        }`}
                      >
                        <Users className="mx-auto size-5 mb-1" />
                        <span>Người tham dự (Attendee)</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setRegType("speaker")}
                        className={`rounded-xl border p-3 text-center transition-all ${
                          regType === "speaker"
                            ? "border-violet-500 bg-violet-500/10 text-violet-600 font-bold shadow-xs"
                            : "border-border text-muted-foreground hover:bg-muted"
                        }`}
                      >
                        <Mic className="mx-auto size-5 mb-1" />
                        <span>Diễn giả chia sẻ (Speaker)</span>
                      </button>
                    </div>
                  </div>

                  {regType === "speaker" && (
                    <div className="space-y-3 pt-2">
                      <div>
                        <label className="font-semibold text-foreground block mb-1">Chủ đề dự kiến chia sẻ *</label>
                        <input
                          type="text"
                          required
                          placeholder="VD: Kinh nghiệm phỏng vấn Tech Lead, Xu hướng Cloud 2026..."
                          value={speakerTopic}
                          onChange={(e) => setSpeakerTopic(e.target.value)}
                          className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                        />
                      </div>

                      <div>
                        <label className="font-semibold text-foreground block mb-1">Giới thiệu ngắn về kinh nghiệm</label>
                        <textarea
                          rows={3}
                          placeholder="Chức danh hiện tại, công ty, dự án tiêu biểu..."
                          value={speakerBio}
                          onChange={(e) => setSpeakerBio(e.target.value)}
                          className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                        />
                      </div>
                    </div>
                  )}

                  <div className="pt-3 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => setRegisteringEvent(null)}
                      className="rounded-xl border border-border px-4 py-2 text-xs font-semibold"
                    >
                      Hủy
                    </button>
                    <button
                      type="submit"
                      disabled={registering}
                      className="rounded-xl bg-primary px-5 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
                    >
                      {registering ? "Đang xử lý..." : "Xác nhận đăng ký"}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}

        {/* Modal Tạo sự kiện */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto">
            <div className="relative w-full max-w-xl rounded-3xl border border-border bg-card p-6 sm:p-8 shadow-2xl max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setShowCreateModal(false)}
                className="absolute right-5 top-5 rounded-full p-2 text-muted-foreground hover:bg-muted"
              >
                <X className="size-5" />
              </button>

              <h2 className="text-lg font-bold text-foreground">Tạo sự kiện mới</h2>
              <p className="text-xs text-muted-foreground mt-0.5">Sự kiện sẽ được công bố trực tiếp tới sinh viên và cựu sinh viên.</p>

              {createSuccess ? (
                <div className="my-8 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 p-6 text-center text-emerald-600">
                  <CheckCircle2 className="mx-auto size-12 mb-2" />
                  <h3 className="font-bold text-sm">Tạo sự kiện thành công!</h3>
                </div>
              ) : (
                <form onSubmit={handleCreateEvent} className="space-y-4 mt-6 text-xs">
                  <div>
                    <label className="font-semibold text-foreground block mb-1">Tên sự kiện *</label>
                    <input
                      type="text"
                      required
                      placeholder="VD: Talkshow: Hành trình từ Sinh viên đến Senior Engineer"
                      value={createFormData.title}
                      onChange={(e) => setCreateFormData({ ...createFormData, title: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="font-semibold text-foreground block mb-1">Loại sự kiện</label>
                      <select
                        value={createFormData.event_type}
                        onChange={(e) => setCreateFormData({ ...createFormData, event_type: e.target.value as any })}
                        className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                      >
                        <option value="talkshow">Talkshow</option>
                        <option value="workshop">Workshop</option>
                        <option value="anniversary">Lễ kỷ niệm</option>
                        <option value="seminar">Hội thảo Seminar</option>
                        <option value="other">Khác</option>
                      </select>
                    </div>

                    <div>
                      <label className="font-semibold text-foreground block mb-1">Thời gian bắt đầu *</label>
                      <input
                        type="datetime-local"
                        required
                        value={createFormData.start_time}
                        onChange={(e) => setCreateFormData({ ...createFormData, start_time: e.target.value })}
                        className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="checkbox"
                      id="is_online"
                      checked={createFormData.is_online}
                      onChange={(e) => setCreateFormData({ ...createFormData, is_online: e.target.checked })}
                      className="rounded"
                    />
                    <label htmlFor="is_online" className="font-semibold text-foreground cursor-pointer">
                      Sự kiện trực tuyến (Google Meet / Zoom)
                    </label>
                  </div>

                  {createFormData.is_online ? (
                    <div>
                      <label className="font-semibold text-foreground block mb-1">Link phòng họp trực tuyến</label>
                      <input
                        type="url"
                        placeholder="https://meet.google.com/..."
                        value={createFormData.online_link || ""}
                        onChange={(e) => setCreateFormData({ ...createFormData, online_link: e.target.value })}
                        className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                  ) : (
                    <div>
                      <label className="font-semibold text-foreground block mb-1">Địa điểm tổ chức</label>
                      <input
                        type="text"
                        placeholder="VD: Hội trường lớn A2, Trường Đại học..."
                        value={createFormData.location || ""}
                        onChange={(e) => setCreateFormData({ ...createFormData, location: e.target.value })}
                        className="w-full rounded-xl border border-border bg-background py-2 px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                      />
                    </div>
                  )}

                  <div>
                    <label className="font-semibold text-foreground block mb-1">Mô tả sự kiện</label>
                    <textarea
                      rows={3}
                      placeholder="Mục đích, đối tượng tham gia, nội dung chính..."
                      value={createFormData.description || ""}
                      onChange={(e) => setCreateFormData({ ...createFormData, description: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>

                  <div>
                    <label className="font-semibold text-foreground block mb-1">Lịch trình chi tiết (Agenda)</label>
                    <textarea
                      rows={3}
                      placeholder="8:00 - Khai mạc&#10;8:30 - Diễn giả chia sẻ&#10;10:00 - Q&A..."
                      value={createFormData.agenda || ""}
                      onChange={(e) => setCreateFormData({ ...createFormData, agenda: e.target.value })}
                      className="w-full rounded-xl border border-border bg-background p-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
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
                      {creating ? "Đang lưu..." : "Tạo sự kiện"}
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
