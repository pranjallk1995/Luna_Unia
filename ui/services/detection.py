"""Find which Luna stacks are running by asking their services over luna_sentia_network."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

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

    @property
    def can_open(self) -> bool:
        return self.state is not AppState.OFFLINE


class ServiceDetector:
    """Run every app's health checks at once and summarize each app."""

    def __init__(self, timeout: float, transport: httpx.BaseTransport | None = None) -> None:
        self.timeout = timeout
        self.transport = transport

    @staticmethod
    def answers(client: httpx.Client, url: str) -> bool:
        try:
            return client.get(url).status_code < 500
        except httpx.HTTPError:
            return False

    @staticmethod
    def summarize(app: LunaApp, results: dict[str, bool]) -> AppStatus:
        down = tuple(name for name, _ in app.checks if not results[name])
        first_check = app.checks[0][0]
        if not results[first_check]:
            return AppStatus(app, AppState.OFFLINE, down)
        return AppStatus(app, AppState.DEGRADED if down else AppState.RUNNING, down)

    def detect(self, apps: tuple[LunaApp, ...]) -> list[AppStatus]:
        checks = [(app.key, name, url) for app in apps for name, url in app.checks]
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            with ThreadPoolExecutor(max_workers=len(checks)) as pool:
                answered = list(pool.map(lambda check: self.answers(client, check[2]), checks))
        results: dict[str, dict[str, bool]] = {app.key: {} for app in apps}
        for (key, name, _), ok in zip(checks, answered):
            results[key][name] = ok
        return [self.summarize(app, results[app.key]) for app in apps]
