from dataclasses import dataclass

from app.application.ports.notifier import IExternalNotifier
from app.application.ports.repository import IUserRepository
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
        notifier: IExternalNotifier,
    ) -> None:
        self._user_repo = user_repo
        self._notifier = notifier

    def execute(self, command: RegisterUserCommand) -> User:
        """Выполнить сценарий регистрации пользователя"""

        existing_user = self._user_repo.get_by_login(command.login)
        if existing_user is not None:
            raise LoginAlreadyTakenError(f"Логин '{command.login}' уже занят")

        user = User(login=command.login, password=command.password)
        self._user_repo.add(user)

        self._notifier.notify(f"User '{user.login}' successfully registered")

        return user
