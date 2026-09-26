"""
Admin Document Pipeline Router (SPEC §4 Module 1).

Luồng duy nhất:
  POST /documents/preview  — Admin upload PDF → AI trích xuất → preview list (không lưu DB)
  POST /documents/confirm  — Admin xem preview → Xác nhận → upsert alumni_profiles
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import get_session
from app.services.auth_service import current_active_user
from app.services.document_service import (
    confirm_student_document,
    preview_student_document,
)
from app.services.knowledge_service import (
    delete_knowledge_document,
    list_knowledge_documents,
    search_knowledge_chunks,
    upload_knowledge_document,
)
from app.services.parser_service import DocumentType

router = APIRouter(prefix="/documents", tags=["Documents"])

_MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def _require_admin(user: User) -> None:
    """Raise 403 nếu user không phải admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Chỉ Admin mới có quyền thực hiện thao tác này."
        )


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    title: str
    status: str
    char_count: int
    chunk_count: int
    error: str | None
    created_at: str


class DocumentChunkOut(BaseModel):
    document_id: str
    document_title: str
    chunk_index: int
    content: str


class PreviewRecordDiff(BaseModel):
    """Nội dung thay đổi so với dữ liệu hiện tại trong DB (chỉ có khi status='update')."""

    old: object
    new: object


class PreviewItem(BaseModel):
    status: str  # "new" | "update"
    record: dict
    diff: dict | None = None  # {field: {old, new}} hoặc None nếu không có thay đổi thực


class ConfirmRequest(BaseModel):
    """Payload gửi lên sau khi Admin review preview và chọn records muốn import."""

    items: list[dict]  # subset của PreviewItem.record (Admin có thể bỏ bớt)


class ConfirmResult(BaseModel):
    created: int
    updated: int
    skipped: int
    skip_reasons: list[str] = []


# ---------------------------------------------------------------------------
# Admin Document Pipeline
# ---------------------------------------------------------------------------


@router.post("/preview", response_model=list[PreviewItem], status_code=200)
async def preview_document(
    file: Annotated[UploadFile, File()],
    doc_type: DocumentType = Query(
        "general",
        description="Loại tài liệu: grade_sheet | internship_list | course_enrollment | general",
    ),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    """
    [Admin only] Upload PDF tài liệu trường, AI trích xuất danh sách sinh viên,
    trả về preview để Admin xem trước — **KHÔNG lưu DB**.

    Mỗi item trong kết quả có:
    - `status`: "new" (chưa có trong DB) hoặc "update" (đã có, kèm `diff`).
    - `record`: thông tin sinh viên trích xuất được.
    - `diff`: map field → {old, new} (chỉ khi status="update" và có thay đổi thực).

    Sau khi xem preview, Admin gọi POST /documents/confirm với danh sách đã chọn.
    """
    _require_admin(current_user)

    filename = file.filename or ""
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext not in ("pdf", "csv", "xlsx", "xls"):
        raise HTTPException(
            status_code=400,
            detail="Chỉ chấp nhận file định dạng PDF, Excel (.xlsx, .xls) hoặc CSV.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File rỗng.")
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File vượt quá giới hạn {_MAX_UPLOAD_BYTES // (1024 * 1024)}MB.",
        )

    items = await preview_student_document(db, content, filename, doc_type)
    return [PreviewItem(**item) for item in items]


@router.post("/confirm", response_model=ConfirmResult, status_code=200)
async def confirm_document(
    body: ConfirmRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    """
    [Admin only] Xác nhận import danh sách records đã review từ preview vào DB.

    `items` là danh sách record Admin muốn import (có thể là subset của kết quả
    /preview — Admin bỏ chọn những record không muốn import).

    Mỗi record khớp với user trong DB theo email. Record không tìm được user
    sẽ bị skip (returned in `skipped` count).
    """
    _require_admin(current_user)

    # Wrap bare records vào format preview_items expect
    preview_items = [{"record": item} if "record" not in item else item for item in body.items]
    result = await confirm_student_document(db, preview_items, uploaded_by_id=current_user.id)
    return ConfirmResult(**result)


# ---------------------------------------------------------------------------
# Knowledge Base RAG — tài liệu tự do (quy chế, FAQ...), TÁCH BIỆT với Admin
# Document Pipeline ở trên (pipeline đó chỉ ghi vào alumni_profiles).
# ---------------------------------------------------------------------------


def _to_document_out(doc, chunk_count: int) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        filename=doc.filename,
        title=doc.title,
        status=doc.status,
        char_count=doc.char_count,
        chunk_count=chunk_count,
        error=doc.error,
        created_at=doc.created_at.isoformat(),
    )


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: Annotated[UploadFile, File()],
    db: AsyncSession = Depends(get_session),
):
    """Upload tài liệu tham khảo tự do (không phải hồ sơ SV) — extract, chia
    chunk và sinh embedding ngay, trả về document (có thể status=FAILED nếu
    không trích xuất được text)."""
    filename = file.filename or "document"
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext not in ("pdf", "csv", "xlsx", "xls"):
        raise HTTPException(400, "Chỉ chấp nhận file PDF, Excel (.xlsx, .xls) hoặc CSV.")
    content = await file.read()
    if not content:
        raise HTTPException(400, "File rỗng.")
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File vượt quá giới hạn {_MAX_UPLOAD_BYTES // (1024 * 1024)}MB.")
    doc, chunk_count = await upload_knowledge_document(db, content, filename)
    return _to_document_out(doc, chunk_count)


@router.get("", response_model=list[DocumentOut])
async def list_documents(db: AsyncSession = Depends(get_session)):
    """Danh sách tài liệu tham khảo, mới nhất lên đầu."""
    pairs = await list_knowledge_documents(db)
    return [_to_document_out(doc, count) for doc, count in pairs]


@router.get("/search", response_model=list[DocumentChunkOut])
async def search_documents(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_session),
):
    """Semantic search trên các đoạn tài liệu tham khảo (không phải hồ sơ SV)."""
    return await search_knowledge_chunks(db, q, limit)


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    _require_admin(current_user)
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(400, "document_id không hợp lệ.") from None
    ok = await delete_knowledge_document(db, doc_uuid)
    if not ok:
        raise HTTPException(404, "Không tìm thấy tài liệu.")
    return {"status": "deleted", "document_id": document_id}
