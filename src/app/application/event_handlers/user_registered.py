from app.application.ports.event_bus import IEventHandler
from app.application.ports.notifier import INotificationService
from app.domain.events import UserRegisteredEvent


class UserRegisteredNotificationHandler(IEventHandler[UserRegisteredEvent]):
    """Обработчик события регистрации пользователя: отправка уведомления."""

    def __init__(self, notification_service: INotificationService) -> None:
        self._notification_service = notification_service

    async def handle(self, event: UserRegisteredEvent) -> None:
        await self._notification_service.notify(
            f"User '{event.login}' successfully registered"
        )
