import types
from dataclasses import replace
import unittest

import httpx
from starlette.testclient import TestClient

from config import LUNA_APPS, SSOConfig, UIConfig
from gateway import UIGateway
from sso import LunaSingleSignOn
from services.detection import AppState, AppStatus

OWNER = {"user_id": "owner", "email": "owner@example.com", "email_verified": True}
STRANGER = {"email": "other@example.com", "email_verified": True}


class GatewayTestCase(unittest.TestCase):
    def setUp(self):
        self.up = {"luna-visia-ui", "luna-visia-mcp", "luna-vita-ui"}

        def sso(request: httpx.Request) -> httpx.Response:
            session = {"owner": OWNER, "stranger": STRANGER}.get(request.headers["X-Luna-Session"])
            return httpx.Response(200, json=session) if session else httpx.Response(401)

        def checks(request: httpx.Request) -> httpx.Response:
            if request.url.host in self.up:
                return httpx.Response(200, text="ok")
            raise httpx.ConnectError("unreachable", request=request)

        config = UIConfig(allowed_emails=frozenset({"owner@example.com"}), sso=SSOConfig(public_url="https://auth.example.com"))
        gateway = UIGateway(config, httpx.MockTransport(checks), httpx.MockTransport(sso))
        self.client = TestClient(gateway.application(), base_url="https://unia.example.com")

    def sign_in(self, who: str = "owner") -> None:
        self.client.cookies.set(SSOConfig.COOKIE_NAME, who)

    def test_signed_out_gets_a_login_link_back_to_this_app(self):
        session = self.client.get("/auth/session").json()
        self.assertEqual(session["login_url"], "https://auth.example.com/login?next=https%3A%2F%2Funia.example.com%2F")

    def test_allowed_person_gets_the_refresh_setting(self):
        self.sign_in()
        session = self.client.get("/auth/session").json()
        self.assertEqual(session["settings"]["refresh_seconds"], UIConfig.REFRESH_SECONDS)

    def test_statuses_need_an_allowed_session(self):
        self.assertEqual(self.client.get("/app/status").status_code, 401)
        self.sign_in("stranger")
        self.assertEqual(self.client.get("/app/status").status_code, 403)

    def test_statuses_report_every_stack(self):
        self.sign_in()
        apps = {app["key"]: app for app in self.client.get("/app/status").json()["apps"]}
        self.assertEqual(set(apps), {app.key for app in LUNA_APPS})
        self.assertEqual((apps["visia"]["state"], apps["visia"]["status"]), ("running", "Running"))
        self.assertEqual((apps["vita"]["state"], apps["vita"]["status"]), ("degraded", "MCP not responding"))
        self.assertTrue(apps["vita"]["can_open"])
        self.assertEqual((apps["lumia"]["state"], apps["lumia"]["status"]), ("offline", "Not running"))
        self.assertFalse(apps["lumia"]["can_open"])
        self.assertEqual(apps["visia"]["host"], "localhost:18505")

    def test_offline_ui_with_a_live_service_names_the_ui(self):
        status = AppStatus(LUNA_APPS[0], AppState.OFFLINE, ("UI",))
        self.assertEqual(UIGateway.status_label(status), "UI not responding")

    def test_health_and_security_headers(self):
        headers = self.client.get("/health").headers
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])


class VisibleAppTests(unittest.TestCase):
    def visible(self, user):
        gateway = UIGateway.__new__(UIGateway)
        gateway.config, gateway.sso = types.SimpleNamespace(apps=LUNA_APPS), LunaSingleSignOn
        return {app.key for app in gateway.visible_apps(user)}

    def test_others_see_only_what_they_can_use(self):
        seen = self.visible({"user_id": "ab12", "hidden_apps": ["lumia"]})
        self.assertNotIn("lumia", seen)
        self.assertNotIn("sentia", seen)
        self.assertNotIn("socia", seen)
        self.assertIn("visia", seen)

    def test_each_other_link_goes_while_its_service_is_down(self):
        app = replace(LUNA_APPS[-1], also=(("Adminer", "http://localhost:19000"), ("Monitor", "http://localhost:19003")))
        links = UIGateway.also_links(AppStatus(app, AppState.RUNNING))
        self.assertEqual(links, [{"name": "Adminer", "url": "http://localhost:19000", "host": "localhost:19000"},
                                 {"name": "Monitor", "url": "http://localhost:19003", "host": "localhost:19003"}])
        self.assertEqual([link["name"] for link in UIGateway.also_links(AppStatus(app, AppState.DEGRADED, ("Adminer",)))], ["Monitor"])
        self.assertEqual(UIGateway.also_links(AppStatus(LUNA_APPS[0], AppState.RUNNING)), [])

    def test_the_owner_sees_everything(self):
        self.assertEqual(self.visible({"user_id": "owner", "hidden_apps": []}), {app.key for app in LUNA_APPS})


if __name__ == "__main__":
    unittest.main()
