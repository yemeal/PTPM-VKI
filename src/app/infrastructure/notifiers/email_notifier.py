import logging

from app.application.ports.notifier import IExternalNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(IExternalNotifier):
    """Реализация сервиса отправки email-уведомлений"""

    def notify(self, message: str) -> None:
        logger.info("[EMAIL NOTIFIER] Sent notification: %s", message)
