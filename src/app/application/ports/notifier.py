from abc import ABC, abstractmethod


class INotificationService(ABC):
    """Интерфейс сервиса уведомлений"""

    @abstractmethod
    async def notify(self, message: str) -> None:
        """Асинхронно отправить сообщение во внешнюю систему"""
