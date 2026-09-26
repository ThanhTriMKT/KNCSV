# Alumni Portal — Cổng thông tin kết nối Cựu sinh viên & Nhà trường

> Spec kỹ thuật chính thức cho dự án Alumni Portal

## 1. Tên đề tài

**"Xây dựng Cổng thông tin kết nối Cựu sinh viên - Khoa - Sinh viên hỗ trợ Tuyển dụng, Sự kiện và Hỗ trợ tài chính"**

---

## 2. Phân quyền hệ thống (Roles)

| Role | Mô tả |
|------|-------|
| `admin` | Quản trị viên (Khoa) — toàn quyền |
| `alumni` | Cựu sinh viên đã đăng ký tài khoản |
| `student` | Sinh viên đang học |

---

## 3. Luồng nghiệp vụ chính

### Module 1 — Quản lý Hồ sơ Cựu sinh viên
```
[Admin upload Excel/PDF danh sách CSV]
    ↓
[Parser trích xuất → Preview danh sách: Thêm mới / Cập nhật]
    ↓
[Admin xác nhận → Lưu vào alumni_profiles]
    ↓
[CSV tự đăng ký tài khoản → Link với hồ sơ]
```

### Module 2 — Tuyển dụng & Thực tập
```
[Alumni/Admin tạo tin tuyển dụng]
    ↓
[Admin duyệt tin]
    ↓
[Sinh viên tìm kiếm, lọc, nộp hồ sơ]
```

### Module 3 — Sự kiện & Talkshow
```
[Admin tạo sự kiện (Lễ kỷ niệm / Talkshow / Hội thảo)]
    ↓
[CSV đăng ký tham dự / đăng ký làm Diễn giả]
[Sinh viên đăng ký tham dự]
    ↓
[Admin điểm danh, quản lý danh sách]
```

### Module 4 — Khảo sát Việc làm Sau Tốt nghiệp
```
[Admin tạo biểu mẫu khảo sát]
    ↓
[CSV nhận thông báo → điền khảo sát]
    ↓
[Dashboard thống kê tự động: tỷ lệ việc làm, đúng/trái ngành]
```

### Module 5 — Hỗ trợ Tài chính & Học bổng
```
[CSV/Doanh nghiệp đăng ký đóng góp quỹ]
    ↓
[Sinh viên nộp hồ sơ xin hỗ trợ tài chính]
    ↓
[Admin xét duyệt → quản lý giải ngân]
```

---

## 4. Database Schema (ERD)

### Bảng chính
- `users` — tài khoản đăng nhập (roles: admin, alumni, student)
- `alumni_profiles` — hồ sơ đầy đủ của CSV (kể cả chưa có tài khoản)
- `companies` — đơn vị công tác
- `job_posts` — tin tuyển dụng / thực tập
- `job_applications` — hồ sơ ứng tuyển của sinh viên
- `events` — sự kiện, talkshow, lễ kỷ niệm
- `event_registrations` — đăng ký tham dự sự kiện
- `surveys` — biểu mẫu khảo sát
- `survey_questions` — câu hỏi trong khảo sát
- `survey_responses` — câu trả lời của CSV
- `financial_contributions` — đóng góp quỹ học bổng
- `aid_applications` — đơn xin hỗ trợ tài chính

---

## 5. Kiến trúc hệ thống

```
[Next.js Frontend] ──HTTP──▶ [FastAPI Backend]
                                    │
                              [PostgreSQL DB]
```

---

## 6. Tech Stack

### Frontend — Next.js 16
| Nhu cầu | Thư viện |
|---------|---------|
| UI | shadcn/ui + Tailwind CSS |
| Form & Validate | react-hook-form + zod |
| Data fetching | TanStack Query |
| Charts | Recharts |
| Icons | lucide-react |

### Backend — Python (FastAPI)
| Nhu cầu | Thư viện | Vai trò |
|---------|---------|---------|
| Web Framework | fastapi + uvicorn | REST API async |
| ORM | sqlalchemy (async) + asyncpg + alembic | Schema & migration |
| Auth | fastapi-users[sqlalchemy] | JWT, roles |
| File Parsing | pandas + openpyxl + pypdf | Import Excel/PDF |
| Email | resend | Thông báo khảo sát |
| DevOps | Docker + Docker Compose | Container hóa |
