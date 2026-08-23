from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.billing.api import router as billing_router
from app.modules.catalog.api import router as catalog_router
from app.modules.identity.api import router as identity_router
from app.modules.learning.api import router as learning_router
from app.modules.tutor.api import router as tutor_router
from app.shared.config import Settings, get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Lifespan setup (DB connection pools, Redis clients) will initialize here
    yield
    # Lifespan cleanup (DB connection pools, Redis clients) will close here


def create_health_router(settings: Settings) -> APIRouter:
    health_router = APIRouter(tags=["health"])

    @health_router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    @health_router.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    return health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()

    app = FastAPI(
        title=config.app_name,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Base health & readiness endpoints
    app.include_router(create_health_router(config))

    # Public module routers (modular monolith)
    app.include_router(identity_router, prefix="/api/v1")
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(learning_router, prefix="/api/v1")
    app.include_router(tutor_router, prefix="/api/v1")
    app.include_router(billing_router, prefix="/api/v1")

    return app


app = create_app()
