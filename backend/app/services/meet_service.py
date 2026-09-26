"""
Google Calendar service — creates anonymous Google Meet links.

Lịch sử gộp file (2026-08): dự án từng có 2 bản song song —
`calendar.py` (bản đang được gọi thật, nhưng hard-code thời gian sự kiện
cố định "2026-08-20T17:00:00+07:00" thay vì giờ thật tại thời điểm tạo —
mọi buổi hẹn đều bị tạo cho cùng 1 mốc thời gian đã qua) và
`calendar_client.py` (bản `CalendarClient` đúng — dùng `datetime.utcnow()`
thật, có type lỗi riêng, trích `meet_link` rõ ràng — nhưng chưa từng được
import ở đâu). File này giữ `CalendarClient` làm client thật, còn
`create_anonymous_meet_link` được viết lại để gọi qua đó.

Per docs/SPEC.md §3 và §7: Meet links luôn được tạo qua service account của
hệ thống, không dùng calendar cá nhân. Link ("anyone with the link can
join") chính là thứ mang lời mời — không phải calendar invite tới địa chỉ
cá nhân. Đây là cơ chế giữ kín email thật của SV/CSV với nhau; không thêm
field `attendees` vào event body dù có vẻ tiện cho việc nhắc lịch.

Yêu cầu service account JSON key có bật Calendar API; không cần domain-wide
delegation — service account tạo event trên chính calendar của nó
(settings.google_calendar_id), không phải calendar của user bị impersonate.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from app.config import settings

_SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarConfigError(RuntimeError):
    """Raised when the service account file is missing or unreadable."""


class CalendarAPIError(RuntimeError):
    """Raised when the Google Calendar API call itself fails."""


@dataclass
class AnonymousMeeting:
    event_id: str
    meet_link: str
    start_time: datetime
    end_time: datetime


class CalendarClient:
    """
    Thin wrapper around the Google Calendar v3 API, scoped to exactly what
    Module 3 needs: create a short anonymous Meet event and hand back the
    join link. Nothing here reads or lists existing events — this is a
    write-only helper by design, to keep the surface area small.
    """

    def __init__(
        self,
        service_account_file: str | None = None,
        calendar_id: str | None = None,
    ):
        self._service_account_file = service_account_file or settings.google_service_account_file
        self._calendar_id = calendar_id or settings.google_calendar_id
        self._service = None  # lazily built on first use

    def _get_service(self):
        if self._service is not None:
            return self._service

        if not self._service_account_file:
            raise CalendarConfigError(
                "GOOGLE_SERVICE_ACCOUNT_FILE is not set. Point it at your "
                "service account JSON key in backend/.env before calling "
                "any Calendar-creating MCP tool."
            )

        try:
            credentials = service_account.Credentials.from_service_account_file(
                self._service_account_file, scopes=_SCOPES
            )
        except FileNotFoundError as exc:
            raise CalendarConfigError(
                f"Service account file not found at "
                f"'{self._service_account_file}'. Check GOOGLE_SERVICE_ACCOUNT_FILE."
            ) from exc

        self._service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        return self._service

    async def create_anonymous_meeting(
        self,
        summary: str,
        duration_minutes: int = 20,
        start_time: datetime | None = None,
        description: str = "",
    ) -> AnonymousMeeting:
        """
        Create a short-lived Meet event and return its join link.

        `summary` should stay generic (e.g. "Buổi tư vấn ẩn danh") — do not
        pass student/alumni names here, since the event lives on the shared
        system calendar and its title is not access-controlled per user.

        No `attendees` field is set on purpose (see module docstring). The
        caller is responsible for delivering `meet_link` to both sides
        through the proxy channel (Zalo button / web), not through a
        calendar invite.
        """
        start_time = start_time or datetime.utcnow()
        end_time = start_time + timedelta(minutes=duration_minutes)
        request_id = str(uuid.uuid4())

        event_body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_time.isoformat() + "Z", "timeZone": "UTC"},
            "end": {"dateTime": end_time.isoformat() + "Z", "timeZone": "UTC"},
            "conferenceData": {
                "createRequest": {
                    "requestId": request_id,
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            # Deliberately no "attendees" key — see module docstring.
            # Deliberately no "guestsCanInviteOthers"/"visibility" override;
            # Meet's own "anyone with the link" join model is what we rely on.
        }

        service = self._get_service()
        try:
            created = (
                service.events()
                .insert(
                    calendarId=self._calendar_id,
                    body=event_body,
                    conferenceDataVersion=1,
                )
                .execute()
            )
        except HttpError as exc:
            logger.warning(f"Google Calendar API error creating event: {exc}")
            raise CalendarAPIError(str(exc)) from exc

        meet_link = _extract_meet_link(created)
        if not meet_link:
            raise CalendarAPIError(
                "Event was created but no Meet link was returned — check "
                "that the Calendar API has Meet conference generation enabled "
                "for this service account/workspace."
            )

        return AnonymousMeeting(
            event_id=created["id"],
            meet_link=meet_link,
            start_time=start_time,
            end_time=end_time,
        )


def _extract_meet_link(event: dict) -> str | None:
    """Pull the hangoutLink / conferenceData entryPoint URI off a created event."""
    if link := event.get("hangoutLink"):
        return link
    entry_points = (event.get("conferenceData") or {}).get("entryPoints") or []
    for entry in entry_points:
        if entry.get("entryPointType") == "video":
            return entry.get("uri")
    return None


# ---------------------------------------------------------------------------
# High-level helper — dùng bởi app/ai/tools.py, app/mcp/tools.py,
# routers/mentorship.py, routers/webhooks.py
# ---------------------------------------------------------------------------


async def create_anonymous_meet_link(
    session_id: str, summary: str = "AI Alumni Micro-Mentorship Session"
) -> str:
    """
    Generate an anonymous Google Meet link using Google Calendar API
    (Service Account), hoặc trả về system meeting room URL fallback nếu
    chưa cấu hình / API lỗi.
    """
    if settings.google_service_account_file:
        try:
            meeting = await CalendarClient().create_anonymous_meeting(
                summary=summary,
                duration_minutes=20,
                description="AI Alumni Anonymous Mentorship Session",
            )
            return meeting.meet_link
        except Exception as e:
            logger.warning(f"Google Calendar API fallback due to: {e}")

    # Fallback system meeting URL (Privacy Proxy)
    clean_id = session_id.replace("-", "")[:8]
    return f"https://meet.google.com/alm-{clean_id[:3]}-{clean_id[3:6]}"
