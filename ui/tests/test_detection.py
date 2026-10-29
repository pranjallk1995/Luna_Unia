import os
import unittest
from unittest.mock import patch

import httpx

from config import LUNA_APPS, UIConfig
from services.detection import AppState, ServiceDetector

BASE_ENV = {"LUNA_SSO_URL": "https://auth.example.com", "LUNAUNIA_ALLOWED_EMAILS": "owner@example.com"}


def detector(up: set[str]) -> ServiceDetector:
    """A detector whose network answers only for the hosts in ``up``."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host in up:
            return httpx.Response(200, text="ok")
        raise httpx.ConnectError("unreachable", request=request)

    return ServiceDetector(timeout=1, transport=httpx.MockTransport(handler))


class DetectionTests(unittest.TestCase):
    def test_app_is_running_degraded_or_offline_by_its_ui_and_services(self):
        statuses = {
            status.app.key: status
            for status in detector({"luna-visia-ui", "luna-visia-mcp", "luna-vita-ui"}).detect(LUNA_APPS)
        }
        self.assertIs(statuses["visia"].state, AppState.RUNNING)
        self.assertIs(statuses["vita"].state, AppState.DEGRADED)
        self.assertEqual(statuses["vita"].down, ("MCP",))
        self.assertTrue(statuses["vita"].can_open)
        self.assertIs(statuses["lumia"].state, AppState.OFFLINE)
        self.assertFalse(statuses["lumia"].can_open)

    def test_server_errors_count_as_down(self):
        failing = ServiceDetector(timeout=1, transport=httpx.MockTransport(lambda request: httpx.Response(503)))
        self.assertTrue(all(status.state is AppState.OFFLINE for status in failing.detect(LUNA_APPS)))

    def test_sentia_opens_adminer_and_reports_its_services(self):
        status = detector({"luna-sentia-adminer", "luna-sentia-auth"}).detect(LUNA_APPS)[-1]
        self.assertEqual(status.app.key, "sentia")
        self.assertIs(status.state, AppState.DEGRADED)
        self.assertEqual(status.down, ("Models",))


class AppUrlTests(unittest.TestCase):
    def test_urls_default_to_localhost_ports_and_can_be_overridden(self):
        with patch.dict(os.environ, {**BASE_ENV, "LUNAVIBIA_URL": "https://vibia.example.com/"}, clear=True):
            urls = {app.key: app.url for app in UIConfig.from_env().apps}
        self.assertEqual(urls["visia"], "http://localhost:18501")
        self.assertEqual(urls["vibia"], "https://vibia.example.com")
        self.assertEqual(urls["sentia"], "http://localhost:19080")

    def test_template_names_every_app_but_sentia(self):
        env = {**BASE_ENV, "LUNAUNIA_URL_TEMPLATE": "https://{app}.example.com", "LUNALEXIA_URL": "https://docs.example.com"}
        with patch.dict(os.environ, env, clear=True):
            urls = {app.key: app.url for app in UIConfig.from_env().apps}
        self.assertEqual(urls["vita"], "https://vita.example.com")
        self.assertEqual(urls["lexia"], "https://docs.example.com")
        self.assertEqual(urls["sentia"], "http://localhost:19080")

    def test_invalid_url_is_rejected(self):
        with patch.dict(os.environ, {**BASE_ENV, "LUNAVITA_URL": "vita.example.com"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "LUNAVITA_URL"):
                UIConfig.from_env()

    def test_every_app_has_an_icon(self):
        for app in LUNA_APPS:
            self.assertTrue(app.icon_path.is_file(), app.icon_path)


if __name__ == "__main__":
    unittest.main()
