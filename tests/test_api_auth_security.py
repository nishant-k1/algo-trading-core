"""Auth and security: invalid/expired token, wrong API key, protected routes."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import settings


@pytest.mark.integration
def test_me_rejects_invalid_bearer_token(client: TestClient) -> None:
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert r.status_code == 401


@pytest.mark.integration
def test_me_rejects_expired_jwt(client: TestClient) -> None:
    payload = {
        "sub": "1",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm="HS256",
    )
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


@pytest.mark.integration
def test_me_rejects_wrong_api_key(client: TestClient) -> None:
    r = client.get("/api/auth/me", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401


@pytest.mark.integration
def test_me_accepts_valid_api_key(client: TestClient) -> None:
    r = client.get("/api/auth/me", headers={"X-API-Key": settings.secret_key})
    assert r.status_code == 200
    assert r.json().get("user_id") == 1


@pytest.mark.integration
def test_protected_routes_reject_missing_auth(client: TestClient) -> None:
    for path in ["/api/settings", "/api/watchlists", "/api/strategies/configs", "/api/dashboard"]:
        r = client.get(path)
        assert r.status_code == 401, f"Expected 401 for {path}"
