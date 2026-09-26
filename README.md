# KNCSV — Cổng Thông Tin Quản Lý & Kết Nối Cựu Sinh Viên
### Khoa Công Nghệ Thông Tin — Trường Đại Học Đà Lạt (DLU)

Hệ thống quản lý, kết nối và khảo sát cựu sinh viên toàn diện dành cho Khoa Công nghệ Thông tin - Trường Đại học Đà Lạt. Dự án giải quyết trọn vẹn bài toán quản lý dữ liệu cựu sinh viên, phục vụ công tác kiểm định chất lượng đào tạo, kết nối tuyển dụng doanh nghiệp và hỗ trợ học bổng sinh viên.

---

## 🌟 Tính Năng & Các Phân Hệ Nghiệp Vụ Chính

### 1. 🎓 Quản lý Cơ sở dữ liệu Cựu sinh viên (`/alumni`)
- Tra cứu hồ sơ cựu sinh viên theo niên khóa, chuyên ngành, đơn vị công tác, chức vụ và kỹ năng.
- Chế độ hiển thị danh sách dạng Card trực quan hoặc Table chuyên nghiệp.
- Tính năng **Import dữ liệu sinh viên từ file Excel** với bộ lọc xem trước (preview) tự động dành cho quản trị viên khoa.
- Cho phép cựu sinh viên cập nhật thông tin cá nhân và tình trạng công tác hiện tại.

### 2. 📋 Khảo sát Tình trạng Việc làm sau Tốt nghiệp (`/surveys`)
- Thu thập phản hồi về tỷ lệ có việc làm, mức thu nhập trung bình, lĩnh vực công tác và mức độ phù hợp với chương trình đào tạo của Khoa CNTT.
- Hỗ trợ đa dạng loại câu hỏi: văn bản, trắc nghiệm 1 lựa chọn, trắc nghiệm nhiều lựa chọn, thang điểm đánh giá (Rating scale).
- Báo cáo thống kê trực quan với biểu đồ phân bố phục vụ công tác **kiểm định chất lượng giáo dục**.

### 3. 💼 Tuyển dụng & Giới thiệu Việc làm (`/jobs`)
- Cầu nối tuyển dụng trực tiếp giữa Cựu sinh viên, Doanh nghiệp đối tác và Sinh viên.
- Đăng tin tuyển dụng thực tập (Internship), Fresher, Junior, Mid/Senior trong ngành CNTT.
- Ứng tuyển và theo dõi hồ sơ ứng viên trực tiếp trên hệ thống.

### 4. 🤝 Quỹ Học bổng & Hỗ trợ Tài chính (`/financial-aid`)
- Huy động nguồn lực đóng góp từ cộng đồng cựu sinh viên và các đơn vị hảo tâm.
- Sinh viên có hoàn cảnh khó khăn nộp đơn xin cấp học bổng và hỗ trợ tài chính trực tuyến.
- Quy trình xét duyệt minh bạch: Tiếp nhận đơn -> Ban chủ nhiệm duyệt -> Giải ngân.
- Thống kê tổng quỹ, số lượt đóng góp và danh sách vinh danh các nhà hảo tâm.

### 5. 📅 Tổ chức Sự kiện & Talkshow Giao lưu (`/events`)
- Lịch tổ chức các ngày lễ kỷ niệm, chuỗi talkshow định hướng nghề nghiệp, workshop công nghệ.
- Đăng ký tham gia sự kiện và đăng ký vai trò diễn giả (Speaker) dành cho cựu sinh viên.
- Quản lý danh sách người tham dự và điểm danh trực tuyến.

### 6. 🚀 Trợ lý Hướng nghiệp & Phát triển Kỹ năng (`/career-advisor`)
- Bản đồ lộ trình nghề nghiệp chuẩn hoá theo các chuyên ngành trọng điểm của Khoa CNTT:
  - **Kỹ thuật Phần mềm (Software Engineering)**
  - **Trí tuệ Nhân tạo & Khoa học Dữ liệu (AI & Data Science)**
  - **DevOps, Điện toán Đám mây & An toàn Thông tin (Cybersecurity)**
- Ngân hàng câu hỏi phỏng vấn thực tế theo từng lĩnh vực.
- Bộ mẫu CV & Cover Letter chuẩn cho sinh viên IT.
- Thống kê tổng quan thị trường việc làm từ dữ liệu thực tế của Alumni Portal.

### 7. 🛡️ Phân hệ Quản trị Toàn diện (`/admin`)
- Dashboard tổng hợp thống kê toàn khoa (số lượng cựu sinh viên, tỷ lệ việc làm, quy mô quỹ học bổng, sự kiện).
- Quản lý tài khoản người dùng, phân quyền (Admin, Alumni, Student).
- Kiểm duyệt tin tuyển dụng, phê duyệt hồ sơ học bổng, quản lý khảo sát.

---

## 🛠️ Công Nghệ Sử Dụng (Tech Stack)

### Frontend
- **Framework:** [Next.js](https://nextjs.org/) (App Router, Turbopack)
- **Ngôn ngữ:** TypeScript
- **Styling:** Tailwind CSS, Lucide Icons, Glassmorphism UI
- **Components:** Radix UI primitives, Custom animated components

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Package & Dependency Manager:** [uv](https://docs.astral.sh/uv/)
- **Cơ sở dữ liệu:** SQLite / PostgreSQL (hỗ trợ chuyển đổi linh hoạt qua async SQLAlchemy)
- **ORM & Migrations:** SQLAlchemy 2.0 (Asyncio) + Alembic
- **Xác thực:** FastAPI-Users + JWT Token Bearer

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### Yêu cầu tiên quyết
- **Node.js:** >= 20.0.0
- **Python:** >= 3.12
- **uv:** Công cụ quản lý môi trường Python siêu tốc ([Cài đặt uv](https://docs.astral.sh/uv/getting-started/installation/))

### 1. Clone mã nguồn
```bash
git clone https://github.com/ThanhTriMKT/KNCSV.git
cd KNCSV
```

### 2. Cài đặt Dependencies
Cài đặt toàn bộ dependencies cho cả Frontend và Backend:
```bash
npm run install:all
```
*(Hoặc chạy thủ công: `uv sync --project backend` và `npm --prefix frontend install`)*

### 3. Khởi chạy Ứng dụng
Chạy đồng thời cả Backend và Frontend chỉ với một câu lệnh:
```bash
npm run dev
```

### 4. Truy cập hệ thống
- **Frontend App:** [http://localhost:3000](http://localhost:3000)
- **Backend API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 👤 Tác Giả & Phát Triển

- **Tác giả:** **ThanhTriMKT (Thanh Tri)**
- **Email:** [thanhtri.dev.pg@gmail.com](mailto:thanhtri.dev.pg@gmail.com)
- **GitHub:** [@ThanhTriMKT](https://github.com/ThanhTriMKT)
- **Đơn vị:** Khoa Công nghệ Thông tin — Trường Đại học Đà Lạt (DLU)

---

## 📄 Bản quyền (License)
Dự án được phát triển phục vụ công tác quản lý và kết nối cựu sinh viên Khoa CNTT - Đại học Đà Lạt. Mọi quyền được bảo lưu.
