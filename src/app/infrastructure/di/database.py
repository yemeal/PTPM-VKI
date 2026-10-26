from collections.abc import AsyncGenerator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import Settings


class DatabaseProvider(Provider):
    """провайдер подключения к бд и сессий sqlalchemy"""

    @provide(scope=Scope.APP)
    async def provide_engine(
        self, settings: Settings
    ) -> AsyncGenerator[AsyncEngine]:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def provide_sessionmaker(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )

    @provide(scope=Scope.REQUEST)
    async def provide_session(
        self, sessionmaker: async_sessionmaker[AsyncSession]
    ) -> AsyncGenerator[AsyncSession]:
        async with sessionmaker() as session:
            yield session
            await session.commit()
