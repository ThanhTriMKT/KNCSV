"""
Seed script for AlumniProfile, Users, and Pending Points.

Mục đích:
  - Khởi tạo dữ liệu mẫu phong phú và thực tế cho bảng `alumni_profiles`
    để kiểm thử toàn diện các tính năng AI Agent (app/ai/agent.py, app/ai/schemas.py, app/ai/tools.py).
  - Tự động sinh vector embedding (1536 chiều) qua `generate_embedding` cho từng profile.
  - Tạo các tài khoản người dùng mẫu (Admin, Student, Alumni đã đăng ký & Alumni chưa đăng ký).
  - Khởi tạo dữ liệu PendingPoints để kiểm thử tính năng tích điểm chờ.
  - Cung cấp cờ `--test-ai` để tự động chạy kiểm thử các kịch bản AI Agent (tìm kiếm trực tiếp,
    hỏi bổ sung clarify form, resume form, hội thoại thông thường, câu hỏi không tìm thấy).

Cách chạy:
  # Chạy seed dữ liệu (upsert an toàn, không trùng lặp):
  python scripts/seed.py

  # Reset toàn bộ dữ liệu mẫu và seed lại từ đầu:
  python scripts/seed.py --reset

  # Chạy seed kèm kiểm thử tự động các kịch bản AI Agent:
  python scripts/seed.py --test-ai
"""

# ruff: noqa: E402
import argparse
import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any

# Đảm bảo import được app.* bất kể chạy từ root hay từ thư mục backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from loguru import logger
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agent import close_agent, init_agent, run_chat_agent
from app.ai.schemas import (
    ActionCardEvent,
    ActivityEvent,
    ChunkEvent,
    ClarifyEvent,
    DoneEvent,
    MetaEvent,
)
from app.database.models import AlumniProfile, PendingPoints, User
from app.database.session import async_session_factory, engine
from app.services.rag_service import generate_embedding

# Password hasher cho test users
_pwd_hash = PasswordHash.recommended()
DEFAULT_PASSWORD = "Alumni@123456"

