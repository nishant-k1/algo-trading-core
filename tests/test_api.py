"""API endpoint tests (require backend app + DB/Redis)."""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_health(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data or "ok" in data or data.get("status") == "ok"


@pytest.mark.integration
def test_version(client: TestClient) -> None:
    r = client.get("/api/version")
    assert r.status_code == 200
    data = r.json()
    assert "version" in data or "version" in str(data).lower()


@pytest.mark.integration
def test_login(client: TestClient, seed_user: None) -> None:
    r = client.post("/api/auth/login", data={"username": "user", "password": "any"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)


@pytest.mark.integration
def test_me_unauthorized(client: TestClient) -> None:
    r = client.get("/api/auth/me")
    assert r.status_code == 401


@pytest.mark.integration
def test_me_authorized(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "user_id" in data


@pytest.mark.integration
def test_settings_requires_auth(client: TestClient) -> None:
    r = client.get("/api/settings")
    assert r.status_code == 401


@pytest.mark.integration
def test_settings_authorized(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get("/api/settings", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "active_broker_id" in data
    assert "paper_live" in data


@pytest.mark.integration
def test_strategies_list(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get("/api/strategies", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(s.get("key") == "previous_high_breakout" for s in data)


@pytest.mark.integration
def test_trading_modes(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get("/api/settings/trading-modes", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
