"""
Script re-embed lại tất cả bản ghi AlumniProfile trong database bằng mô hình chuẩn
gemini-embedding-001 (1536 chiều).
"""

import asyncio
import os
import sys

# Đảm bảo import được app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from loguru import logger
from sqlalchemy import select

from app.database.models import AlumniProfile
from app.database.session import async_session_factory
from app.services.rag_service import generate_embedding


async def reembed_all():
    logger.info("Bắt đầu re-embed tất cả AlumniProfile...")
    async with async_session_factory() as db:
        res = await db.execute(select(AlumniProfile))
        profiles = res.scalars().all()
        logger.info(f"Tìm thấy {len(profiles)} hồ sơ cần xử lý.")

        for count, p in enumerate(profiles, start=1):
            skills = p.skills.get("items", []) if isinstance(p.skills, dict) else []
            courses = p.courses_taken.get("items", []) if isinstance(p.courses_taken, dict) else []
            text_to_embed = (
                p.raw_text
                or f"{p.full_name}. {p.current_job or ''} tại {p.company or ''}. "
                f"Kỹ năng: {', '.join(skills)}. Môn học: {', '.join(courses)}."
            )
            vec = await generate_embedding(text_to_embed, task_type="RETRIEVAL_DOCUMENT")
            p.embedding = vec
            logger.info(
                f"[{count}/{len(profiles)}] Đã cập nhật embedding cho: {p.full_name} ({p.company})"
            )

        await db.commit()
        logger.info("Hoàn tất re-embed toàn bộ AlumniProfile trong DB!")


if __name__ == "__main__":
    asyncio.run(reembed_all())
