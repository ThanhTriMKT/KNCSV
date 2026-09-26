"""
AI RAG (Retrieval-Augmented Generation) & Semantic Matchmaking Service.
"""

import math
import re
import uuid
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import AlumniProfile


def get_fallback_vector(text: str, dim: int = 1536) -> list[float]:
    """Generate a mock normalized embedding vector from string hash for local testing."""
    vec = [0.0] * dim
    val = sum(ord(c) for c in text)
    for i in range(dim):
        vec[i] = math.sin(val + i)
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]


_GEMINI_EMBEDDING_MODEL = "gemini-embedding-2"


def _embedding_api_key() -> str:
    """Trả về API key cho embedding: ưu tiên GEMINI_EMBEDDING_API_KEY, fallback GEMINI_API_KEY."""
    return getattr(settings, "gemini_embedding_api_key", None) or settings.gemini_api_key


async def generate_embedding(
    text: str,
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[float]:
    """Generate 1536-dim embedding vector dùng Gemini Embedding 2.

    task_type:
      - "RETRIEVAL_DOCUMENT" : dùng khi tạo vector cho hồ sơ (seed/upload).
      - "RETRIEVAL_QUERY"    : dùng khi tạo vector cho câu hỏi tìm kiếm.
    """
    api_key = _embedding_api_key()
    if api_key:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{_GEMINI_EMBEDDING_MODEL}:embedContent?key={api_key}"
        )
        payload = {
            "content": {"parts": [{"text": text}]},
            "task_type": task_type,
            "output_dimensionality": 1536,
        }
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    values = res.json().get("embedding", {}).get("values", [])
                    if values:
                        return values[:1536]
                logger.warning(f"Gemini Embedding 2 returned {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.error(f"Gemini Embedding 2 request failed: {e}")

    return get_fallback_vector(text)


def anonymize_name(full_name: str) -> str:
    """
    Ẩn danh họ tên: "Nguyễn Văn An" → "Anh/Chị N.V.A"
    Chỉ hiện chữ cái đầu từng từ — không lộ danh tính thật cho SV.
    """
    parts = full_name.strip().split()
    if not parts:
        return "Alumni"
    initials = ".".join(p[0].upper() for p in parts if p)
    return f"Anh/Chị {initials}"


_STOP_WORDS = {
    "có",
    "anh",
    "chị",
    "nào",
    "làm",
    "việc",
    "tại",
    "ở",
    "ko",
    "không",
    "hỏi",
    "cho",
    "em",
    "mình",
    "với",
    "tôi",
    "muốn",
    "xin",
    "tư",
    "vấn",
    "về",
    "ngành",
    "của",
    "và",
    "là",
    "đang",
    "được",
    "tìm",
    "kiếm",
    "giúp",
    "biết",
    "ai",
    "bạn",
}


def _extract_keywords(query: str) -> list[str]:
    """Tách các từ khóa có ý nghĩa từ query để boost keyword match."""
    # Tách theo chữ cái, số (bỏ dấu câu)
    tokens = re.findall(r"\b[\w-]+\b", query.lower())
    keywords = [t for t in tokens if len(t) >= 2 and t not in _STOP_WORDS]
    return keywords


async def search_relevant_alumni(
    db: AsyncSession, query: str, limit: int = 5
) -> list[dict[str, Any]]:
    """
    Tìm kiếm CSV phù hợp bằng Hybrid Search:
    Kết hợp pgvector cosine distance + Keyword match boost (trên company, current_job, skills, raw_text).
    Đảm bảo các truy vấn như 'shope' -> khớp Shopee nhận điểm ưu tiên cao nhất.
    """
    try:
        from sqlalchemy import or_

        query_vec = await generate_embedding(query, task_type="RETRIEVAL_QUERY")
        keywords = _extract_keywords(query)

        # 1. Lấy ứng viên từ pgvector cosine distance
        vector_stmt = (
            select(
                AlumniProfile,
                (1.0 - AlumniProfile.embedding.cosine_distance(query_vec)).label("vector_sim"),
            )
            .where(AlumniProfile.embedding.isnot(None))
            .order_by(AlumniProfile.embedding.cosine_distance(query_vec))
            .limit(15)
        )
        vec_res = await db.execute(vector_stmt)
        candidates: dict[str, tuple[AlumniProfile, float]] = {
            str(row[0].id): (row[0], float(row[1]) if row[1] is not None else 0.0)
            for row in vec_res.all()
        }

        # 2. Lấy ứng viên từ Keyword match nếu có từ khóa
        if keywords:
            kw_conditions = []
            for kw in keywords:
                kw_conditions.append(AlumniProfile.company.ilike(f"%{kw}%"))
                kw_conditions.append(AlumniProfile.current_job.ilike(f"%{kw}%"))
                kw_conditions.append(AlumniProfile.raw_text.ilike(f"%{kw}%"))

            kw_stmt = select(AlumniProfile).where(or_(*kw_conditions)).limit(15)
            kw_res = await db.execute(kw_stmt)
            for p in kw_res.scalars().all():
                p_id = str(p.id)
                if p_id not in candidates:
                    candidates[p_id] = (p, 0.0)

        if not candidates:
            return []

        # 3. Tính điểm kết hợp (Hybrid scoring)
        scored_profiles: list[tuple[AlumniProfile, float]] = []
        for _, (profile, vec_sim) in candidates.items():
            score = vec_sim
            company_lower = (profile.company or "").lower()
            job_lower = (profile.current_job or "").lower()
            skills_list = [
                s.lower()
                for s in (
                    profile.skills.get("items", []) if isinstance(profile.skills, dict) else []
                )
            ]
            skills_text = " ".join(skills_list)
            raw_lower = (profile.raw_text or "").lower()

            for kw in keywords:
                # Nếu từ khóa khớp trong tên công ty (ví dụ: 'shope' trong 'Shopee')
                if kw in company_lower:
                    score += 0.8
                # Nếu từ khóa khớp trong chức danh / vị trí
                if kw in job_lower:
                    score += 0.5
                # Nếu từ khóa khớp trong kỹ năng
                if kw in skills_text:
                    score += 0.3
                elif kw in raw_lower:
                    score += 0.2

            scored_profiles.append((profile, score))

        # Sắp xếp điểm giảm dần
        scored_profiles.sort(key=lambda x: x[1], reverse=True)
        top_profiles = [p for p, _ in scored_profiles[:limit]]

        return [
            {
                "id": str(p.id),
                "anonymized_name": anonymize_name(p.full_name),
                "current_job": p.current_job or "",
                "company": p.company or "",
                "skills": p.skills.get("items", []) if isinstance(p.skills, dict) else [],
                "courses_taken": (
                    p.courses_taken.get("items", []) if isinstance(p.courses_taken, dict) else []
                ),
            }
            for p in top_profiles
        ]
    except Exception as e:
        logger.error(f"Alumni semantic search failed: {e}")
        return []


def profile_to_card(p: AlumniProfile) -> dict:
    """Chuyển đổi AlumniProfile thành dictionary an toàn cho thẻ hiển thị cựu sinh viên."""
    return {
        "id": str(p.id),
        "anonymized_name": anonymize_name(p.full_name),
        "current_job": p.current_job or "",
        "company": p.company or "",
        "skills": p.skills.get("items", []) if isinstance(p.skills, dict) else [],
        "courses_taken": (
            p.courses_taken.get("items", []) if isinstance(p.courses_taken, dict) else []
        ),
    }


async def find_alumni_card(db: AsyncSession, target_id: str) -> dict | None:
    """Tìm 1 cựu sinh viên phù hợp theo UUID, student_id hoặc tên/tên viết tắt ẩn danh."""
    if not target_id:
        return None
    target_id_clean = target_id.strip()

    # 1. Thử theo UUID
    try:
        val_uuid = uuid.UUID(target_id_clean)
        res = await db.execute(select(AlumniProfile).where(AlumniProfile.id == val_uuid))
        p = res.scalar_one_or_none()
        if p:
            return profile_to_card(p)
    except ValueError:
        pass

    # 2. Thử theo student_id
    res = await db.execute(select(AlumniProfile).where(AlumniProfile.student_id == target_id_clean))
    p = res.scalar_one_or_none()
    if p:
        return profile_to_card(p)

    # 3. Thử tìm theo anonymized name hoặc full_name — dùng SQL ILIKE tránh full table scan
    normalized_target = (
        target_id_clean.lower()
        .replace("anh/chị", "")
        .replace("anh", "")
        .replace("chị", "")
        .replace(".", "")
        .strip()
    )
    if normalized_target:
        from sqlalchemy import or_

        res = await db.execute(
            select(AlumniProfile)
            .where(
                or_(
                    AlumniProfile.full_name.ilike(f"%{normalized_target}%"),
                    AlumniProfile.full_name.ilike(f"%{target_id_clean}%"),
                )
            )
            .limit(5)
        )
        for p in res.scalars().all():
            anon = anonymize_name(p.full_name)
            anon_clean = anon.lower().replace("anh/chị", "").replace(".", "").strip()
            if (
                target_id_clean.lower() in anon.lower()
                or anon.lower() in target_id_clean.lower()
                or (normalized_target and normalized_target == anon_clean)
                or target_id_clean.lower() in p.full_name.lower()
            ):
                return profile_to_card(p)

    return None
