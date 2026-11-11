"""Validated settings for the UI gateway and the browser app it serves."""

import os
from dataclasses import dataclass, replace
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
    SESSION_CACHE_ENTRIES: ClassVar[int] = 256

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
    # More links on the card, each as (the name of its check, its address).
    also: tuple[tuple[str, str], ...] = ()

    @property
    def icon_path(self) -> Path:
        return UIConfig.STATIC_DIR / "apps" / f"{self.key}.png"


def _app(key: str, name: str, description: str, ui_port: int) -> LunaApp:
    return LunaApp(
        key=key,
        name=name,
        description=description,
        checks=(
            # Every app answers here, Streamlit or React, until the React branches are all merged.
            ("UI", f"http://luna-{key}-ui:8501/_stcore/health"),
            ("MCP", f"http://luna-{key}-mcp:8000/health"),
        ),
        url=f"http://localhost:{ui_port}",
    )


# Every Luna stack, in the order luna.sh starts them, with Sentia last.
LUNA_APPS: tuple[LunaApp, ...] = (
    _app("visia", "Luna Visia", "Private image library. A local vision model captions and tags every upload, so assistants can search, edit, and share images.", 18505),
    _app("vita", "Luna Vita", "Nutrition, body measurements, and workouts, with daily targets and food logged from a chat.", 18506),
    _app("lumia", "Luna Lumia", "Smart-light control for WiZ bulbs: rooms, scenes, schedules, and lighting that follows the weather or the music.", 18502),
    _app("fiora", "Luna Fiora", "Personal finance from bank messages: income, spending, savings, categories, and cash flow by month.", 18500),
    _app("lexia", "Luna Lexia", "Vault for payslips, statements, and tax proofs, read and classified locally with their details extracted.", 18501),
    _app("vibia", "Luna Vibia", "Music library that listens to every track, captions and tags it, and builds playlists for a mood.", 18504),
    LunaApp(
        key="socia",
        name="Luna Socia",
        description="A private chat with Luna by text, voice, and photos; she sends pictures of herself. For the owner only; an early prototype.",
        # One service, the chat page and its API, with no MCP server.
        checks=(("UI", "http://luna-socia-ui:8501/health"),),
        url="http://localhost:18503",
    ),
    LunaApp(
        key="sentia",
        name="Luna Sentia",
        description="Shared PostgreSQL, Ollama models, ComfyUI, and single sign-on for every app. Opens user settings; Adminer browses the databases, the monitor shows model calls and the GPU, and ComfyUI makes pictures.",
        checks=(
            ("Sign-on", "http://luna-sentia-auth:8000/health"),
            ("Adminer", "http://luna-sentia-adminer:8080/"),
            ("Models", "http://luna-sentia-ollama:11434/api/version"),
            ("Monitor", "http://luna-sentia-monitor:8000/health"),
            ("ComfyUI", "http://luna-sentia-comfyui:8188/system_stats"),
        ),
        url="http://localhost:19000",
    ),
)


@dataclass(frozen=True)
class UIConfig:
    """Immutable gateway and service-detection settings."""

    UI_ROOT: ClassVar[Path] = Path(__file__).resolve().parent
    # The release this image holds, shown in the footer and on Luna Unia's cards.
    VERSION: ClassVar[str] = os.getenv("LUNA_VERSION", "").strip()
    # The built React app; the Dockerfile puts it here.
    STATIC_DIR: ClassVar[Path] = UI_ROOT / "static"
    # Each health check gives up after this long; all checks run at once.
    CHECK_TIMEOUT_SECONDS: ClassVar[float] = 2.0
    # The app grid checks every stack again this often while the page is open.
    REFRESH_SECONDS: ClassVar[int] = 15
    # Hashed bundles never change under the same name.
    IMMUTABLE_CACHE_CONTROL: ClassVar[str] = "private, max-age=31536000, immutable"
    CONTENT_SECURITY_POLICY: ClassVar[str] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    )

    allowed_emails: frozenset[str]
    sso: SSOConfig
    apps: tuple[LunaApp, ...] = LUNA_APPS

    @staticmethod
    def app_url(app: LunaApp) -> str:
        """The address browsers open for ``app``; for Sentia, its Adminer.

        LUNA<KEY>_URL wins; otherwise LUNAUNIA_URL_TEMPLATE with ``{app}`` replaced by the
        app's short name (for every app but Sentia, whose Adminer has no name in the
        pattern); otherwise the app's localhost port.
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

    @staticmethod
    def monitor_url() -> str:
        """Luna Sentia's model monitor: LUNASENTIA_MONITOR_URL, or its localhost port."""
        url = (os.getenv("LUNASENTIA_MONITOR_URL", "").strip() or "http://localhost:19004").rstrip("/")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError("LUNASENTIA_MONITOR_URL must be a valid HTTP(S) URL.")
        return url

    @staticmethod
    def comfyui_url() -> str:
        """Luna Sentia's ComfyUI page: LUNASENTIA_COMFYUI_URL, or its localhost port."""
        url = (os.getenv("LUNASENTIA_COMFYUI_URL", "").strip() or "http://localhost:19002").rstrip("/")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError("LUNASENTIA_COMFYUI_URL must be a valid HTTP(S) URL.")
        return url

    @classmethod
    def from_env(cls) -> "UIConfig":
        """Build and validate UI configuration from environment variables."""
        allowed_emails = frozenset(
            email.strip().casefold()
            for email in os.getenv("LUNAUNIA_ALLOWED_EMAILS", "").split(",")
            if email.strip()
        )
        sso = SSOConfig.from_env()
        apps = tuple(
            # Sentia's card opens its user settings, with links to Adminer (LUNASENTIA_URL),
            # the model monitor (LUNASENTIA_MONITOR_URL) and ComfyUI (LUNASENTIA_COMFYUI_URL).
            replace(app, url=f"{sso.public_url}/admin",
                    also=(("Adminer", cls.app_url(app)), ("Monitor", cls.monitor_url()), ("ComfyUI", cls.comfyui_url())))
            if app.key == "sentia"
            else replace(app, url=cls.app_url(app))
            for app in LUNA_APPS
        )
        return cls(allowed_emails=allowed_emails, sso=sso, apps=apps)
