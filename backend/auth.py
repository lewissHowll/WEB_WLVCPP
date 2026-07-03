"""Site-wide HTTP Basic Auth.

Protects everything — the API and the built frontend — behind a single
username/password, read from environment variables so credentials never
live in the repo.

Credentials come from APP_USERNAME / APP_PASSWORD. If either is unset,
auth is disabled (so local dev stays friction-free) and a warning is
logged loudly at startup. Set both in your hosting provider's dashboard
(e.g. Render's Environment tab) for any deployment you want locked down.

/api/health is always left open, so uptime checks / load balancers don't
need credentials.
"""
import base64
import logging
import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("uvicorn.error")

APP_USERNAME = os.environ.get("APP_USERNAME")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
AUTH_ENABLED = bool(APP_USERNAME and APP_PASSWORD)

UNPROTECTED_PATHS = {"/api/health"}


class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not AUTH_ENABLED or request.url.path in UNPROTECTED_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("authorization")
        if auth_header and self._is_valid(auth_header):
            return await call_next(request)

        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="WLVCPP"'},
            content="Authentication required.",
        )

    @staticmethod
    def _is_valid(auth_header: str) -> bool:
        try:
            scheme, credentials = auth_header.split(" ", 1)
            if scheme.lower() != "basic":
                return False
            decoded = base64.b64decode(credentials).decode("utf-8")
            username, _, password = decoded.partition(":")
        except (ValueError, UnicodeDecodeError):
            return False

        # constant-time comparisons to avoid timing side-channels
        user_ok = secrets.compare_digest(username, APP_USERNAME)
        pass_ok = secrets.compare_digest(password, APP_PASSWORD)
        return user_ok and pass_ok


if not AUTH_ENABLED:
    logger.warning(
        "APP_USERNAME / APP_PASSWORD not set — the site is running WITHOUT "
        "password protection. Set both env vars to lock it down."
    )
