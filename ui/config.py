"""Validated presentation and service settings for the Streamlit UI."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlparse


@dataclass(frozen=True)
class SSOConfig:
    """Single sign-on through Luna Sentia; this block is identical in every Luna app's config.py."""

    COOKIE_NAME: ClassVar[str] = "luna_sso"
    SESSION_HEADER: ClassVar[str] = "X-Luna-Session"
    # How long a confirmed session is trusted before asking Sentia again, so a sign-out
    # in another app takes effect here within this many seconds.
    RECHECK_SECONDS: ClassVar[int] = 60
    LOOKUP_TIMEOUT_SECONDS: ClassVar[float] = 5.0

    public_url: str
    internal_url: str = "http://luna-sentia-auth:8000"

    @classmethod
    def from_env(cls) -> "SSOConfig":
        public_url = os.getenv("LUNA_SSO_URL", "").strip().rstrip("/")
        if not public_url:
            raise RuntimeError("LUNA_SSO_URL must be the public address of Luna Sentia's auth service.")
        internal_url = os.getenv("LUNA_SSO_INTERNAL_URL", "").strip().rstrip("/")
        return cls(public_url=public_url, internal_url=internal_url or cls.internal_url)


@dataclass(frozen=True)
class LunaApp:
    """One Luna stack Unia looks for on luna_sentia_network, and where people open it."""

    key: str
    name: str
    description: str
    # Addresses on luna_sentia_network that answer when the stack is running. The first
    # is the stack's UI; the rest are the services it needs (its MCP, or Sentia's parts).
    checks: tuple[tuple[str, str], ...]
    # The address browsers open when neither LUNA<KEY>_URL nor LUNAUNIA_URL_TEMPLATE sets one.
    url: str

    @property
    def icon_path(self) -> Path:
        return UIConfig.UI_ROOT / "assets" / "apps" / f"{self.key}.png"


def _app(key: str, name: str, description: str, ui_port: int) -> LunaApp:
    return LunaApp(
        key=key,
        name=name,
        description=description,
        checks=(
            ("UI", f"http://luna-{key}-ui:8501/_stcore/health"),
            ("MCP", f"http://luna-{key}-mcp:8000/health"),
        ),
        url=f"http://localhost:{ui_port}",
    )


# Every Luna stack, in the order luna.sh starts them, with Sentia last.
LUNA_APPS: tuple[LunaApp, ...] = (
    _app("visia", "Luna Visia", "Private image library. A local vision model captions and tags every upload, so assistants can search, edit, and share images.", 18501),
    _app("vita", "Luna Vita", "Nutrition, body measurements, and workouts, with daily targets and food logged from a chat.", 18502),
    _app("lumia", "Luna Lumia", "Smart-light control for WiZ bulbs: rooms, scenes, schedules, and weather-driven lighting schemes.", 18503),
    _app("fiora", "Luna Fiora", "Personal finance from bank messages: income, spending, savings, categories, and cash flow by month.", 18504),
    _app("lexia", "Luna Lexia", "Vault for payslips, statements, and tax proofs, read and classified locally with their details extracted.", 18505),
    _app("vibia", "Luna Vibia", "Music library that listens to every track, captions and tags it, and builds playlists for a mood.", 18506),
    LunaApp(
        key="sentia",
        name="Luna Sentia",
        description="Shared PostgreSQL, Ollama models, and single sign-on for every app. Opens Adminer to browse the databases.",
        checks=(
            ("Adminer", "http://luna-sentia-adminer:8080/"),
            ("Sign-on", "http://luna-sentia-auth:8000/health"),
            ("Models", "http://luna-sentia-ollama:11434/api/version"),
        ),
        url="http://localhost:19080",
    ),
)


@dataclass(frozen=True)
class UIConfig:
    """Immutable UI layout and service-detection settings."""

    UI_ROOT: ClassVar[Path] = Path(__file__).resolve().parent
    LOGO_PATH: ClassVar[Path] = UI_ROOT / "assets" / "lunaunia_logo.png"
    # Each health check gives up after this long; all checks run at once.
    CHECK_TIMEOUT_SECONDS: ClassVar[float] = 2.0
    # The app grid checks every stack again this often while the page is open.
    REFRESH_SECONDS: ClassVar[int] = 15

    allowed_emails: frozenset[str]
    sso: SSOConfig
    apps: tuple[LunaApp, ...] = LUNA_APPS

    @staticmethod
    def app_url(app: LunaApp) -> str:
        """The address browsers open for ``app``.

        LUNA<KEY>_URL wins; otherwise LUNAUNIA_URL_TEMPLATE with ``{app}`` replaced by the
        app's short name (for every app but Sentia, whose Adminer is only on localhost);
        otherwise the app's localhost port.
        """
        url = os.getenv(f"LUNA{app.key.upper()}_URL", "").strip()
        template = os.getenv("LUNAUNIA_URL_TEMPLATE", "").strip()
        if not url and template and app.key != "sentia":
            url = template.replace("{app}", app.key)
        url = (url or app.url).rstrip("/")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError(f"LUNA{app.key.upper()}_URL must be a valid HTTP(S) URL.")
        return url

    @classmethod
    def from_env(cls) -> "UIConfig":
        """Build and validate UI configuration from environment variables."""
        allowed_emails = frozenset(
            email.strip().casefold()
            for email in os.getenv("LUNAUNIA_ALLOWED_EMAILS", "").split(",")
            if email.strip()
        )
        if not allowed_emails:
            raise RuntimeError("LUNAUNIA_ALLOWED_EMAILS must list at least one account.")
        apps = tuple(
            LunaApp(app.key, app.name, app.description, app.checks, cls.app_url(app)) for app in LUNA_APPS
        )
        return cls(allowed_emails=allowed_emails, sso=SSOConfig.from_env(), apps=apps)