# ---------------------------------------------------------------------------
# Dữ liệu 12 hồ sơ Cựu sinh viên (AlumniProfile) phong phú, chuẩn thực tế
# ---------------------------------------------------------------------------
SEED_ALUMNI_DATA: list[dict[str, Any]] = [
    {
        "student_id": "1811001",
        "full_name": "Nguyễn Quốc Anh",
        "email": "1811001@dlu.edu.vn",
        "current_job": "Senior AI Engineer",
        "company": "VinAI Research",
        "skills": [
            "Python",
            "PyTorch",
            "LangChain",
            "Transformers",
            "RAG",
            "Computer Vision",
            "Deep Learning",
            "MLOps",
        ],
        "courses_taken": [
            "Học máy",
            "Trí tuệ nhân tạo nâng cao",
            "Thị giác máy tính",
            "Xử lý ngôn ngữ tự nhiên",
            "Cấu trúc dữ liệu và giải thuật",
        ],
        "raw_text": (
            "Nguyễn Quốc Anh, cựu sinh viên khóa K18 ngành Khoa học máy tính. "
            "Hiện là Senior AI Engineer tại VinAI Research với hơn 4 năm kinh nghiệm nghiên cứu "
            "và triển khai các mô hình Deep Learning, Large Language Models (LLM), hệ thống RAG và Computer Vision. "
            "Thành thạo Python, PyTorch, Hugging Face Transformers, LangChain, vector database và quy trình MLOps. "
            "Từng hoàn thành xuất sắc các môn: Học máy, Trí tuệ nhân tạo nâng cao, Thị giác máy tính. "
            "Sẵn sàng tư vấn 15-30 phút cho sinh viên về: lộ trình tự học AI/Machine Learning từ nền tảng, "
            "chuẩn bị đồ án tốt nghiệp mảng AI, kinh nghiệm phỏng vấn vị trí AI Fresher/Intern tại các lab nghiên cứu và công ty lớn, "
            "review CV và định hướng nghiên cứu chuyên sâu."
        ),
        "user_account": {
            "email": "1811001@dlu.edu.vn",
            "phone": "0901001001",
            "role": "alumni",
        },
    },
    {
        "student_id": "1711045",
        "full_name": "Trần Minh Trí",
        "email": "1711045@dlu.edu.vn",
        "current_job": "Staff Backend Engineer",
        "company": "VNG Corporation (ZaloPay)",
        "skills": [
            "Golang",
            "Python",
            "FastAPI",
            "PostgreSQL",
            "Redis",
            "Apache Kafka",
            "Distributed Systems",
            "Docker",
            "Kubernetes",
        ],
        "courses_taken": [
            "Cơ sở dữ liệu nâng cao",
            "Hệ phân tán",
            "Kiến trúc phần mềm",
            "Mạng máy tính",
            "Nhập môn lập trình",
        ],
        "raw_text": (
            "Trần Minh Trí, cựu sinh viên K17 ngành Kỹ thuật phần mềm. "
            "Hiện giữ vị trí Staff Backend Engineer tại ZaloPay (VNG Corporation) với hơn 6 năm kinh nghiệm "
            "thiết kế và tối ưu hệ thống thanh toán điện tử chịu tải hàng triệu giao dịch mỗi ngày. "
            "Chuyên sâu về Golang, Python, FastAPI, kiến trúc Microservices, message queue Kafka, bộ nhớ đệm Redis và tối ưu hóa PostgreSQL. "
            "Đạt điểm xuất sắc các môn: Hệ phân tán, Kiến trúc phần mềm, Cơ sở dữ liệu nâng cao. "
            "Rất nhiệt tình hỗ trợ sinh viên: tư vấn thiết kế hệ thống backend chuẩn, cách xử lý bài toán concurrency/high traffic, "
            "kỹ năng viết API sạch và dễ mở rộng, kinh nghiệm phỏng vấn Backend Developer và vượt qua vòng thử việc."
        ),
        # Chưa đăng ký user -> để test tính năng Pending Points và Claim on Signup
        "user_account": None,
        "pending_points": [
            {"points": 10, "reason": "Tư vấn SV về định hướng Backend Microservices"},
            {"points": 20, "reason": "Tham gia chia sẻ tọa đàm hướng nghiệp K22"},
        ],
    },
    {
        "student_id": "1911082",
        "full_name": "Lê Thị Hồng Vân",
        "email": "1911082@dlu.edu.vn",
        "current_job": "Senior Frontend Engineer",
        "company": "NAB Innovation Centre Vietnam",
        "skills": [
            "TypeScript",
            "React",
            "Next.js",
            "Tailwind CSS",
            "Redux Toolkit",
            "Web Performance",
            "UI/UX Design",
            "GraphQL",
        ],
        "courses_taken": [
            "Phát triển ứng dụng Web",
            "Thiết kế giao diện người dùng (UI/UX)",
            "Lập trình hướng đối tượng",
            "Công nghệ phần mềm",
        ],
        "raw_text": (
            "Lê Thị Hồng Vân, cựu sinh viên K19 ngành Công nghệ thông tin. "
            "Hiện làm việc tại NAB Innovation Centre Vietnam với vai trò Senior Frontend Engineer. "
            "Chuyên về hệ sinh thái React, Next.js (App Router, Server Components), TypeScript, Tailwind CSS và kiến trúc Design System. "
            "Có nhiều kinh nghiệm tối ưu Web Vitals, hiệu năng tải trang và trải nghiệm người dùng ngân hàng số. "
            "Đạt điểm A môn Phát triển ứng dụng Web và Thiết kế giao diện UI/UX. "
            "Sẵn sàng kết nối chia sẻ: cách xây dựng portfolio frontend nổi bật để ứng tuyển công ty đa quốc gia, "
            "kinh nghiệm làm việc bằng tiếng Anh trong môi trường Agile quốc tế, mẹo phỏng vấn Live Coding React/JS."
        ),
        "user_account": {
            "email": "1911082@dlu.edu.vn",
            "phone": "0901001003",
            "role": "alumni",
        },
    },
    {
        "student_id": "1811120",
        "full_name": "Phạm Hoàng Long",
        "email": "1811120@dlu.edu.vn",
        "current_job": "Lead Cloud & DevOps Engineer",
        "company": "MoMo (M_Service)",
        "skills": [
            "Docker",
            "Kubernetes",
            "AWS",
            "Terraform",
            "CI/CD",
            "GitLab CI",
            "Prometheus",
            "Grafana",
            "Linux System",
        ],
        "courses_taken": [
            "Điện toán đám mây",
            "Quản trị hệ thống Linux",
            "An toàn thông tin",
            "Kiến trúc máy tính",
        ],
        "raw_text": (
            "Phạm Hoàng Long, cựu sinh viên K18. "
            "Trưởng nhóm DevOps/Cloud Infrastructure tại Ví điện tử MoMo. "
            "Chuyên về triển khai hạ tầng đám mây AWS, tự động hóa với Terraform (IaC), điều phối container Kubernetes (EKS), "
            "xây dựng pipeline CI/CD và hệ thống giám sát cảnh báo Prometheus/Grafana. "
            "Đạt chứng chỉ AWS Certified Solutions Architect Professional và CKA (Certified Kubernetes Administrator). "
            "Có thể tư vấn cho SV: lộ trình học DevOps từ sinh viên năm 2-3, cách tự build home lab thực hành Docker/K8s, "
            "ôn thi chứng chỉ đám mây quốc tế và bí quyết ứng tuyển vị trí DevOps Fresher."
        ),
        "user_account": {
            "email": "1811120@dlu.edu.vn",
            "phone": "0901001004",
            "role": "alumni",
        },
    },
    {
        "student_id": "2011033",
        "full_name": "Đặng Thu Thảo",
        "email": "2011033@dlu.edu.vn",
        "current_job": "Senior Mobile Developer (Flutter/Android)",
        "company": "Ahamove",
        "skills": [
            "Flutter",
            "Dart",
            "Android SDK",
            "Kotlin",
            "Clean Architecture",
            "BLoC",
            "Firebase",
            "RESTful API",
        ],
        "courses_taken": [
            "Lập trình thiết bị di động",
            "Lập trình hướng đối tượng",
            "Công nghệ phần mềm",
            "Phân tích thiết kế hệ thống",
        ],
        "raw_text": (
            "Đặng Thu Thảo, cựu sinh viên K20 ngành Kỹ thuật phần mềm. "
            "Hiện là Senior Mobile Developer tại Ahamove, phụ trách phát triển ứng dụng tài xế và khách hàng trên Flutter. "
            "Kinh nghiệm xử lý GPS tracking realtime, tối ưu hóa pin và bộ nhớ cho app di động, áp dụng Clean Architecture và BLoC pattern. "
            "Từng đạt giải thưởng nghiên cứu khoa học sinh viên mảng ứng dụng di động. "
            "Nhận tư vấn sinh viên: hướng dẫn làm đồ án tốt nghiệp mobile app thực tế, lộ trình từ beginner đến Mobile Engineer, "
            "kinh nghiệm chọn công nghệ giữa Flutter, React Native hay Native (Kotlin/Swift)."
        ),
        "user_account": None,
    },
    {
        "student_id": "1911145",
        "full_name": "Vũ Tuấn Kiệt",
        "email": "1911145@dlu.edu.vn",
        "current_job": "QA Automation Lead",
        "company": "KMS Technology",
        "skills": [
            "Selenium",
            "Cypress",
            "Playwright",
            "Python",
            "Postman",
            "API Testing",
            "Performance Testing",
            "JMeter",
            "CI/CD Integration",
        ],
        "courses_taken": [
            "Kiểm thử phần mềm",
            "Đảm bảo chất lượng phần mềm",
            "Nhập môn công nghệ phần mềm",
            "Cơ sở dữ liệu",
        ],
        "raw_text": (
            "Vũ Tuấn Kiệt, cựu sinh viên K19. "
            "Hiện là QA Automation Lead tại KMS Technology với hơn 4 năm kinh nghiệm kiểm thử phần mềm tự động. "
            "Thành thạo xây dựng test framework với Playwright, Cypress, Selenium kết hợp Python/TypeScript. "
            "Chuyên về kiểm thử API với Postman, kiểm thử hiệu năng với JMeter và tích hợp automation test vào CI/CD pipeline. "
            "Học rất tốt môn Kiểm thử phần mềm và Đảm bảo chất lượng phần mềm. "
            "Sẵn lòng hỗ trợ: định hướng nghề nghiệp ngành Software Testing (QA/QC/Automation Tester), "
            "hướng dẫn viết Test Plan, Test Cases chuẩn chỉ và bí quyết vượt qua bài test phỏng vấn QA."
        ),
        "user_account": {
            "email": "1911145@dlu.edu.vn",
            "phone": "0901001006",
            "role": "alumni",
        },
    },
    {
        "student_id": "1811210",
        "full_name": "Đoàn Kim Ngân",
        "email": "1811210@dlu.edu.vn",
        "current_job": "Senior Data Engineer",
        "company": "Techcombank",
        "skills": [
            "Apache Spark",
            "Apache Airflow",
            "dbt",
            "SQL",
            "Python",
            "Google BigQuery",
            "Snowflake",
            "Data Pipeline",
            "Data Warehousing",
        ],
        "courses_taken": [
            "Kho dữ liệu và khai phá dữ liệu",
            "Cơ sở dữ liệu phân tán",
            "Hệ thống thông tin quản lý",
            "Cấu trúc dữ liệu và giải thuật",
        ],
        "raw_text": (
            "Đoàn Kim Ngân, cựu sinh viên K18 chuyên ngành Hệ thống thông tin. "
            "Hiện là Senior Data Engineer tại Khối Dữ liệu & Phân tích Techcombank. "
            "Chuyên sâu về kiến trúc Data Lakehouse, xây dựng batch & streaming data pipeline với Spark, Airflow, dbt, "
            "tối ưu hóa truy vấn SQL trên kho dữ liệu phân tán hàng chục Terabyte. "
            "Điểm 10 môn Kho dữ liệu và Khai phá dữ liệu. "
            "Sẵn sàng tư vấn cho các bạn SV: phân biệt rõ lộ trình Data Analyst vs Data Engineer vs Data Scientist, "
            "kỹ năng SQL thực chiến nâng cao trong doanh nghiệp và cách chuẩn bị phỏng vấn ngành Dữ liệu."
        ),
        "user_account": None,
    },
    {
        "student_id": "1711099",
        "full_name": "Bùi Quang Huy",
        "email": "1711099@dlu.edu.vn",
        "current_job": "Security Specialist / Pentester",
        "company": "Viettel Cyber Security",
        "skills": [
            "Penetration Testing",
            "Web Security",
            "OWASP Top 10",
            "Network Security",
            "Reverse Engineering",
            "SIEM",
            "Linux Hardening",
            "Burp Suite",
        ],
        "courses_taken": [
            "An toàn mạng máy tính",
            "Mật mã học ứng dụng",
            "An ninh hệ thống thông tin",
            "Hệ điều hành",
        ],
        "raw_text": (
            "Bùi Quang Huy, cựu sinh viên K17 ngành An toàn thông tin / Khoa học máy tính. "
            "Chuyên gia đánh giá an toàn thông tin (Pentester) tại Viettel Cyber Security. "
            "Từng phát hiện nhiều lỗ hổng bảo mật Web/API (theo OWASP Top 10), giàu kinh nghiệm tham gia giải đấu CTF trong và ngoài nước. "
            "Sở hữu chứng chỉ OSCP và CEH. "
            "Hỗ trợ sinh viên: định hướng lộ trình học An toàn thông tin, rèn luyện kỹ năng CTF qua HackTheBox/TryHackMe, "
            "tư vấn xin thực tập tại các trung tâm an ninh mạng (SOC) và đạo đức nghề nghiệp hacker mũ trắng."
        ),
        "user_account": {
            "email": "1711099@dlu.edu.vn",
            "phone": "0901001008",
            "role": "alumni",
        },
    },
    {
        "student_id": "1611012",
        "full_name": "Hoàng Ngọc Mai",
        "email": "1611012@dlu.edu.vn",
        "current_job": "Product Lead",
        "company": "Shopee (Sea Group)",
        "skills": [
            "Product Management",
            "Agile/Scrum",
            "User Research",
            "System Design",
            "Data Analytics",
            "Product Roadmapping",
            "Stakeholder Management",
        ],
        "courses_taken": [
            "Quản lý dự án phần mềm",
            "Phân tích thiết kế hệ thống",
            "Khởi nghiệp công nghệ",
            "Kỹ thuật truyền thông",
        ],
        "raw_text": (
            "Hoàng Ngọc Mai, cựu sinh viên K16. "
            "Hiện là Product Lead tại sàn thương mại điện tử Shopee (Sea Group). "
            "Xuất thân từ dân kỹ thuật phần mềm, sau đó chuyển hướng và gặt hái nhiều thành công trong mảng Product Management. "
            "Có kinh nghiệm quản lý sản phẩm quy mô lớn, nghiên cứu hành vi người dùng, phối hợp giữa Business và Engineering team. "
            "Nhiệt tình hỗ trợ SV: cách chuyển hướng từ IT sang Product Owner / Product Manager (APM), "
            "phương pháp tư duy sản phẩm định hướng dữ liệu (Data-driven Product Design) và kỹ năng giao tiếp thuyết trình."
        ),
        "user_account": None,
    },
    {
        "student_id": "1811305",
        "full_name": "Nguyễn Văn Đức",
        "email": "1811305@dlu.edu.vn",
        "current_job": "Embedded Software Engineer",
        "company": "Bosch Global Software Technologies",
        "skills": [
            "C",
            "C++",
            "Embedded Linux",
            "RTOS",
            "STM32",
            "CAN Bus",
            "Automotive Software",
            "AUTOSAR",
            "IoT",
        ],
        "courses_taken": [
            "Hệ thống nhúng",
            "Vi điều khiển",
            "Kiến trúc máy tính",
            "Kỹ thuật số và mạch logic",
        ],
        "raw_text": (
            "Nguyễn Văn Đức, cựu sinh viên K18 ngành Kỹ thuật máy tính / Điện tử viễn thông. "
            "Kỹ sư phát triển phần mềm nhúng ô tô tại Bosch Global Software Technologies Vietnam. "
            "Thành thạo lập trình C/C++, FreeRTOS, vi điều khiển ARM Cortex-M (STM32), giao thức mạng CAN bus và kiến trúc AUTOSAR. "
            "Hoàn thành xuất sắc môn Hệ thống nhúng và Vi điều khiển. "
            "Sẵn sàng giải đáp: lộ trình học lập trình nhúng và IoT từ ghế nhà trường, "
            "bí quyết phỏng vấn vào các tập đoàn công nghệ phần cứng/nhúng như Bosch, Renesas, FPT Software Automotive."
        ),
        "user_account": {
            "email": "1811305@dlu.edu.vn",
            "phone": "0901001010",
            "role": "alumni",
        },
    },
    {
        "student_id": "1711200",
        "full_name": "Trần Bảo Long",
        "email": "1711200@dlu.edu.vn",
        "current_job": "Senior Software Engineer (Overseas)",
        "company": "Grab Singapore",
        "skills": [
            "Distributed Systems",
            "Golang",
            "Microservices",
            "Algorithms & Data Structures",
            "System Design",
            "English Communication",
            "International Relocation",
        ],
        "courses_taken": [
            "Cấu trúc dữ liệu và giải thuật",
            "Hệ điều hành",
            "Tiếng Anh chuyên ngành",
            "Lập trình phân tán",
        ],
        "raw_text": (
            "Trần Bảo Long, cựu sinh viên K17. "
            "Hiện làm việc tại trụ sở Grab Singapore với vai trò Senior Software Engineer. "
            "Có nhiều kinh nghiệm phỏng vấn thuật toán LeetCode, phỏng vấn System Design bằng tiếng Anh, "
            "và quy trình xin visa làm việc nước ngoài (Work Pass). "
            "Từng là sinh viên giỏi môn Cấu trúc dữ liệu & Giải thuật. "
            "Rất muốn hỗ trợ các bạn trẻ: cách chuẩn bị hồ sơ ứng tuyển công ty Big Tech quốc tế, "
            "luyện tập giải thuật LeetCode có chiến lược, cải thiện tiếng Anh chuyên ngành và hòa nhập môi trường làm việc toàn cầu."
        ),
        "user_account": None,
    },
    {
        "student_id": "1911320",
        "full_name": "Lê Tuấn Anh",
        "email": "1911320@dlu.edu.vn",
        "current_job": "Game Developer",
        "company": "Amanotes Vietnam",
        "skills": [
            "Unity 3D",
            "C#",
            "Game Physics",
            "3D Math",
            "Shader Programming",
            "Mobile Game Optimization",
            "Git",
        ],
        "courses_taken": [
            "Lập trình đồ họa",
            "Lập trình game",
            "Cấu trúc dữ liệu và giải thuật",
            "Toán rời rạc",
        ],
        "raw_text": (
            "Lê Tuấn Anh, cựu sinh viên K19. "
            "Game Developer tại Amanotes — công ty phát hành game âm nhạc hàng đầu thế giới với hàng tỷ lượt tải. "
            "Chuyên về Unity engine, C#, lập trình đồ họa shader, toán học 3D trong game và tối ưu hóa FPS cho game mobile. "
            "Đam mê làm game từ năm thứ 2 đại học và có nhiều sản phẩm indie game trên Google Play. "
            "Sẵn sàng chia sẻ cho sinh viên: con đường trở thành Game Developer, cách tự làm game hoàn chỉnh từ A-Z, "
            "kinh nghiệm chọn đề tài môn học mảng Game và cơ hội nghề nghiệp trong ngành công nghiệp game Việt Nam."
        ),
        "user_account": {
            "email": "1911320@dlu.edu.vn",
            "phone": "0901001012",
            "role": "alumni",
        },
    },
]

