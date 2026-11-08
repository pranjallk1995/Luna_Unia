"""Find which Luna stacks are running by asking their services over luna_sentia_network."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple

import httpx

from config import LunaApp


class AppState(str, Enum):
    RUNNING = "running"
    # The UI answers but a service behind it does not; the app opens with errors.
    DEGRADED = "degraded"
    OFFLINE = "offline"


@dataclass(frozen=True)
class AppStatus:
    app: LunaApp
    state: AppState
    # Names of the checks that did not answer, such as ("MCP",).
    down: tuple[str, ...] = ()
    # The release the stack reports; blank while it is offline or too old to say.
    version: str = ""

    @property
    def can_open(self) -> bool:
        return self.state is not AppState.OFFLINE


class Answer(NamedTuple):
    ok: bool
    version: str = ""


class ServiceDetector:
    """Run every app's health checks at once and summarize each app."""

    def __init__(self, timeout: float, transport: httpx.BaseTransport | None = None) -> None:
        self.timeout = timeout
        self.transport = transport

    @staticmethod
    def reported_version(response: httpx.Response) -> str:
        """The release a health answer names; images older than this feature name none."""
        try:
            body = response.json()
        except ValueError:
            return ""
        version = body.get("version") if isinstance(body, dict) else None
        return version if isinstance(version, str) else ""

    @classmethod
    def ask(cls, client: httpx.Client, url: str) -> Answer:
        try:
            response = client.get(url)
        except httpx.HTTPError:
            return Answer(False)
        return Answer(response.status_code < 500, cls.reported_version(response))

    @staticmethod
    def summarize(app: LunaApp, results: dict[str, Answer]) -> AppStatus:
        down = tuple(name for name, _ in app.checks if not results[name].ok)
        # Only the stack's own first service speaks for its release; Ollama's version is Ollama's.
        first = results[app.checks[0][0]]
        if not first.ok:
            return AppStatus(app, AppState.OFFLINE, down)
        return AppStatus(app, AppState.DEGRADED if down else AppState.RUNNING, down, first.version)

    def detect(self, apps: tuple[LunaApp, ...]) -> list[AppStatus]:
        checks = [(app.key, name, url) for app in apps for name, url in app.checks]
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            with ThreadPoolExecutor(max_workers=len(checks)) as pool:
                answered = list(pool.map(lambda check: self.ask(client, check[2]), checks))
        results: dict[str, dict[str, Answer]] = {app.key: {} for app in apps}
        for (key, name, _), answer in zip(checks, answered):
            results[key][name] = answer
        return [self.summarize(app, results[app.key]) for app in apps]
