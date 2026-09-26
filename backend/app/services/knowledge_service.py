"""
Knowledge Base RAG service — quản lý tài liệu tự do (quy chế, FAQ...) dùng
để AI trả lời câu hỏi chung. TÁCH BIỆT hoàn toàn khỏi Admin Document Pipeline
(document_service.py, chỉ dùng cho alumni_profiles). KHÔNG import ai/ hay
fastmcp (giống quy ước của email_service.py).
"""

import uuid
from typing import Any

from loguru import logger
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DocumentChunk, KnowledgeDocument
from app.services.parser_service import extract_text_from_file
from app.services.rag_service import generate_embedding

_CHUNK_SIZE = 1000
_CHUNK_OVERLAP = 100


def _split_text(text: str) -> list[str]:
    """Cắt text thành các đoạn ~1000 ký tự, overlap 100 ký tự để không mất
    ngữ cảnh ở ranh giới đoạn."""
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - _CHUNK_OVERLAP
    return chunks


async def upload_knowledge_document(
    db: AsyncSession,
    file_bytes: bytes,
    filename: str,
    uploaded_by_id: uuid.UUID | None = None,
) -> tuple[KnowledgeDocument, int]:
    """
    Tạo KnowledgeDocument, extract + chunk + embed đồng bộ.

    Trả về (doc, chunk_count) — chunk_count trả tường minh thay vì đọc
    doc.chunks (relationship chưa eager-load sẽ crash MissingGreenlet trong
    async SQLAlchemy).
    """
    doc = KnowledgeDocument(
        filename=filename,
        title=filename.rsplit(".", 1)[0],
        uploaded_by_id=uploaded_by_id,
        status="PROCESSING",
    )
    db.add(doc)
    await db.commit()  # commit riêng để có doc.id ổn định trước khi tạo chunk
    await db.refresh(doc)

    try:
        raw_text = extract_text_from_file(file_bytes, filename)
        if not raw_text.strip():
            doc.status = "FAILED"
            doc.error = "Không trích xuất được text từ file."
            await db.commit()
            return doc, 0

        pieces = _split_text(raw_text)
        for idx, piece in enumerate(pieces):
            embedding = await generate_embedding(piece)
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    content=piece,
                    embedding=embedding,
                )
            )
        doc.char_count = len(raw_text)
        doc.status = "READY"
        await db.commit()
        return doc, len(pieces)
    except Exception as e:
        logger.error(f"upload_knowledge_document failed for '{filename}': {e}")
        # Bỏ mọi DocumentChunk dở dang chưa commit trước khi đánh dấu FAILED,
        # tránh tài liệu FAILED nhưng vẫn có chunk mồ côi trong DB.
        await db.rollback()
        doc.status = "FAILED"
        doc.error = str(e)[:500]
        await db.commit()
        return doc, 0


async def list_knowledge_documents(
    db: AsyncSession,
) -> list[tuple[KnowledgeDocument, int]]:
    """Trả kèm chunk_count qua LEFT JOIN + COUNT — không đụng relationship
    .chunks (tránh lazy-load ngầm định, không hỗ trợ trong async ORM)."""
    stmt = (
        select(KnowledgeDocument, func.count(DocumentChunk.id))
        .outerjoin(DocumentChunk, DocumentChunk.document_id == KnowledgeDocument.id)
        .group_by(KnowledgeDocument.id)
        .order_by(KnowledgeDocument.created_at.desc())
    )
    res = await db.execute(stmt)
    return [(doc, count) for doc, count in res.all()]


async def search_knowledge_chunks(
    db: AsyncSession, query: str, limit: int = 5
) -> list[dict[str, Any]]:
    query_vec = await generate_embedding(query)
    stmt = (
        select(DocumentChunk, KnowledgeDocument.title)
        .join(KnowledgeDocument, KnowledgeDocument.id == DocumentChunk.document_id)
        .where(DocumentChunk.embedding.isnot(None))
        .order_by(DocumentChunk.embedding.cosine_distance(query_vec))
        .limit(limit)
    )
    res = await db.execute(stmt)
    return [
        {
            "document_id": str(chunk.document_id),
            "document_title": title,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
        }
        for chunk, title in res.all()
    ]


async def delete_knowledge_document(db: AsyncSession, doc_id: uuid.UUID) -> bool:
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        return False
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc_id))
    await db.delete(doc)
    await db.commit()
    return True
