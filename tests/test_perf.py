"""Lightweight performance check: critical endpoints respond within threshold."""
import time

import pytest
from fastapi.testclient import TestClient


def _get_elapsed(client: TestClient, path: str, headers: dict | None = None, iterations: int = 5) -> list[float]:
    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        client.get(path, headers=headers or {})
        times.append(time.perf_counter() - start)
    return times


@pytest.mark.integration
def test_health_response_time(client: TestClient) -> None:
    times = _get_elapsed(client, "/api/health")
    avg_ms = sum(times) / len(times) * 1000
    assert avg_ms < 500, f"Health avg {avg_ms:.0f}ms exceeds 500ms"


@pytest.mark.integration
def test_settings_response_time(client: TestClient, auth_headers: dict[str, str]) -> None:
    times = _get_elapsed(client, "/api/settings", headers=auth_headers)
    avg_ms = sum(times) / len(times) * 1000
    assert avg_ms < 1000, f"Settings avg {avg_ms:.0f}ms exceeds 1000ms"
