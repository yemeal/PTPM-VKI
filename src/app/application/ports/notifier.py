from abc import ABC, abstractmethod


class IExternalNotifier(ABC):
    """Интерфейс сервиса уведомлений (сторонней зависимости)."""

    @abstractmethod
    def notify(self, message: str) -> None:
        """Отправить сообщение во внешнюю систему."""
