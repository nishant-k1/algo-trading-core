"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.constants import API_PREFIX, VERSION
from app.core.exceptions import register_exception_handlers
from app.api.routes import auth, dashboard, health, instruments, orders, screener, settings as settings_routes, strategies, watchlists


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect DB/Redis, start scheduler. Shutdown: stop scheduler."""
    from app.engines.scheduler import start_scheduler
    start_scheduler()
    yield
    from app.engines.scheduler import stop_scheduler
    stop_scheduler()


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    app = FastAPI(
        title="Algo Trading API",
        version=VERSION,
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=f"{API_PREFIX}/redoc",
        openapi_url=f"{API_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # CORS: allow frontend so browser doesn't block; explicit origins required when using credentials
    _origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",  # Vite preview (E2E)
        settings.frontend_url,
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o for o in _origins if o],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(instruments.router, prefix=API_PREFIX)
    app.include_router(settings_routes.router, prefix=API_PREFIX)
    app.include_router(screener.router, prefix=API_PREFIX)
    app.include_router(watchlists.router, prefix=API_PREFIX)
    app.include_router(strategies.router, prefix=API_PREFIX)
    app.include_router(orders.router, prefix=API_PREFIX)
    app.include_router(dashboard.router, prefix=API_PREFIX)

    return app


app = create_app()
