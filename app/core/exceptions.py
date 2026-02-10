"""Global exception handlers for the API."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def _cors_headers(request: Request) -> dict[str, str]:
    """Return CORS headers for error responses so browser does not hide 4xx/5xx (middleware may not add them)."""
    origin = request.headers.get("origin")
    allowed = getattr(request.app.state, "cors_allow_origins", None) or []
    if origin and allowed and origin in allowed:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    return {}


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers on the app."""

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
            headers=_cors_headers(request),
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers=_cors_headers(request),
        )
