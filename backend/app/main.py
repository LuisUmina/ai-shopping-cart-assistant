from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_chat, routes_health, routes_preferences
from app.config import get_settings
from app.utils.logging_utils import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    # Allow any localhost port so Vite can run on 5173, 5174, etc.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes_health.router, prefix="/api")
    app.include_router(routes_chat.router, prefix="/api")
    app.include_router(routes_preferences.router, prefix="/api")
    logger.info("%s started (provider=%s)", settings.app_name, settings.llm_provider)
    return app


app = create_app()
