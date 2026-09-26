"""
Auth business logic: fastapi-users DB adapter + UserManager, JWT auth
backend, and role-based authorization dependencies.

Everything auth-related that isn't "just a route" or "just a schema" lives
here, so app/routers/auth.py stays a thin route-registration file.
"""

import uuid
from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, exceptions, schemas
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import User
from app.database.session import get_session

# ---------------------------------------------------------------------------
# DB adapter
# ---------------------------------------------------------------------------


async def get_user_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, User)


# ---------------------------------------------------------------------------
# UserManager — password validation + lifecycle hooks
# ---------------------------------------------------------------------------


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.jwt_secret
    verification_token_secret = settings.jwt_secret

    async def validate_password(self, password: str, user: schemas.UC | User) -> None:
        if len(password) < 8:
            raise exceptions.InvalidPasswordException(reason="Mật khẩu phải có ít nhất 8 ký tự.")

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        # Never log email/phone here — only the opaque id + role.
        logger.info(f"User registered: id={user.id} role={user.role}")

        # Auto-extract student_id từ email trường (SPEC: 2212369@dlu.edu.vn → "2212369")
        # Áp dụng cho cả student lẫn alumni — student_id = phần trước "@"
        if not user.student_id and user.email:
            local_part = user.email.split("@")[0]
            # Chỉ gán nếu local part trông như MSSV (toàn số hoặc alphanumeric hợp lệ)
            if local_part and len(local_part) <= 20:
                try:
                    user.student_id = local_part
                    await self.user_db.update(user, {"student_id": local_part})
                    logger.info(f"Auto-set student_id='{local_part}' for user {user.id}")
                except Exception as e:
                    logger.warning(f"Could not set student_id for user {user.id}: {e}")

        # Auto-link AlumniProfile nếu CSV đã được admin import trước đó
        try:
            from sqlalchemy import or_, select

            from app.database.models import AlumniProfile

            conds = []
            if user.student_id:
                conds.append(AlumniProfile.student_id == user.student_id)
            if user.email:
                conds.append(AlumniProfile.email == user.email)

            if conds:
                stmt = select(AlumniProfile).where(
                    AlumniProfile.user_id.is_(None),
                    or_(*conds) if len(conds) > 1 else conds[0],
                )
                res = await self.user_db.session.execute(stmt)
                profile = res.scalar_one_or_none()
                if profile:
                    profile.user_id = user.id
                    await self.user_db.session.commit()
                    logger.info(f"Auto-linked AlumniProfile {profile.id} to user {user.id}")
        except Exception as e:
            logger.warning(f"Could not auto-link AlumniProfile for user {user.id}: {e}")

        try:
            from app.services.points_service import claim_pending_points_for_user

            claim_res = await claim_pending_points_for_user(self.user_db.session, user)
            if claim_res.get("claimed_points", 0) > 0:
                logger.info(
                    f"Auto-claimed {claim_res['claimed_points']} pending points for registered user {user.id}"
                )
        except Exception as e:
            logger.warning(f"Could not auto-claim pending points for user {user.id}: {e}")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ) -> None:
        # TODO: wire to the `resend` email service once transactional email
        # templates exist. For now, log that a reset was requested (not the
        # token itself — the token is a bearer credential).
        logger.info(f"Password reset requested: id={user.id}")

    async def on_after_reset_password(self, user: User, request: Request | None = None) -> None:
        logger.info(f"Password reset completed: id={user.id}")


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


# ---------------------------------------------------------------------------
# JWT authentication backend
# ---------------------------------------------------------------------------

bearer_transport = BearerTransport(tokenUrl="/api/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[User, uuid.UUID]:
    return JWTStrategy(secret=settings.jwt_secret, lifetime_seconds=settings.jwt_lifetime_seconds)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# Standard fastapi-users dependencies, re-exported so routers/other services
# don't need to know about the FastAPIUsers plumbing directly.
current_active_user = fastapi_users.current_user(active=True)
current_active_user_optional = fastapi_users.current_user(active=True, optional=True)


# ---------------------------------------------------------------------------
# Role-based authorization
# ---------------------------------------------------------------------------


def require_roles(*roles: str) -> Callable[..., Coroutine[Any, Any, User]]:
    """
    Dependency factory for role-gated endpoints, e.g.:

        @router.post("/admin/import")
        async def import_alumni(user: User = Depends(require_roles("admin"))):
            ...

    Raises 403 (not 404) on mismatch — the endpoint's existence isn't a
    secret, only the ability to use it is restricted.
    """

    async def dependency(user: User = Depends(current_active_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập tài nguyên này.",
            )
        return user

    return dependency


require_admin = require_roles("admin")
require_alumni = require_roles("alumni", "admin")
