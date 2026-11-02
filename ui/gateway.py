"""The UI gateway: serves the React app, enforces sign-in, and fronts the backend.

Every data route checks the shared Luna session and this app's allowlist first.
Unia has no backend of its own: it asks each stack's services whether they answer.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlparse

import anyio
import httpx
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from config import SSOConfig, UIConfig
from services.detection import AppState, AppStatus, ServiceDetector
from sso import LunaSingleSignOn


class StaticApp(StaticFiles):
    """Serve the built app: hashed bundles are cached forever, the page itself never."""

    async def get_response(self, path: str, scope: Any) -> Response:
        response = await super().get_response(path, scope)
        immutable = path.startswith("assets/")
        response.headers["Cache-Control"] = UIConfig.IMMUTABLE_CACHE_CONTROL if immutable else "no-cache"
        return response


class UIGateway:
    """Translate browser requests into session checks and service checks."""

    def __init__(
        self,
        config: UIConfig,
        check_transport: httpx.BaseTransport | None = None,
        sso_transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.config = config
        self.sso = LunaSingleSignOn(config.allowed_emails, config.sso, sso_transport)
        self.detector = ServiceDetector(UIConfig.CHECK_TIMEOUT_SECONDS, check_transport)

    # Sign-in

    @staticmethod
    def here(request: Request) -> str:
        """This app's public address. Behind a TLS-terminating proxy such as a Cloudflare
        tunnel, the proxy's X-Forwarded-Proto and X-Forwarded-Host give the real one."""
        headers = request.headers
        scheme = headers.get("x-forwarded-proto", "").split(",")[0].strip() or request.url.scheme
        host = headers.get("x-forwarded-host", "").split(",")[0].strip() or request.url.netloc
        return f"{scheme}://{host}/"

    async def person(self, request: Request) -> dict[str, Any] | None:
        return await self.sso.user(request.cookies.get(SSOConfig.COOKIE_NAME))

    def protected(self, handler: Callable[[Request], Awaitable[Response]]):
        """Run ``handler`` only for a signed-in person on this app's allowlist."""

        async def endpoint(request: Request) -> Response:
            user = await self.person(request)
            if user is None:
                return JSONResponse({"error": "Sign in to continue."}, status_code=401)
            if not self.sso.is_allowed(user):
                return JSONResponse({"error": "This account is not authorized."}, status_code=403)
            return await handler(request)

        return endpoint

    async def session(self, request: Request) -> Response:
        """Tell the browser app who is signed in."""
        here = self.here(request)
        user = await self.person(request)
        if user is None:
            return JSONResponse({"status": "signed_out", "login_url": self.sso.login_url(here)})
        logout_url = self.sso.logout_url(here)
        if not self.sso.is_allowed(user):
            return JSONResponse({"status": "forbidden", "email": user.get("email"), "logout_url": logout_url})
        return JSONResponse({"status": "signed_in", "email": user.get("email"), "logout_url": logout_url, "settings": {"refresh_seconds": UIConfig.REFRESH_SECONDS}})

    # Stacks

    @staticmethod
    def status_label(status: AppStatus) -> str:
        if status.state is AppState.RUNNING:
            return "Running"
        if status.state is AppState.OFFLINE and len(status.down) == len(status.app.checks):
            return "Not running"
        return f"{', '.join(status.down)} not responding"

    async def statuses(self, request: Request) -> Response:
        """Ask every stack now, so each answer is as fresh as the page's refresh."""
        statuses = await anyio.to_thread.run_sync(self.detector.detect, self.config.apps)
        return JSONResponse(
            {
                "apps": [
                    {
                        "key": status.app.key,
                        "name": status.app.name,
                        "description": status.app.description,
                        "url": status.app.url,
                        "host": urlparse(status.app.url).netloc,
                        "state": status.state.value,
                        "status": self.status_label(status),
                        "can_open": status.can_open,
                    }
                    for status in statuses
                ]
            },
            headers={"Cache-Control": "no-store"},
        )

    # Application

    @staticmethod
    async def health(request: Request) -> Response:
        return JSONResponse({"status": "ok"})

    def application(self) -> Starlette:
        app = Starlette(
            routes=[
                Route("/health", self.health),
                Route("/auth/session", self.session),
                Route("/app/status", self.protected(self.statuses)),
                Mount("/", StaticApp(directory=UIConfig.STATIC_DIR, html=True, check_dir=False)),
            ]
        )

        async def secure_headers(request: Request, call_next) -> Response:
            response = await call_next(request)
            response.headers["Content-Security-Policy"] = UIConfig.CONTENT_SECURITY_POLICY
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        app.add_middleware(BaseHTTPMiddleware, dispatch=secure_headers)
        return app


def create_app() -> Starlette:
    return UIGateway(UIConfig.from_env()).application()
