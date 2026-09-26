"""
Conversations Router — lịch sử chat SV <-> AI Agent.

Yêu cầu đăng nhập (role student) cho mọi endpoint: lịch sử chat gắn với
user_id thật, không có khái niệm "ẩn danh" ở đây (khác proxy_messages).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import ChatConversation, User
from app.database.session import get_session
from app.services.auth_service import current_active_user

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    meta: dict | None
    created_at: str

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationSummary):
    messages: list[ChatMessageOut]


async def _get_owned_conversation(
    db: AsyncSession, conversation_id: uuid.UUID, user: User, *, with_messages: bool = False
) -> ChatConversation:
    stmt = select(ChatConversation).where(
        ChatConversation.id == conversation_id, ChatConversation.user_id == user.id
    )
    if with_messages:
        stmt = stmt.options(selectinload(ChatConversation.messages))
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại.")
    return conversation


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    """Danh sách hội thoại của SV hiện tại, mới nhất lên đầu."""
    stmt = (
        select(ChatConversation)
        .where(ChatConversation.user_id == current_user.id)
        .order_by(ChatConversation.updated_at.desc())
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    """Chi tiết 1 hội thoại kèm toàn bộ message, để load lại khi SV mở lại."""
    conversation = await _get_owned_conversation(
        db, conversation_id, current_user, with_messages=True
    )
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        messages=[
            ChatMessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                meta=m.meta,
                created_at=m.created_at.isoformat(),
            )
            for m in conversation.messages
        ],
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    """Xoá 1 hội thoại (và toàn bộ message trong đó, qua cascade)."""
    conversation = await _get_owned_conversation(db, conversation_id, current_user)
    await db.delete(conversation)
    await db.commit()
    return {"status": "deleted", "conversation_id": str(conversation_id)}


class RenameBody(BaseModel):
    title: str


@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: uuid.UUID,
    body: RenameBody,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(current_active_user),
):
    """Đổi tên hội thoại (SV tự đặt lại, khác title tự sinh ban đầu)."""
    conversation = await _get_owned_conversation(db, conversation_id, current_user)
    conversation.title = body.title.strip()[:255] or conversation.title
    await db.commit()
    return {"status": "updated", "title": conversation.title}
