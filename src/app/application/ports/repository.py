from abc import ABC, abstractmethod

from app.domain.user import User


class IUserRepository(ABC):
    """Интерфейс хранилища пользователей."""

    @abstractmethod
    def add(self, user: User) -> None:
        """Добавить пользователя в репозиторий."""

    @abstractmethod
    def get_by_login(self, login: str) -> User | None:
        """Получить пользователя по логину."""

    @abstractmethod
    def delete(self, login: str) -> bool:
        """Удалить пользователя по логину. Возвращает True, если пользователь был удален."""
