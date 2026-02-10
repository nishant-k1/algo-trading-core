"""Negative and error-path tests: 4xx, validation, not-found."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_get_nonexistent_watchlist_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.get("/api/watchlists/999999", headers=auth_headers)
    assert r.status_code == 404
    assert "detail" in r.json()


@pytest.mark.integration
def test_patch_nonexistent_watchlist_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.patch("/api/watchlists/999999", headers=auth_headers, json={"name": "X"})
    assert r.status_code == 404


@pytest.mark.integration
def test_delete_nonexistent_watchlist_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.delete("/api/watchlists/999999", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.integration
def test_create_strategy_config_with_nonexistent_watchlist_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.post(
        "/api/strategies/configs",
        headers=auth_headers,
        json={
            "name": "Test",
            "strategy_key": "previous_high_breakout",
            "watchlist_id": 999999,
        },
    )
    assert r.status_code == 404


@pytest.mark.integration
def test_run_strategy_without_active_config_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    configs = client.get("/api/strategies/configs", headers=auth_headers).json()
    for c in configs:
        if c.get("is_active"):
            client.patch(
                f"/api/strategies/configs/{c['id']}",
                headers=auth_headers,
                json={"is_active": False},
            )
    r = client.post("/api/strategies/run", headers=auth_headers)
    assert r.status_code == 400
    data = r.json()
    assert "detail" in data
    assert "active" in data["detail"].lower() or "config" in data["detail"].lower()


@pytest.mark.integration
def test_validation_error_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.post(
        "/api/strategies/configs",
        headers=auth_headers,
        json={
            "name": "Test",
            "strategy_key": "previous_high_breakout",
            "watchlist_id": -1,
        },
    )
    assert r.status_code in (400, 404, 422)


@pytest.mark.integration
def test_screener_requires_auth(client: TestClient) -> None:
    r = client.get("/api/screener/gainers")
    assert r.status_code == 401


@pytest.mark.integration
def test_invalid_limit_returns_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get("/api/screener/gainers?limit=0", headers=auth_headers)
    assert r.status_code == 422


@pytest.mark.integration
def test_patch_nonexistent_strategy_config_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.patch(
        "/api/strategies/configs/999999",
        headers=auth_headers,
        json={"name": "X"},
    )
    assert r.status_code == 404


@pytest.mark.integration
def test_delete_nonexistent_strategy_config_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.delete("/api/strategies/configs/999999", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.integration
def test_add_symbol_to_nonexistent_watchlist_returns_404(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.post(
        "/api/watchlists/999999/symbols",
        headers=auth_headers,
        json={"exchange": "NSE", "symbol": "REL"},
    )
    assert r.status_code == 404
