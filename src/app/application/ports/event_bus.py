from abc import ABC, abstractmethod

from app.domain.events import DomainEvent


class IEventHandler[EventT: DomainEvent](ABC):
    """
    Интерфейс подписчика/наблюдателя доменного события
    """

    @abstractmethod
    async def handle(self, event: EventT) -> None:
        """
        Асинхронно обработать доменное событие
        """


class IEventPublisher(ABC):
    """
    Интерфейс издателя доменных событий
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Асинхронно опубликовать/протолкнуть событие наблюдателям
        """
