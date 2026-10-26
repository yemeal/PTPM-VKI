from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.logging import setup_logging
from app.core.settings import get_settings
from app.entrypoints.http.exception_handlers import register_exception_handlers
from app.entrypoints.http.routers import (
    comments_router,
    health_router,
    root_router,
)
from app.infrastructure.db.base import Base
from app.infrastructure.di import create_container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """управление жизненным циклом приложения и бд"""
    container: AsyncContainer = app.state.dishka_container
    engine = await container.get(AsyncEngine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


def create_app(container: AsyncContainer | None = None) -> FastAPI:
    """фабрика создания приложения fastapi с di-контейнером"""
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)

    app = FastAPI(
        title=settings.SERVICE_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(comments_router)
    app.include_router(root_router)

    di_container = container or create_container()
    setup_dishka(di_container, app)

    return app


app = create_app()
