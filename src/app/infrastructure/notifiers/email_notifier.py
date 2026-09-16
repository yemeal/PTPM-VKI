import logging

from app.application.ports.notifier import INotificationService

logger = logging.getLogger(__name__)


class EmailNotificationService(INotificationService):
    """Реализация сервиса отправки email-уведомлений."""

    async def notify(self, message: str) -> None:
        logger.info("[EMAIL NOTIFIER] Sent notification: %s", message)
