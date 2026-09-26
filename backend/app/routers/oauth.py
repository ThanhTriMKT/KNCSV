"""
OAuth 2.1 router — Authorization Code + PKCE flow for Claude Desktop MCP.

Endpoints:
  GET  /.well-known/oauth-authorization-server  — server metadata (RFC 8414)
  POST /oauth/register                           — dynamic client registration (RFC 7591)
  GET  /oauth/authorize                          — show login form
  POST /oauth/authorize                          — submit credentials, issue code
  POST /oauth/token                              — exchange code for MCP token

Scope note: there is no clients table or users table yet. Dynamic client
registration accepts any client and hands back a client_id with no stored
record — every client_id is implicitly trusted. Login authenticates against
a single admin account (see app/services/auth.py). Both are acceptable for
a single-operator MCP server; neither is acceptable multi-tenant. Revisit
once a database layer exists.
"""

import base64
import hashlib
import html
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from loguru import logger

from app.config import settings
from app.services.oauth_service import verify_admin_credentials

# Two routers: one mounts at root (for .well-known), one at /oauth
wellknown_router = APIRouter()
router = APIRouter()

_JWT_ALGORITHM = "HS256"
_ACCESS_TOKEN_TTL_SECONDS = 3600
_AUTH_CODE_TTL_SECONDS = 300  # 5 minutes — RFC 6749 §4.1.2 recommends short-lived codes


# ---------------------------------------------------------------------------
# In-memory authorization code store.
#
# Codes live for ~5 minutes between /oauth/authorize issuing one and
# /oauth/token redeeming it — an in-process dict is fine for that window.
# This does NOT survive a server restart or work across multiple worker
# processes; once a real datastore exists, swap this for a table with a
# TTL index instead of adding process-external locking here.
# ---------------------------------------------------------------------------


@dataclass
class _PendingAuthCode:
    client_id: str
    redirect_uri: str
    code_challenge: str
    code_challenge_method: str
    expires_at: float
    used: bool = False


_auth_codes: dict[str, _PendingAuthCode] = {}


def _prune_expired_codes() -> None:
    now = time.time()
    expired = [code for code, entry in _auth_codes.items() if entry.expires_at < now]
    for code in expired:
        del _auth_codes[code]


def _store_auth_code(
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    code_challenge_method: str,
) -> str:
    _prune_expired_codes()
    code = secrets.token_urlsafe(32)
    _auth_codes[code] = _PendingAuthCode(
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        expires_at=time.time() + _AUTH_CODE_TTL_SECONDS,
    )
    return code


def _redeem_auth_code(code: str) -> _PendingAuthCode | None:
    """
    Look up a code and mark it used. Returns None if the code doesn't
    exist, has expired, or was already redeemed (RFC 6749 §4.1.2 requires
    rejecting a reused code and, ideally, revoking anything already issued
    from it — we don't have anything to revoke yet since we mint the
    access token in the same call that redeems the code).
    """
    entry = _auth_codes.get(code)
    if entry is None:
        return None
    if entry.used or entry.expires_at < time.time():
        return None
    entry.used = True
    return entry


def _verify_pkce(code_verifier: str, code_challenge: str, method: str) -> bool:
    if method != "S256":
        # RFC 7636 also allows "plain", but we only advertise S256 support
        # in oauth_metadata below — reject anything else outright.
        return False
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return secrets.compare_digest(computed, code_challenge)


def _require_session_secret() -> str:
    if not settings.oauth_session_secret:
        raise HTTPException(
            status_code=500,
            detail="OAUTH_SESSION_SECRET is not configured on the server.",
        )
    return settings.oauth_session_secret


