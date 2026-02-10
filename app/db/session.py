"""Database session and engine (sync)."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# PostgreSQL; set DATABASE_URL=postgresql://user:pass@host:5432/db
# When empty (e.g. env not loaded), use in-memory SQLite so app can start for health check
_db_url = settings.database_url.strip() or "sqlite:///:memory:"
engine = create_engine(
    _db_url,
    echo=settings.environment == "development",
    future=True,
)

SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency: yield a DB session and close after request."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
