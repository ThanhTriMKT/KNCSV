"""
Trợ lý Hướng nghiệp DLU — Career Advisor API
Knowledge-based career guidance for Khoa CNTT - Đại học Đà Lạt.
No external AI API — all data is curated and served from structured knowledge.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AlumniProfile, Company, JobPost
from app.database.session import get_session

router = APIRouter(prefix="/career-advisor", tags=["career-advisor"])


# ---------------------------------------------------------------------------
# Knowledge Base — curated career data for DLU CNTT
# ---------------------------------------------------------------------------

CAREER_TRACKS = {
    "software_engineering": {
        "id": "software_engineering",
        "name": "Kỹ thuật Phần mềm",
        "icon": "💻",
        "description": "Thiết kế, phát triển và bảo trì hệ thống phần mềm quy mô lớn",
        "skills": {
            "core": [
                "Lập trình OOP (Java, C#, Python)",
                "Cấu trúc dữ liệu & Giải thuật",
                "Cơ sở dữ liệu (SQL, NoSQL)",
                "Mạng máy tính cơ bản",
            ],
            "specialized": [
                "Web Development (React, Next.js, FastAPI)",
                "Mobile Development (React Native, Flutter)",
                "DevOps & CI/CD (Docker, GitHub Actions)",
                "Cloud Services (AWS, GCP, Azure)",
                "Software Architecture & Design Patterns",
            ],
            "soft": [
                "Làm việc nhóm Agile/Scrum",
                "Giao tiếp kỹ thuật & viết tài liệu",
                "Tư duy phân tích & giải quyết vấn đề",
            ],
        },
        "roadmap": [
            {
                "year": "Năm 1-2",
                "focus": "Nền tảng",
                "tasks": [
                    "Học vững C/C++, Python, Java",
                    "Nắm Cấu trúc dữ liệu & Giải thuật",
                    "Tham gia CLB Tin học DLU",
                    "Làm project cá nhân đầu tiên trên GitHub",
                ],
            },
            {
                "year": "Năm 2-3",
                "focus": "Chuyên sâu",
                "tasks": [
                    "Chọn hướng: Web / Mobile / Backend",
                    "Học framework: React, Django/FastAPI, Spring Boot",
                    "Tham gia hackathon & cuộc thi lập trình",
                    "Xây dựng 2-3 project portfolio chất lượng",
                ],
            },
            {
                "year": "Năm 3-4",
                "focus": "Thực chiến",
                "tasks": [
                    "Thực tập tại TMA Solutions, FPT Software, VNG",
                    "Đóng góp Open Source trên GitHub",
                    "Chuẩn bị CV & portfolio chuyên nghiệp",
                    "Ôn thuật toán cho phỏng vấn kỹ thuật",
                ],
            },
        ],
        "target_companies": [
            "TMA Solutions (Đà Lạt & HCM)",
            "FPT Software",
            "VNG Corporation",
            "Viettel Solutions",
            "KMS Technology",
            "Axon Active",
        ],
        "salary_range": {
            "intern": "5-10 triệu/tháng",
            "fresher": "10-18 triệu/tháng",
            "junior": "15-25 triệu/tháng",
            "mid": "25-45 triệu/tháng",
            "senior": "45-80+ triệu/tháng",
        },
    },
    "data_science": {
        "id": "data_science",
        "name": "Khoa học Dữ liệu & AI",
        "icon": "📊",
        "description": "Phân tích dữ liệu, xây dựng mô hình AI/ML để giải quyết bài toán thực tế",
        "skills": {
            "core": [
                "Python (NumPy, Pandas, Matplotlib)",
                "Toán: Xác suất thống kê, Đại số tuyến tính",
                "SQL & Data Warehousing",
                "Xử lý dữ liệu & ETL",
            ],
            "specialized": [
                "Machine Learning (scikit-learn, XGBoost)",
                "Deep Learning (PyTorch, TensorFlow)",
                "NLP & Computer Vision",
                "Big Data (Spark, Hadoop)",
                "MLOps & Model Deployment",
            ],
            "soft": [
                "Kể chuyện bằng dữ liệu (Data Storytelling)",
                "Tư duy phản biện & thực nghiệm",
                "Trình bày kết quả cho stakeholder",
            ],
        },
        "roadmap": [
            {
                "year": "Năm 1-2",
                "focus": "Nền tảng Toán & Lập trình",
                "tasks": [
                    "Học Python chuyên sâu cho Data Science",
                    "Nắm vững Xác suất Thống kê & Đại số tuyến tính",
                    "Thực hành SQL với dữ liệu thật",
                    "Khám phá dữ liệu với Pandas & Matplotlib",
                ],
            },
            {
                "year": "Năm 2-3",
                "focus": "Machine Learning",
                "tasks": [
                    "Hoàn thành khóa Andrew Ng ML trên Coursera",
                    "Tham gia Kaggle competitions",
                    "Xây dựng 3-5 project ML có dashboard",
                    "Học Deep Learning cơ bản (PyTorch)",
                ],
            },
            {
                "year": "Năm 3-4",
                "focus": "Chuyên sâu & Thực tập",
                "tasks": [
                    "Chọn niche: NLP / CV / Recommender System",
                    "Thực tập Data Analyst/Engineer tại doanh nghiệp",
                    "Publish paper hoặc blog kỹ thuật",
                    "Xây portfolio trên GitHub & Kaggle",
                ],
            },
        ],
        "target_companies": [
            "VNG Corporation (AI Lab)",
            "FPT AI Center",
            "Zalo AI (VNG)",
            "Cốc Cốc",
            "Shopee / SEA Group",
            "TMA Solutions (Data Division)",
        ],
        "salary_range": {
            "intern": "6-12 triệu/tháng",
            "fresher": "12-20 triệu/tháng",
            "junior": "18-30 triệu/tháng",
            "mid": "30-55 triệu/tháng",
            "senior": "55-100+ triệu/tháng",
        },
    },
    "network_security": {
        "id": "network_security",
        "name": "Mạng máy tính & An toàn Thông tin",
        "icon": "🔒",
        "description": "Thiết kế, quản trị hệ thống mạng và bảo mật thông tin",
        "skills": {
            "core": [
                "Mạng máy tính (TCP/IP, DNS, DHCP)",
                "Quản trị Linux & Windows Server",
                "Firewall & VPN",
                "Scripting (Bash, PowerShell, Python)",
            ],
            "specialized": [
                "Penetration Testing & Ethical Hacking",
                "SIEM & SOC Operations",
                "Cloud Security (AWS/Azure Security)",
                "Digital Forensics",
                "Compliance (ISO 27001, GDPR)",
            ],
            "soft": [
                "Tư duy phòng thủ & phân tích rủi ro",
                "Viết báo cáo bảo mật",
                "Cập nhật xu hướng tấn công mới",
            ],
        },
        "roadmap": [
            {
                "year": "Năm 1-2",
                "focus": "Nền tảng mạng",
                "tasks": [
                    "Học CCNA (Cisco Certified Network Associate)",
                    "Thực hành Lab mạng (Packet Tracer, GNS3)",
                    "Quản trị Linux cơ bản (Ubuntu, CentOS)",
                    "Tham gia CLB An ninh mạng DLU",
                ],
            },
            {
                "year": "Năm 2-3",
                "focus": "Bảo mật chuyên sâu",
                "tasks": [
                    "Học CEH hoặc CompTIA Security+",
                    "Tham gia CTF (Capture The Flag) competitions",
                    "Thực hành Pentest trên HackTheBox, TryHackMe",
                    "Xây dựng Home Lab bảo mật",
                ],
            },
            {
                "year": "Năm 3-4",
                "focus": "Thực chiến & Chứng chỉ",
                "tasks": [
                    "Thực tập tại SOC / NOC doanh nghiệp",
                    "Thi chứng chỉ CCNP hoặc OSCP",
                    "Viết blog phân tích mã độc / lỗ hổng",
                    "Xây portfolio các bài CTF writeup",
                ],
            },
        ],
        "target_companies": [
            "Viettel Cyber Security",
            "VNPT (VNPT-IT)",
            "CMC Cyber Security",
            "BKAV Corporation",
            "Deloitte Vietnam (Cyber Advisory)",
            "VNG Security Team",
        ],
        "salary_range": {
            "intern": "5-10 triệu/tháng",
            "fresher": "10-18 triệu/tháng",
            "junior": "15-28 triệu/tháng",
            "mid": "28-50 triệu/tháng",
            "senior": "50-90+ triệu/tháng",
        },
    },
}

INTERVIEW_BANK = {
    "general": {
        "category": "Câu hỏi chung",
        "icon": "🎯",
        "questions": [
            {
                "q": "Hãy giới thiệu bản thân bạn.",
                "tip": "Trình bày ngắn gọn 2-3 phút: Tên, trường (Khoa CNTT - ĐH Đà Lạt), chuyên ngành, kinh nghiệm nổi bật, điểm mạnh và mục tiêu nghề nghiệp. Kết thúc bằng lý do bạn phù hợp với vị trí.",
            },
            {
                "q": "Tại sao bạn chọn ngành Công nghệ Thông tin?",
                "tip": "Chia sẻ câu chuyện cá nhân + đam mê cụ thể (ví dụ: viết chương trình đầu tiên, giải quyết bài toán bằng code...). Tránh trả lời chung chung.",
            },
            {
                "q": "Bạn biết gì về công ty chúng tôi?",
                "tip": "Nghiên cứu kỹ trước: sản phẩm chính, văn hóa, thành tựu gần đây. Ví dụ TMA: 'TMA Solutions có chi nhánh tại Đà Lạt, là đối tác offshore lớn nhất Việt Nam...'",
            },
            {
                "q": "Điểm mạnh và điểm yếu của bạn?",
                "tip": "Điểm mạnh: liên quan trực tiếp đến vị trí ứng tuyển + ví dụ cụ thể. Điểm yếu: thật nhưng đang cải thiện (ví dụ: 'Trước đây tôi hay làm việc một mình, nhưng sau dự án X tại DLU, tôi đã quen với teamwork').",
            },
            {
                "q": "Bạn có câu hỏi gì cho chúng tôi không?",
                "tip": "LUÔN hỏi ít nhất 1-2 câu: 'Quy trình onboarding cho thực tập sinh/fresher?', 'Team hiện tại đang dùng tech stack gì?', 'Lộ trình phát triển cho vị trí này?'",
            },
        ],
    },
    "technical_web": {
        "category": "Kỹ thuật — Web Development",
        "icon": "🌐",
        "questions": [
            {
                "q": "Giải thích sự khác nhau giữa SSR, CSR và SSG trong Next.js.",
                "tip": "SSR (Server-Side Rendering): render tại server mỗi request → SEO tốt, data luôn mới. CSR (Client-Side Rendering): render tại browser → nhanh sau lần load đầu. SSG (Static Site Generation): build trước → nhanh nhất, phù hợp blog/doc.",
            },
            {
                "q": "REST API vs GraphQL — khi nào dùng cái nào?",
                "tip": "REST: đơn giản, chuẩn, caching dễ, phù hợp CRUD đơn giản. GraphQL: khi frontend cần flexibility, tránh over-fetching, phù hợp mobile app hoặc dashboard phức tạp.",
            },
            {
                "q": "Giải thích cách hoạt động của JWT authentication.",
                "tip": "User login → server verify → tạo JWT (header.payload.signature) → client lưu token → gửi kèm header Authorization mỗi request → server verify signature.",
            },
            {
                "q": "Làm sao để optimize performance của ứng dụng React?",
                "tip": "Các kỹ thuật: React.memo, useMemo, useCallback, lazy loading, code splitting, virtualized list, debounce API calls, image optimization.",
            },
        ],
    },
    "technical_data": {
        "category": "Kỹ thuật — Data Science",
        "icon": "📊",
        "questions": [
            {
                "q": "Overfitting là gì? Cách xử lý?",
                "tip": "Model học quá chi tiết trên training data → kém trên data mới. Xử lý: Cross-validation, Regularization (L1/L2), Dropout, tăng data, Early stopping, Feature selection.",
            },
            {
                "q": "Giải thích Bias-Variance tradeoff.",
                "tip": "High Bias: model đơn giản, underfit. High Variance: model phức tạp, overfit. Mục tiêu: tìm sweet spot để tổng lỗi nhỏ nhất.",
            },
            {
                "q": "Khi nào dùng Classification vs Regression?",
                "tip": "Classification: output rời rạc (spam/not spam, loại hoa). Regression: output liên tục (giá nhà, nhiệt độ). Chọn đúng metric: accuracy/F1 vs MAE/RMSE.",
            },
        ],
    },
    "technical_security": {
        "category": "Kỹ thuật — An toàn Thông tin",
        "icon": "🔐",
        "questions": [
            {
                "q": "Giải thích mô hình CIA trong bảo mật.",
                "tip": "Confidentiality (Bảo mật): chỉ người được phép mới truy cập. Integrity (Toàn vẹn): dữ liệu không bị thay đổi trái phép. Availability (Sẵn sàng): hệ thống luôn hoạt động khi cần.",
            },
            {
                "q": "SQL Injection là gì? Cách phòng chống?",
                "tip": "Attacker chèn SQL vào input → truy cập/thay đổi DB trái phép. Phòng: Parameterized queries, ORM, Input validation, WAF, Least privilege.",
            },
            {
                "q": "Phân biệt Symmetric vs Asymmetric encryption.",
                "tip": "Symmetric: 1 key (AES) → nhanh, dùng encrypt data. Asymmetric: public/private key (RSA) → chậm hơn, dùng key exchange & digital signature. TLS dùng cả 2.",
            },
        ],
    },
}

CV_TEMPLATES = [
    {
        "id": "fresher_dev",
        "name": "CV Fresher Developer",
        "target": "Sinh viên mới tốt nghiệp ứng tuyển vị trí Developer",
        "sections": [
            "Thông tin cá nhân (Tên, Email, SĐT, LinkedIn, GitHub)",
            "Tóm tắt bản thân (2-3 dòng mục tiêu nghề nghiệp)",
            "Học vấn (Cử nhân CNTT - Đại học Đà Lạt, GPA, thành tích)",
            "Kỹ năng kỹ thuật (Languages, Frameworks, Tools, Databases)",
            "Dự án cá nhân (2-3 project, mô tả ngắn + tech stack + link GitHub)",
            "Kinh nghiệm (Thực tập / Freelance / CLB nếu có)",
            "Chứng chỉ (AWS, CCNA, Coursera...)",
            "Hoạt động ngoại khóa (CLB, hackathon, tình nguyện)",
        ],
        "tips": [
            "Giữ CV trong 1 trang A4",
            "Dùng bullet points, không viết đoạn văn dài",
            "Bắt đầu mỗi bullet bằng action verb: Xây dựng, Triển khai, Phân tích...",
            "Đính kèm link GitHub & portfolio website",
            "Customize CV cho từng vị trí ứng tuyển",
        ],
    },
    {
        "id": "intern_data",
        "name": "CV Thực tập Data Analyst",
        "target": "Sinh viên năm 3-4 ứng tuyển thực tập Data",
        "sections": [
            "Thông tin cá nhân + LinkedIn + Kaggle profile",
            "Objective (Mục tiêu thực tập)",
            "Kỹ năng: Python, SQL, Power BI / Tableau, Excel nâng cao",
            "Dự án phân tích dữ liệu (dataset, insight, visualization)",
            "Kaggle competitions & ranking",
            "Học vấn (Khoa CNTT - ĐH Đà Lạt)",
            "Chứng chỉ: Google Data Analytics, IBM Data Science...",
        ],
        "tips": [
            "Highlight kết quả bằng số liệu: 'Phân tích dataset 100K+ records...'",
            "Đính kèm link Kaggle notebooks",
            "Show dashboard samples trong portfolio",
        ],
    },
    {
        "id": "cover_letter",
        "name": "Thư ứng tuyển (Cover Letter)",
        "target": "Mẫu thư ứng tuyển chuyên nghiệp",
        "sections": [
            "Lời chào & vị trí ứng tuyển",
            "Đoạn 1: Tại sao bạn quan tâm đến công ty (research cụ thể)",
            "Đoạn 2: Kinh nghiệm & kỹ năng phù hợp nhất (2-3 điểm nổi bật)",
            "Đoạn 3: Dự án / thành tích cụ thể chứng minh năng lực",
            "Kết: Mong muốn trao đổi thêm, cảm ơn",
        ],
        "tips": [
            "Viết cá nhân hóa cho TỪNG công ty, không copy paste",
            "Dài tối đa 1 trang, 3-4 đoạn",
            "Tránh lặp lại CV — cover letter bổ sung câu chuyện",
            "Kiểm tra chính tả kỹ trước khi gửi",
        ],
    },
]


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CareerTrackResponse(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    skills: dict
    roadmap: list
    target_companies: list[str]
    salary_range: dict


class InterviewCategoryResponse(BaseModel):
    category: str
    icon: str
    questions: list[dict]


class CVTemplateResponse(BaseModel):
    id: str
    name: str
    target: str
    sections: list[str]
    tips: list[str]


class CareerStatsResponse(BaseModel):
    total_alumni: int
    total_companies: int
    total_jobs: int
    top_companies: list[dict]
    top_skills: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/tracks", response_model=list[CareerTrackResponse])
async def get_career_tracks():
    """Lấy danh sách lộ trình nghề nghiệp theo chuyên ngành DLU CNTT."""
    return list(CAREER_TRACKS.values())


@router.get("/tracks/{track_id}", response_model=CareerTrackResponse)
async def get_career_track(track_id: str):
    """Lấy chi tiết 1 lộ trình nghề nghiệp."""
    track = CAREER_TRACKS.get(track_id)
    if not track:
        from fastapi import HTTPException
        raise HTTPException(404, f"Track '{track_id}' not found")
    return track


@router.get("/interview-bank", response_model=list[InterviewCategoryResponse])
async def get_interview_bank(
    category: str | None = Query(None, description="Filter by category key"),
):
    """Ngân hàng câu hỏi phỏng vấn theo từng lĩnh vực."""
    if category and category in INTERVIEW_BANK:
        return [INTERVIEW_BANK[category]]
    return list(INTERVIEW_BANK.values())


@router.get("/cv-templates", response_model=list[CVTemplateResponse])
async def get_cv_templates():
    """Mẫu CV & Cover Letter cho sinh viên DLU."""
    return CV_TEMPLATES


@router.get("/stats", response_model=CareerStatsResponse)
async def get_career_stats(db: AsyncSession = Depends(get_session)):
    """Thống kê tổng quan thị trường việc làm từ dữ liệu Alumni Portal."""
    total_alumni = (
        await db.execute(select(func.count(AlumniProfile.id)))
    ).scalar() or 0
    total_companies = (
        await db.execute(select(func.count(Company.id)))
    ).scalar() or 0
    total_jobs = (
        await db.execute(select(func.count(JobPost.id)))
    ).scalar() or 0

    # Top companies by number of alumni
    companies_result = await db.execute(
        select(Company.name, func.count(AlumniProfile.id).label("count"))
        .outerjoin(AlumniProfile, AlumniProfile.company_id == Company.id)
        .group_by(Company.id, Company.name)
        .order_by(func.count(AlumniProfile.id).desc())
        .limit(5)
    )
    top_companies = [
        {"name": row.name, "alumni_count": row.count}
        for row in companies_result.all()
    ]

    # Collect skills from alumni
    skills_result = await db.execute(
        select(AlumniProfile.skills).where(AlumniProfile.skills.isnot(None))
    )
    skill_count: dict[str, int] = {}
    for (skills_json,) in skills_result.all():
        if isinstance(skills_json, list):
            for s in skills_json:
                skill_count[s] = skill_count.get(s, 0) + 1
    top_skills = sorted(skill_count, key=skill_count.get, reverse=True)[:10]

    return CareerStatsResponse(
        total_alumni=total_alumni,
        total_companies=total_companies,
        total_jobs=total_jobs,
        top_companies=top_companies,
        top_skills=top_skills,
    )
