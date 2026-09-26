"""
Email notification service — dùng Resend Python SDK (đã có trong pyproject.toml).

Nguyên tắc (SPEC §6b): file này chỉ chứa business logic thuần, KHÔNG import
`ai` hay `fastmcp`. Cả ai/tools.py lẫn mcp/tools.py đều gọi hàm ở đây.

Nếu chưa cấu hình RESEND_API_KEY → log warning và bỏ qua (không crash server).
"""

import asyncio

import resend
from loguru import logger

from app.config import settings


def _get_client() -> resend.Emails | None:
    """Trả về Resend email client nếu API key được cấu hình, ngược lại None."""
    if not settings.resend_api_key:
        return None
    resend.api_key = settings.resend_api_key
    return resend.Emails


async def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """
    Gửi email thông báo qua Resend (non-blocking).

    Args:
        to_email: Địa chỉ email nhận (SPEC §7: ẩn danh / hệ thống).
        subject:  Tiêu đề email.
        body:     Nội dung email.

    Returns:
        True nếu gửi thành công, False nếu thiếu config hoặc lỗi.
    """
    client = _get_client()
    if client is None:
        logger.warning(f"RESEND_API_KEY chưa được cấu hình — bỏ qua gửi email tới {to_email}")
        return False

    try:
        params: resend.Emails.SendParams = {
            "from": settings.resend_from_email,
            "to": [to_email],
            "subject": subject,
            "text": body,
        }
        await asyncio.to_thread(client.send, params)
        logger.info(f"Email đã gửi tới {to_email} | subject={subject}")
        return True
    except Exception as exc:
        logger.error(f"Gửi email thất bại tới {to_email}: {exc}")
        return False
