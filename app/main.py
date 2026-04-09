import logging

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging

setup_logging(debug=settings.debug)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.on_event("startup")
    async def startup() -> None:
        logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)

    return app


app = create_app()
