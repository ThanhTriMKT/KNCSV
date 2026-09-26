"""
Application configuration loaded from environment variables.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

# Thư mục chứa file này: backend/app/ → lên 1 cấp = backend/
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    """
    Infrastructure settings loaded from .env or environment.
    """

    # --- Database ---
    database_url: str = Field(
        default="sqlite+aiosqlite:///./alumni.db",
        description="Database connection string (SQLite or PostgreSQL async)",
    )

    # --- Auth (fastapi-users) ---
    # Single secret reused for JWT auth tokens + reset-password tokens.
    # MUST be overridden in production — this default is dev-only.
    jwt_secret: str = Field(
        default="CHANGE_ME_dev_only_secret",
        description="Secret used to sign JWT access tokens and reset-password tokens",
    )
    jwt_lifetime_seconds: int = Field(
        default=3600 * 24 * 7,  # 7 days
        description="Access token lifetime in seconds",
    )

    # --- AI Keys ---
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    gemini_embedding_api_key: str = Field(
        default="", description="Optional separate API key for Gemini Embedding"
    )
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic Claude API key (SPEC §6: extra ai[anthropic])",
    )

    # --- Email (Resend) ---
    resend_api_key: str = Field(
        default="", description="Resend API key — bỏ trống để tắt gửi email"
    )
    resend_from_email: str = Field(
        default="noreply@alumni.local",
        description="Địa chỉ From khi gửi email qua Resend (phải verify domain trên Resend dashboard)",
    )

    # --- CORS ---
    cors_origins: str = Field(default="*")

    # --- Google Calendar (service account) ---
    google_service_account_file: str = Field(
        default="",
        description="Path to the Google service account JSON key file used "
        "to create anonymous Meet links via the system's own calendar.",
    )
    google_calendar_id: str = Field(
        default="primary",
        description="Calendar ID under the service account to create events on.",
    )

    oauth_admin_username: str = Field(
        default="",
        description="Username for the single admin account OAuth login "
        "authenticates against. Temporary until a real users table exists.",
    )
    oauth_admin_password_hash: str = Field(
        default="",
        description="Argon2 hash of the admin password (never store plaintext "
        "here). Generate with: "
        'python -c "from pwdlib import PasswordHash; '
        "print(PasswordHash.recommended().hash('your-password'))\"",
    )

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a list."""
        value = self.cors_origins.strip()
        if value == "*":
            return ["*"]
        return [o.strip() for o in value.split(",") if o.strip()]


settings = Settings()
