"""Luna Unia Streamlit application entry point."""

import base64
import html
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
from PIL import Image

from config import UIConfig
from services.detection import AppState, AppStatus, ServiceDetector
from sso import LunaSingleSignOn
from styles import LunaStyle

# Material "north_east": the card opens its app.
OPEN_ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M9 5v2h6.59L4 18.59 5.41 20 17 8.41V15h2V5H9z"/></svg>'
)


class AppGrid:
    """The cards of every Luna stack, checked again every few seconds while open."""

    def __init__(self, config: UIConfig) -> None:
        self.config = config
        self.detector = ServiceDetector(UIConfig.CHECK_TIMEOUT_SECONDS)

    @staticmethod
    @lru_cache(maxsize=None)
    def icon_data(path: Path) -> str:
        return base64.b64encode(path.read_bytes()).decode("ascii")

    @staticmethod
    def status_label(status: AppStatus) -> str:
        if status.state is AppState.RUNNING:
            return "Running"
        if status.state is AppState.OFFLINE and len(status.down) == len(status.app.checks):
            return "Not running"
        return f"{', '.join(status.down)} not responding"

    @classmethod
    def card(cls, status: AppStatus) -> str:
        app = status.app
        host = urlparse(app.url).netloc
        body = (
            f'<div class="lu-top"><img class="lu-icon" src="data:image/png;base64,{cls.icon_data(app.icon_path)}" alt="">'
            f'<div class="lu-heading"><span class="lu-name">{html.escape(app.name)}</span>'
            f'<span class="lu-status">{html.escape(cls.status_label(status))}</span></div></div>'
            f'<p class="lu-desc">{html.escape(app.description)}</p>'
        )
        classes = f"lu-card lu-{status.state.value}"
        if not status.can_open:
            return f'<div class="{classes}" aria-disabled="true">{body}<div class="lu-link"><span>{html.escape(host)}</span></div></div>'
        return (
            f'<a class="{classes}" href="{html.escape(app.url)}" target="_blank" rel="noopener" aria-label="Open {html.escape(app.name)}">'
            f'{body}<div class="lu-link"><span>{html.escape(host)}</span>{OPEN_ICON}</div></a>'
        )

    def render(self) -> None:
        statuses = self.detector.detect(self.config.apps)
        running = sum(status.can_open for status in statuses)
        st.markdown(
            f'<div class="lu-summary"><span><strong>{running} of {len(statuses)}</strong> Luna stacks running</span>'
            f"<span>Checked again every {UIConfig.REFRESH_SECONDS} seconds · open an app to go to it</span></div>"
            f'<div class="lu-grid">{"".join(self.card(status) for status in statuses)}</div>',
            unsafe_allow_html=True,
        )


class LunaUniaApp:
    """Compose and render the Luna Unia Streamlit interface."""

    def __init__(self) -> None:
        self.config = UIConfig.from_env()

    @staticmethod
    def logo_markup(logo_path: Path) -> str:
        logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
        return f'<img class="lv-mark" src="data:image/png;base64,{logo_data}" alt="Luna Unia logo">'

    def render_header(self) -> None:
        """Render the branded header and its controls.

        Nothing that creates a layout block may render before this header; see
        UI_STYLE_GUIDE.md ("Header-position invariant").
        """
        brand_column, buttons_column = st.columns([5, 4], vertical_alignment="center", gap="medium")
        with brand_column:
            st.markdown(
                f"""
                <div class="lv-header">
                    {self.logo_markup(UIConfig.LOGO_PATH)}
                    <div>
                        <h1 class="lv-title">Luna Unia</h1>
                        <p class="lv-subtitle">Private AI-managed home for every Luna app</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with buttons_column:
            refresh_column, sign_out_column = st.columns([3, 2], vertical_alignment="center", gap="small")
            # A click reruns the page, which checks every stack again.
            refresh_column.button(
                "Check again", icon=":material/refresh:", type="primary", key="refresh_apps", width="stretch"
            )
            sign_out_column.button(
                "Sign out",
                icon=":material/logout:",
                key="header_sign_out",
                on_click=LunaSingleSignOn.sign_out,
                width="stretch",
            )

    def render(self) -> None:
        LunaStyle.apply()
        LunaSingleSignOn(self.config.allowed_emails, self.config.sso).require_login(
            "Luna Unia", "Private AI-managed home for every Luna app"
        )
        self.render_header()
        st.fragment(AppGrid(self.config).render, run_every=UIConfig.REFRESH_SECONDS)()

    @classmethod
    def run(cls) -> None:
        st.set_page_config(
            page_title="Luna Unia",
            page_icon=Image.open(UIConfig.LOGO_PATH),
            layout="wide",
            initial_sidebar_state="collapsed",
        )
        cls().render()


if __name__ == "__main__":
    LunaUniaApp.run()
