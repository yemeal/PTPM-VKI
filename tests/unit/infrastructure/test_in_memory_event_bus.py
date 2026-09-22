import asyncio
from unittest.mock import AsyncMock

import pytest

from app.application.ports.event_bus import IEventHandler
from app.domain.events import DomainEvent, UserRegisteredEvent
from app.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus


class OtherDomainEvent(DomainEvent):
    """Тестовое стороннее событие для проверки изоляции."""

    payload: str = "test"


class UnsubscribedEvent(DomainEvent):
    """Событие, на которое нет подписчиков."""


@pytest.fixture
def bus() -> InMemoryEventBus:
    """Фикстура новой шины событий."""
    return InMemoryEventBus()


async def test_multiple_handlers_receive_event(bus: InMemoryEventBus) -> None:
    """Проверка подписки нескольких обработчиков на одно событие."""
    handler_1 = AsyncMock(spec=IEventHandler)
    handler_2 = AsyncMock(spec=IEventHandler)

    bus.subscribe(UserRegisteredEvent, handler_1)
    bus.subscribe(UserRegisteredEvent, handler_2)

    event = UserRegisteredEvent(login="subscriber_test")
    await bus.publish(event)
    await bus.wait_until_idle()

    handler_1.handle.assert_awaited_once_with(event)
    handler_2.handle.assert_awaited_once_with(event)


async def test_event_isolation_between_different_types(
    bus: InMemoryEventBus,
) -> None:
    """Изоляция от других типов событий: обработчик получает только свои события."""
    user_handler = AsyncMock(spec=IEventHandler)
    other_handler = AsyncMock(spec=IEventHandler)

    bus.subscribe(UserRegisteredEvent, user_handler)
    bus.subscribe(OtherDomainEvent, other_handler)

    other_event = OtherDomainEvent(payload="info")
    await bus.publish(other_event)
    await bus.wait_until_idle()

    # other_handler вызван, user_handler НЕ вызван
    other_handler.handle.assert_awaited_once_with(other_event)
    user_handler.handle.assert_not_called()

    # Публикуем событие регистрации пользователя
    user_event = UserRegisteredEvent(login="isolated_user")
    await bus.publish(user_event)
    await bus.wait_until_idle()

    user_handler.handle.assert_awaited_once_with(user_event)
    assert other_handler.handle.await_count == 1


async def test_publish_unsubscribed_event_does_not_fail(
    bus: InMemoryEventBus,
) -> None:
    """Публикация события без зарегистрированных слушателей проходит без ошибок."""
    event = UnsubscribedEvent()
    await bus.publish(event)
    await bus.wait_until_idle()


async def test_background_task_handling_and_wait_until_idle(
    bus: InMemoryEventBus,
) -> None:
    """Обработка фоновых задач: не блокирует вызов publish, завершается при wait_until_idle."""
    is_executed = False

    class AsyncSlowHandler(IEventHandler[UserRegisteredEvent]):
        async def handle(self, event: UserRegisteredEvent) -> None:
            nonlocal is_executed
            await asyncio.sleep(0.02)
            is_executed = True

    bus.subscribe(UserRegisteredEvent, AsyncSlowHandler())
    event = UserRegisteredEvent(login="async_worker")

    # При wait=False задача создается в фоне
    await bus.publish(event, wait=False)
    assert len(bus._running_tasks) == 1
    assert is_executed is False

    # Дожидаемся завершения
    await bus.wait_until_idle()
    assert is_executed is True
    assert len(bus._running_tasks) == 0


async def test_publish_with_wait_true_blocks_until_completion(
    bus: InMemoryEventBus,
) -> None:
    """При wait=True метод publish ожидает завершения всех обработчиков."""
    is_completed = False

    class ImmediateHandler(IEventHandler[UserRegisteredEvent]):
        async def handle(self, event: UserRegisteredEvent) -> None:
            nonlocal is_completed
            await asyncio.sleep(0.01)
            is_completed = True

    bus.subscribe(UserRegisteredEvent, ImmediateHandler())
    event = UserRegisteredEvent(login="sync_publish")

    await bus.publish(event, wait=True)
    assert is_completed is True
    assert len(bus._running_tasks) == 0
