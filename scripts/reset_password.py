"""Reset a user's password. Run against live DB when you've forgotten it.

Usage (set DATABASE_URL from Render dashboard, then):
  python scripts/reset_password.py user mynewpassword
  # or
  EMAIL=user NEW_PASSWORD=mynewpassword python scripts/reset_password.py
"""

import argparse
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
        print("DATABASE_URL not set (e.g. copy from Render dashboard)")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Reset user password")
    parser.add_argument("email", nargs="?", help="User email (username)")
    parser.add_argument("new_password", nargs="?", help="New password")
    args = parser.parse_args()

    email = args.email or os.environ.get("EMAIL")
    new_password = args.new_password or os.environ.get("NEW_PASSWORD")

    if not email or not new_password:
        print("Usage: python scripts/reset_password.py <email> <new_password>")
        print("   or: EMAIL=x NEW_PASSWORD=y python scripts/reset_password.py")
        sys.exit(1)

    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with SessionLocal() as db:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user:
            print(f"No user with email: {email}")
            sys.exit(1)
        user.hashed_password = hashed
        db.commit()
        print(f"Password updated for: {email}")


if __name__ == "__main__":
    main()