# ---------------------------------------------------------------------------
# Tài khoản mẫu bổ sung (Admin & Student)
# ---------------------------------------------------------------------------
EXTRA_USERS = [
    {
        "email": "admin@alumni.vn",
        "full_name": "Quản Trị Viên Hệ Thống",
        "student_id": "ADMIN01",
        "phone": "0999000001",
        "role": "admin",
        "active_points": 0,
    },
    {
        "email": "student@alumni.vn",
        "full_name": "Lê Minh Sinh Viên",
        "student_id": "2212345",
        "phone": "0999000002",
        "role": "student",
        "active_points": 50,
    },
]


async def seed_users_and_profiles(db: AsyncSession, reset: bool = False) -> None:
    """Tạo hoặc cập nhật danh sách AlumniProfile, Users và PendingPoints."""
    logger.info("--- BẮT ĐẦU SEED DỮ LIỆU ---")

    if reset:
        logger.warning("Đang reset dữ liệu cũ theo yêu cầu (--reset)...")
        # Xóa pending points trước do khóa ngoại
        await db.execute(delete(PendingPoints))
        # Xóa alumni profiles
        await db.execute(delete(AlumniProfile))
        # Xóa users được tạo bởi seed (theo email list)
        seed_emails = [a["email"] for a in SEED_ALUMNI_DATA] + [u["email"] for u in EXTRA_USERS]
        await db.execute(delete(User).where(User.email.in_(seed_emails)))
        await db.commit()
        logger.info("Đã xóa sạch dữ liệu mẫu cũ.")

    hashed_default_pwd = _pwd_hash.hash(DEFAULT_PASSWORD)

    # 1. Tạo các Extra Users (Admin, Student)
    created_users = 0
    for u_info in EXTRA_USERS:
        stmt = select(User).where(User.email == u_info["email"])
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email=u_info["email"],
                hashed_password=hashed_default_pwd,
                role=u_info["role"],
                full_name=u_info["full_name"],
                student_id=u_info["student_id"],
                phone=u_info["phone"],
                active_points=u_info["active_points"],
                is_active=True,
                is_verified=True,
                is_superuser=(u_info["role"] == "admin"),
            )
            db.add(user)
            created_users += 1
            logger.info(f"Đã tạo User [{u_info['role']}]: {u_info['email']}")

    await db.commit()

    # 2. Xử lý từng AlumniProfile
    created_profiles = 0
    updated_profiles = 0
    created_pending_points = 0

    for item in SEED_ALUMNI_DATA:
        student_id = item["student_id"]
        full_name = item["full_name"]
        email = item["email"]
        raw_text = item["raw_text"]
        user_account = item.get("user_account")

        # 2a. Nếu profile có user_account -> tạo User nếu chưa có
        user_id = None
        if user_account:
            user_email = user_account["email"]
            stmt = select(User).where(User.email == user_email)
            res = await db.execute(stmt)
            existing_user = res.scalar_one_or_none()
            if not existing_user:
                existing_user = User(
                    id=uuid.uuid4(),
                    email=user_email,
                    hashed_password=hashed_default_pwd,
                    role=user_account["role"],
                    full_name=full_name,
                    student_id=student_id,
                    phone=user_account.get("phone"),
                    active_points=100,
                    is_active=True,
                    is_verified=True,
                )
                db.add(existing_user)
                await db.flush()
                created_users += 1
                logger.info(f"Đã tạo User [alumni]: {user_email}")
            user_id = existing_user.id

        # 2b. Tính vector embedding 1536 chiều
        logger.info(f"Đang sinh embedding cho CSV {full_name} ({item['current_job']})...")
        embedding_vec = await generate_embedding(raw_text)

        # 2c. Tìm profile theo student_id
        stmt = select(AlumniProfile).where(AlumniProfile.student_id == student_id)
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()

        if profile:
            # Cập nhật thông tin
            profile.full_name = full_name
            profile.email = email
            profile.current_job = item["current_job"]
            profile.company = item["company"]
            profile.skills = {"items": item["skills"]}
            profile.courses_taken = {"items": item["courses_taken"]}
            profile.raw_text = raw_text
            profile.embedding = embedding_vec
            if user_id and not profile.user_id:
                profile.user_id = user_id
            updated_profiles += 1
            logger.info(f"Cập nhật AlumniProfile: {full_name} ({student_id})")
        else:
            profile = AlumniProfile(
                id=uuid.uuid4(),
                user_id=user_id,
                student_id=student_id,
                full_name=full_name,
                email=email,
                current_job=item["current_job"],
                company=item["company"],
                skills={"items": item["skills"]},
                courses_taken={"items": item["courses_taken"]},
                raw_text=raw_text,
                embedding=embedding_vec,
            )
            db.add(profile)
            created_profiles += 1
            logger.info(f"Tạo mới AlumniProfile: {full_name} ({student_id})")

        # 2d. Nếu có pending_points mẫu (dành cho CSV chưa đăng ký tài khoản)
        pending_list = item.get("pending_points", [])
        if pending_list:
            for p in pending_list:
                stmt_pts = select(PendingPoints).where(
                    PendingPoints.alumni_student_id == student_id,
                    PendingPoints.reason == p["reason"],
                )
                res_pts = await db.execute(stmt_pts)
                if not res_pts.scalar_one_or_none():
                    pts = PendingPoints(
                        id=uuid.uuid4(),
                        alumni_student_id=student_id,
                        points=p["points"],
                        status="PENDING",
                        reason=p["reason"],
                    )
                    db.add(pts)
                    created_pending_points += 1

    await db.commit()
    logger.success(
        f"Hoàn tất Seed: {created_profiles} hồ sơ tạo mới, {updated_profiles} hồ sơ cập nhật, "
        f"{created_users} người dùng, {created_pending_points} bản ghi điểm chờ."
    )


