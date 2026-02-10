"""Contract/schema tests: API responses have expected shape."""
import pytest
from fastapi.testclient import TestClient


def _assert_health(r_json: dict) -> None:
    assert "status" in r_json
    assert r_json["status"] == "ok"


def _assert_version(r_json: dict) -> None:
    assert "version" in r_json
    assert isinstance(r_json["version"], str)


def _assert_token_response(r_json: dict) -> None:
    assert "access_token" in r_json
    assert isinstance(r_json["access_token"], str)


def _assert_settings(r_json: dict) -> None:
    assert "active_broker_id" in r_json
    assert "paper_live" in r_json
    assert r_json["paper_live"] in ("paper", "live")
    assert "kill_switch" in r_json


def _assert_watchlist(r_json: dict) -> None:
    assert "id" in r_json
    assert "name" in r_json
    assert "symbols" in r_json
    assert isinstance(r_json["symbols"], list)


def _assert_strategy_option(r_json: dict) -> None:
    assert "key" in r_json
    assert "name" in r_json


def _assert_strategy_run(r_json: dict) -> None:
    assert "signals" in r_json
    assert "symbols_scanned" in r_json
    assert "symbols_filtered_by_gap" in r_json
    assert isinstance(r_json["signals"], list)


def _assert_dashboard_summary(r_json: dict) -> None:
    assert "paper_live" in r_json
    assert "positions" in r_json
    assert "orders" in r_json
    assert isinstance(r_json["positions"], list)
    assert isinstance(r_json["orders"], list)


@pytest.mark.integration
def test_health_contract(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    _assert_health(r.json())


@pytest.mark.integration
def test_version_contract(client: TestClient) -> None:
    r = client.get("/api/version")
    assert r.status_code == 200
    _assert_version(r.json())


@pytest.mark.integration
def test_login_contract(client: TestClient, seed_user: None) -> None:
    r = client.post("/api/auth/login", data={"username": "user", "password": "any"})
    assert r.status_code == 200
    _assert_token_response(r.json())


@pytest.mark.integration
def test_settings_contract(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get("/api/settings", headers=auth_headers)
    assert r.status_code == 200
    _assert_settings(r.json())


@pytest.mark.integration
def test_create_watchlist_contract(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.post(
        "/api/watchlists",
        headers=auth_headers,
        json={"name": "Contract WL"},
    )
    assert r.status_code == 200
    _assert_watchlist(r.json())


@pytest.mark.integration
def test_strategies_list_contract(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.get("/api/strategies", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    for item in data:
        _assert_strategy_option(item)


@pytest.mark.integration
def test_dashboard_summary_contract(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    r = client.get("/api/dashboard", headers=auth_headers)
    assert r.status_code == 200
    _assert_dashboard_summary(r.json())
