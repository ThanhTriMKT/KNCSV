"""
OAuth MCP admin credential verification.

Xác thực tài khoản admin duy nhất cho MCP OAuth login form.
Tài khoản cấu hình qua biến môi trường OAUTH_ADMIN_USERNAME /
OAUTH_ADMIN_PASSWORD_HASH trong .env — không lưu trong DB.

Khi có bảng users thật: thay nội dung hàm verify_admin_credentials()
bằng DB lookup + hash check, không cần sửa gì ở routers/oauth.py.
"""

from pwdlib import PasswordHash

from app.config import settings

_password_hash = PasswordHash.recommended()


def verify_admin_credentials(username: str, password: str) -> bool:
    """
    Trả về True nếu (username, password) khớp với tài khoản admin
    được cấu hình trong .env.

    Luôn chạy hash check dù username sai — tránh timing side-channel
    tiết lộ username admin có tồn tại hay không.
    """
    if not settings.oauth_admin_username or not settings.oauth_admin_password_hash:
        return False

    username_ok = username == settings.oauth_admin_username
    try:
        password_ok = _password_hash.verify(password, settings.oauth_admin_password_hash)
    except Exception:
        # OAUTH_ADMIN_PASSWORD_HASH cấu hình sai (không phải argon2 hash hợp lệ)
        # → coi như không khớp, không raise 500.
        password_ok = False

    return username_ok and password_ok
