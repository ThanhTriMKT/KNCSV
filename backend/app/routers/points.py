"""
Points Router — SPEC §4 Module 4 (Growth Loop).

Auto-claim được xử lý tự động trong auth_service.on_after_register() khi CSV đăng ký.
Router này chỉ expose endpoint đọc điểm của user hiện tại.
"""

from fastapi import APIRouter, Depends

from app.database.models import User
from app.services.auth_service import current_active_user

router = APIRouter(prefix="/points", tags=["Points"])


@router.get("/me")
async def get_my_points(
    current_user: User = Depends(current_active_user),
):
    """Trả về điểm cống hiến hiện tại của user đang đăng nhập."""
    return {
        "user_id": str(current_user.id),
        "active_points": current_user.active_points,
    }
