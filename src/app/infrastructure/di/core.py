from dishka import Provider, Scope, provide

from app.core.settings import Settings, get_settings
from app.domain.clock import Clock, utc_now


class CoreProvider(Provider):
    """провайдер базовой конфигурации и системных часов"""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__()
        self._settings = settings or get_settings()

    @provide(scope=Scope.APP)
    def provide_settings(self) -> Settings:
        return self._settings

    @provide(scope=Scope.APP)
    def provide_clock(self) -> Clock:
        return utc_now
