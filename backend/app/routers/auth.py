"""
Auth API for students & alumni (SPEC §"Tech stack": fastapi-users — JWT,
password hashing, forgot-password all provided by the library).

This file only registers routes. Business logic lives in
app/services/auth_service.py, request/response shapes in
app/schemas/auth_schemas.py.

Mounted routes (see app/main.py for the prefix):
  POST /auth/register              — SV/CSV self-registration (role: student|alumni)
  POST /auth/jwt/login             — email + password -> bearer JWT
  POST /auth/jwt/logout            — no-op for JWT (stateless), kept for API symmetry
  POST /auth/forgot-password       — request a reset token (email delivery: TODO)
  POST /auth/reset-password        — consume a reset token
  GET  /users/me, PATCH /users/me  — current user profile (own full_name/phone/zalo_id)

Admin accounts are provisioned out-of-band (not via /auth/register — see
app/schemas/auth_schemas.py:UserCreate), so there is no public admin signup route.
"""

from fastapi import APIRouter

from app.schemas.auth_schemas import UserCreate, UserRead, UserUpdate
from app.services.auth_service import auth_backend, fastapi_users

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
