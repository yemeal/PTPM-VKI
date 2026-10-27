from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.db.base import Base
from app.infrastructure.repositories.sqlalchemy_comment_repo import (
    SqlAlchemyCommentRepository,
)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    """изолированная сессия sqlite в памяти для тестирования адаптеров"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as sess:
        yield sess

    await engine.dispose()


@pytest.fixture
def sqlalchemy_repo(session: AsyncSession) -> SqlAlchemyCommentRepository:
    """экземпляр боевого репозитория на sqlalchemy для тестов адаптера"""
    return SqlAlchemyCommentRepository(session=session)


@pytest.fixture
def repo(
    sqlalchemy_repo: SqlAlchemyCommentRepository,
) -> SqlAlchemyCommentRepository:
    return sqlalchemy_repo
