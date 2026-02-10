"""Register a user directly in the database (email + password).

Use this against your **Render** (or other) database by setting `DATABASE_URL`
to the same value your deployed service uses.

Examples:

  export DATABASE_URL="postgresql://...from Render..."
  python scripts/register_user.py nishant.29k1@gmail.com AlgoPass!2026

If the email already exists, this script will print a message and exit.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt  # type: ignore[import-untyped]
from sqlalchemy import select

from app.config import settings
from app.db.models.user import User
from app.db.session import SessionLocal


def main() -> None:
  if not settings.database_url:
      print("DATABASE_URL not set (copy from Render backend service).")
      sys.exit(1)

  parser = argparse.ArgumentParser(description="Register a user (email + password)")
  parser.add_argument("email", help="User email")
  parser.add_argument("password", help="Plaintext password to set")
  args = parser.parse_args()

  email: str = args.email
  password: str = args.password

  with SessionLocal() as db:
      existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
      if existing:
          print(f"User with email '{email}' already exists.")
          return

      hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
      user = User(email=email, hashed_password=hashed, is_active=True)
      db.add(user)
      db.commit()
      print(f"Created user: email={email}")


if __name__ == "__main__":
  main()

