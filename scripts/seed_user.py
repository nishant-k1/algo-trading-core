"""Seed default user (email=user, password=any) for login. Run once after migrations."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from sqlalchemy import select

from app.config import settings
from app.db.models.user import User
from app.db.session import SessionLocal


def main() -> None:
    if not settings.database_url:
        print("DATABASE_URL not set")
        sys.exit(1)
    with SessionLocal() as db:
        existing = db.execute(select(User).where(User.email == "user")).scalar_one_or_none()
        if existing:
            print("User 'user' already exists")
            return
        hashed = bcrypt.hashpw(b"any", bcrypt.gensalt()).decode("utf-8")
        user = User(
            email="user",
            hashed_password=hashed,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print("Created user: email=user, password=any")


if __name__ == "__main__":
    main()
