from fastapi import FastAPI

from ranking_service.api.routes.feed import router as feed_router
from ranking_service.api.routes.health import router as health_router
from ranking_service.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router)
    app.include_router(feed_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
