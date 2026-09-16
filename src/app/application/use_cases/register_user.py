from dataclasses import dataclass

from app.application.ports.event_bus import IEventPublisher
from app.application.ports.repository import IUserRepository
from app.domain.events import UserRegisteredEvent
from app.domain.exceptions import LoginAlreadyTakenError
from app.domain.user import User


@dataclass(frozen=True)
class RegisterUserCommand:
    """Команда на регистрацию пользователя"""

    login: str
    password: str


class RegisterUserUseCase:
    """Сценарий регистрации пользователя"""

    def __init__(
        self,
        user_repo: IUserRepository,
        event_publisher: IEventPublisher,
    ) -> None:
        self._user_repo = user_repo
        self._event_publisher = event_publisher

    async def execute(self, command: RegisterUserCommand) -> User:
        """Выполнить сценарий регистрации пользователя"""
        existing_user = await self._user_repo.get_by_login(command.login)
        if existing_user is not None:
            raise LoginAlreadyTakenError(f"Логин '{command.login}' уже занят")

        user = User(login=command.login, password=command.password)

        # Здесь ваще по факту должен быть аутбокс и юнит оф ворк, но для этой лабы это оверинжиниринг
        await self._user_repo.add(user)
        await self._event_publisher.publish(
            UserRegisteredEvent(login=user.login)
        )

        return user
