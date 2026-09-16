import asyncio
from collections import defaultdict
from typing import Any

from app.application.ports.event_bus import IEventHandler, IEventPublisher
from app.domain.events import DomainEvent


class InMemoryEventBus(IEventPublisher):
    """
    Асинхронная шина событий (GoF Наблюдатель / Push-модель)
    """

    def __init__(self) -> None:
        self._subscribers: dict[
            type[DomainEvent], list[IEventHandler[Any]]
        ] = defaultdict(list)
        self._running_tasks: set[asyncio.Task[None]] = set()

    def subscribe[EventT: DomainEvent](
        self,
        event_type: type[EventT],
        handler: IEventHandler[EventT],
    ) -> None:
        """
        Зарегистрировать наблюдателя на событие
        """
        self._subscribers[event_type].append(handler)

    async def publish(
        self,
        event: DomainEvent,
        *,
        wait: bool = False,
    ) -> None:
        """Опубликовать доменное событие и вытолкнуть его всем наблюдателям.

        По умолчанию (wait=False) обработчики выполняются асинхронно в фоне
        (asyncio.create_task), не блокируя вызывающий код.
        """
        try:
            handlers = self._subscribers[type(event)]
        except KeyError:
            return

        tasks: list[asyncio.Task[None]] = []
        for handler in handlers:
            task = asyncio.create_task(handler.handle(event))
            self._running_tasks.add(task)
            task.add_done_callback(self._running_tasks.discard)
            tasks.append(task)

        if wait and tasks:
            await asyncio.gather(*tasks)

    async def wait_until_idle(self) -> None:
        """Дождаться завершения всех активных фоновых задач."""
        if self._running_tasks:
            await asyncio.gather(*list(self._running_tasks))
