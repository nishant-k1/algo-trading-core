"""Pytest fixtures: test client."""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

os.environ.setdefault("SECRET_KEY", "test-secret-key")


def _hash_password(password: str) -> str:
    """Hash password for test user (avoid passlib backend issues in pytest)."""
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def seed_user(client: TestClient) -> None:
    """Ensure test user exists (email=user, password=any)."""
    from app.db.session import SessionLocal
    from app.db.models.user import User
    pwd = _hash_password("any")
    with SessionLocal() as db:
        user = db.execute(select(User).where(User.email == "user")).scalar_one_or_none()
        if user:
            user.hashed_password = pwd
            user.is_active = True
            db.commit()
        else:
            # Avoid duplicate key if id=1 already exists (e.g. sequence not advanced)
            existing = db.execute(select(User).order_by(User.id)).scalar_one_or_none()
            if existing:
                existing.email = "user"
                existing.hashed_password = pwd
                existing.is_active = True
                db.commit()
            else:
                db.add(User(email="user", hashed_password=pwd, is_active=True))
                db.commit()


@pytest.fixture
def auth_headers(client: TestClient, seed_user: None) -> dict[str, str]:
    """Login and return Authorization header."""
    r = client.post("/api/auth/login", data={"username": "user", "password": "any"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
