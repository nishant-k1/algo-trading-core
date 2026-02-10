"""Health and version endpoints (no auth)."""

from fastapi import APIRouter

from app.constants import VERSION

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness: returns 200 if app is up."""
    return {"status": "ok"}


@router.get("/version")
async def version() -> dict[str, str]:
    """API version."""
    return {"version": VERSION}