def _issue_access_token(client_id: str) -> str:
    now = int(time.time())
    payload = {
        "iss": "alumni-mcp",
        "sub": client_id,
        "iat": now,
        "exp": now + _ACCESS_TOKEN_TTL_SECONDS,
    }
    return jwt.encode(payload, _require_session_secret(), algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Exposed for the /mcp auth dependency to call. Raises jwt exceptions
    (ExpiredSignatureError, InvalidTokenError, ...) on failure — callers
    should catch those and respond 401, not import this and assume success.
    """
    return jwt.decode(token, _require_session_secret(), algorithms=[_JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# OAuth server metadata (RFC 8414)
# ---------------------------------------------------------------------------


@wellknown_router.get("/.well-known/oauth-authorization-server")
async def oauth_metadata(request: Request):
    base = str(request.base_url).rstrip("/")
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "registration_endpoint": f"{base}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
    }


# ---------------------------------------------------------------------------
# OAuth Protected Resource metadata (RFC 9728)
#
# Advertises that /mcp is an OAuth-protected resource and points clients
# (Claude Desktop, etc.) at the authorization server. Returned in the
# WWW-Authenticate header on 401 responses from /mcp so clients can
# auto-discover the OAuth flow.
# ---------------------------------------------------------------------------


@wellknown_router.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource_metadata(request: Request):
    base = str(request.base_url).rstrip("/")
    return {
        "resource": f"{base}/mcp",
        "authorization_servers": [base],
        "bearer_methods_supported": ["header"],
        "scopes_supported": [],
        "resource_name": "Alumni MCP",
        "resource_documentation": f"{base}/docs",
    }


# RFC 9728 §3.1 encodes the resource path into the well-known URL: for
# resource https://host/mcp the metadata location is
# /.well-known/oauth-protected-resource/mcp. Serve the same document there
# so clients that follow that convention also find it.
@wellknown_router.get("/.well-known/oauth-protected-resource/mcp")
async def oauth_protected_resource_metadata_path_suffix(request: Request):
    return await oauth_protected_resource_metadata(request)


# ---------------------------------------------------------------------------
# Dynamic client registration (RFC 7591)
#
# No clients table exists yet: every registration request is accepted and
# handed a fresh client_id, with nothing persisted server-side to check it
# against later. This is fine for "trust whichever app the operator points
# at this server" but is not a real multi-tenant registration endpoint.
# ---------------------------------------------------------------------------


@router.post("/register", status_code=201)
async def register_client(request: Request):
    base = str(request.base_url).rstrip("/")
    body = await request.json()
    redirect_uris = body.get("redirect_uris") or []
    if not redirect_uris:
        raise HTTPException(
            status_code=400, detail="redirect_uris is required for client registration"
        )

    client_id = secrets.token_urlsafe(16)
    return {
        "client_id": client_id,
        "client_name": body.get("client_name", ""),
        "redirect_uris": redirect_uris,
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "registration_client_uri": f"{base}/oauth/register/{client_id}",
    }


# ---------------------------------------------------------------------------
# Authorization endpoint
# ---------------------------------------------------------------------------


def _login_form(
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
    code_challenge_method: str,
    error: str = "",
) -> str:
    # All values interpolated into the HTML come from the querystring /
    # a failed login attempt — escape everything to avoid reflected XSS
    # (e.g. a malicious redirect_uri containing "><script>...).
    error_html = f'<p class="error">{html.escape(error)}</p>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <title>Đăng nhập — Alumni MCP</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 360px; margin: 80px auto; }}
        input {{ display: block; width: 100%; box-sizing: border-box; margin-bottom: 12px;
                 padding: 8px; font-size: 1rem; }}
        button {{ width: 100%; padding: 10px; font-size: 1rem; cursor: pointer; }}
        .error {{ color: #b91c1c; }}
    </style>
</head>
<body>
    <h1>Đăng nhập</h1>
    {error_html}
    <form method="post" action="/oauth/authorize">
        <input type="text" name="username" placeholder="Username" required autofocus>
        <input type="password" name="password" placeholder="Password" required>
        <input type="hidden" name="client_id" value="{html.escape(client_id)}">
        <input type="hidden" name="redirect_uri" value="{html.escape(redirect_uri)}">
        <input type="hidden" name="state" value="{html.escape(state)}">
        <input type="hidden" name="code_challenge" value="{html.escape(code_challenge)}">
        <input type="hidden" name="code_challenge_method" value="{html.escape(code_challenge_method)}">
        <button type="submit">Đăng nhập</button>
    </form>
</body>
</html>"""


@router.get("/authorize", response_class=HTMLResponse)
async def authorize_get(
    client_id: str,
    redirect_uri: str,
    response_type: str,
    code_challenge: str,
    code_challenge_method: str = "S256",
    state: str = "",
):
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Only response_type=code is supported")
    if code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="Only code_challenge_method=S256 is supported")

    return HTMLResponse(
        _login_form(
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
    )


@router.post("/authorize")
async def authorize_post(
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    state: str = Form(""),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form("S256"),
):
    if not verify_admin_credentials(username, password):
        logger.info(f"OAuth login failed for username={username!r}")
        return HTMLResponse(
            _login_form(
                client_id=client_id,
                redirect_uri=redirect_uri,
                state=state,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                error="Sai tên đăng nhập hoặc mật khẩu.",
            ),
            status_code=401,
        )

    code = _store_auth_code(
        client_id=client_id,
        redirect_uri=redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )
    query = {"code": code}
    if state:
        query["state"] = state
    return RedirectResponse(url=f"{redirect_uri}?{urlencode(query)}", status_code=302)


# ---------------------------------------------------------------------------
# Token endpoint
# ---------------------------------------------------------------------------


@router.post("/token")
async def token_endpoint(
    grant_type: str = Form(...),
    code: str = Form(""),
    redirect_uri: str = Form(""),
    client_id: str = Form(""),
    code_verifier: str = Form(""),
):
    if grant_type != "authorization_code":
        raise HTTPException(
            status_code=400, detail="Only grant_type=authorization_code is supported"
        )

    entry = _redeem_auth_code(code)
    if entry is None:
        raise HTTPException(status_code=400, detail="Invalid, expired, or already-used code")

    if entry.redirect_uri != redirect_uri:
        raise HTTPException(
            status_code=400, detail="redirect_uri does not match the authorization request"
        )

    if not code_verifier or not _verify_pkce(
        code_verifier, entry.code_challenge, entry.code_challenge_method
    ):
        raise HTTPException(status_code=400, detail="code_verifier does not match code_challenge")

    access_token = _issue_access_token(entry.client_id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": _ACCESS_TOKEN_TTL_SECONDS,
    }


# ---------------------------------------------------------------------------
# /mcp auth gate
#
# decode_access_token() above was written to be "exposed for the /mcp auth
# dependency to call", but until now nothing actually called it: main.py
# mounted mcp_http_app directly with no auth check, so /mcp was reachable
# with zero authentication despite this whole PKCE flow existing. This
# middleware is that missing dependency — main.py wraps mcp_http_app with
# it before mounting, so only /mcp is gated (the rest of the FastAPI app is
# untouched).
# ---------------------------------------------------------------------------


class MCPBearerAuthMiddleware:
    """ASGI middleware: require a valid Bearer access token (issued by
    /oauth/token above) on every request to the wrapped app. Responds 401
    with a WWW-Authenticate header pointing at the RFC 9728 protected-
    resource metadata so MCP clients (Claude Desktop, etc.) can
    auto-discover the OAuth flow instead of failing silently."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        auth_header = request.headers.get("authorization", "")
        token = auth_header[7:] if auth_header.lower().startswith("bearer ") else None

        if token:
            try:
                decode_access_token(token)
                await self.app(scope, receive, send)
                return
            except Exception as exc:
                # Bắt rộng (không chỉ jwt.PyJWTError): decode_access_token()
                # cũng có thể raise HTTPException(500) qua _require_session_secret()
                # nếu OAUTH_SESSION_SECRET chưa cấu hình. Dù lý do gì, caller
                # chưa xác thực chỉ nên thấy 401 — không rò rỉ chi tiết lỗi
                # cấu hình server ra ngoài qua 1 request không token hợp lệ.
                logger.info(f"Rejected /mcp request: token invalid or unverifiable ({exc}).")

        base = str(request.base_url).rstrip("/")
        response = JSONResponse(
            {
                "error": "unauthorized",
                "error_description": "Missing or invalid bearer token. "
                "Authenticate via /oauth/authorize first.",
            },
            status_code=401,
            headers={
                "WWW-Authenticate": (
                    f'Bearer resource_metadata="{base}/.well-known/oauth-protected-resource/mcp"'
                )
            },
        )
        await response(scope, receive, send)