# ---------------------------------------------------------------------------
# Test Suite tự động kiểm thử tính năng AI Agent (app/ai/agent.py & schemas.py)
# ---------------------------------------------------------------------------
async def run_ai_tests() -> None:
    """Kiểm tra toàn diện hoạt động của AI Agent với dữ liệu AlumniProfile vừa seed."""
    logger.info("==================================================")
    logger.info("BẮT ĐẦU KIỂM THỬ TỰ ĐỘNG CÁC TÍNH NĂNG AI AGENT")
    logger.info("==================================================")

    # 1. Khởi tạo Agent
    await init_agent()

    # Kịch bản 1: Tìm kiếm trực tiếp cựu sinh viên ngành AI / Machine Learning
    logger.info("\n--- KỊCH BẢN 1: Tìm kiếm cụ thể (AI / Machine Learning) ---")
    query_1 = "Tìm giúp em cựu sinh viên làm AI hoặc Machine Learning để em xin tư vấn thực tập"
    logger.info(f"Query: '{query_1}'")

    events_1: list[Any] = []
    async for ev in run_chat_agent(query_1, None, None, []):
        events_1.append(ev)
        if isinstance(ev, ActivityEvent):
            logger.info(f"  [SSE: activity] tool={ev.tool} | status={ev.status} | {ev.label}")
        elif isinstance(ev, ActionCardEvent):
            logger.success(
                f"  [SSE: action_card] alumni_id={ev.alumni_id} | cards={len(ev.alumni_cards)} | brief preview: {ev.brief[:80]}..."
            )
        elif isinstance(ev, ClarifyEvent):
            logger.warning(f"  [SSE: clarify] fields={ev.fields}")
        elif isinstance(ev, MetaEvent):
            logger.info(f"  [SSE: meta] recommended_alumni count={len(ev.recommended_alumni)}")
        elif isinstance(ev, DoneEvent):
            logger.info("  [SSE: done] stream kết thúc thành công")

    has_action_card = any(isinstance(e, ActionCardEvent) for e in events_1)
    has_chunks = any(isinstance(e, ChunkEvent) for e in events_1)
    assert has_chunks, "Kịch bản 1 thất bại: Không nhận được ChunkEvent phản hồi"
    logger.info(f"Kịch bản 1 kết quả: has_action_card={has_action_card}, has_chunks={has_chunks}")

    # Kịch bản 2: Câu hỏi mơ hồ -> AI kích hoạt Form bổ sung (ClarifyEvent)
    logger.info("\n--- KỊCH BẢN 2: Câu hỏi mơ hồ -> AI kích hoạt Form bổ sung ---")
    query_2 = "Em muốn tìm cựu sinh viên giúp em"
    logger.info(f"Query: '{query_2}'")

    conv_id_2 = str(uuid.uuid4())
    events_2: list[Any] = []
    clarify_ev: ClarifyEvent | None = None
    async for ev in run_chat_agent(query_2, conv_id_2, None, []):
        events_2.append(ev)
        if isinstance(ev, ClarifyEvent):
            clarify_ev = ev
            logger.success(f"  [SSE: clarify] Đã nhận ClarifyEvent với {len(ev.fields)} fields:")
            for f in ev.fields:
                logger.info(f"    - Field: name={f.get('name')}, label={f.get('label')}")

    # Kịch bản 3: Sinh viên điền Form bổ sung -> AI resume và tìm kiếm kết quả
    if clarify_ev:
        logger.info("\n--- KỊCH BẢN 3: Resume sau khi SV điền Form bổ sung ---")
        clarification_data = {
            "industry": "Backend Development",
            "skills": "Golang, Python, Microservices",
        }
        logger.info(f"Sinh viên nộp clarification_data: {clarification_data}")

        events_3: list[Any] = []
        async for ev in run_chat_agent(
            query_2, conv_id_2, clarification_data=clarification_data, alumni_matches=[]
        ):
            events_3.append(ev)
            if isinstance(ev, ActivityEvent):
                logger.info(f"  [SSE: activity] {ev.label}")
            elif isinstance(ev, ActionCardEvent):
                logger.success(
                    f"  [SSE: action_card] Resume thành công! Alumni được đề xuất: {ev.alumni_id}"
                )
            elif isinstance(ev, DoneEvent):
                logger.info("  [SSE: done] Resume hoàn thành")

    # Kịch bản 4: Trò chuyện xã giao thông thường -> Không gọi search tool
    logger.info("\n--- KỊCH BẢN 4: Trò chuyện thông thường (Không gọi tool) ---")
    query_4 = "Chào bạn! Bạn có thể làm được những gì?"
    logger.info(f"Query: '{query_4}'")

    events_4: list[Any] = []
    async for ev in run_chat_agent(query_4, None, None, []):
        events_4.append(ev)

    called_search = any(
        isinstance(e, ActivityEvent) and e.tool == "search_alumni_pgvector" for e in events_4
    )
    assert not called_search, "Kịch bản 4 thất bại: AI không được gọi search tool khi chào hỏi"
    logger.success("Kịch bản 4 thành công: AI trả lời tự nhiên mà không kích hoạt search tool.")

    # 4. Đóng Agent connection
    await close_agent()
    logger.info("\n==================================================")
    logger.success("HOÀN TẤT KIỂM THỬ TOÀN DIỆN AI AGENT & SCHEMAS!")
    logger.info("==================================================")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed dữ liệu AlumniProfile để test chức năng AI Agent"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Xóa sạch dữ liệu mẫu cũ trước khi seed lại",
    )
    parser.add_argument(
        "--test-ai",
        action="store_true",
        help="Chạy kiểm thử tự động các kịch bản của AI Agent sau khi seed",
    )
    args = parser.parse_args()

    async def _async_main() -> None:
        async with async_session_factory() as session:
            await seed_users_and_profiles(session, reset=args.reset)

        if args.test_ai:
            await run_ai_tests()

        await engine.dispose()

    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
