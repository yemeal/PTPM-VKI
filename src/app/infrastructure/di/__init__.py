from dishka import AsyncContainer, Provider, make_async_container

from app.core.settings import Settings
from app.infrastructure.di.core import CoreProvider
from app.infrastructure.di.database import DatabaseProvider
from app.infrastructure.di.handlers import HandlersProvider
from app.infrastructure.di.infrastructure import InfrastructureProvider

__all__ = [
    "CoreProvider",
    "DatabaseProvider",
    "HandlersProvider",
    "InfrastructureProvider",
    "create_container",
]


def create_container(
    settings: Settings | None = None,
    *additional_providers: Provider,
) -> AsyncContainer:
    """фабрика создания асинхронного di-контейнера приложения"""
    return make_async_container(
        CoreProvider(settings=settings),
        DatabaseProvider(),
        InfrastructureProvider(),
        HandlersProvider(),
        *additional_providers,
    )
