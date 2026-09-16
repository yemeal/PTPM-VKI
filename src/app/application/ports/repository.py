from abc import ABC, abstractmethod

from app.domain.user import User


class IUserRepository(ABC):
    """
    Интерфейс хранилища пользователей
    """

    @abstractmethod
    async def add(self, user: User) -> None:
        """
        Добавить пользователя в репозиторий
        """

    @abstractmethod
    async def get_by_login(self, login: str) -> User | None:
        """
        Получить пользователя по логину
        """

    @abstractmethod
    async def delete(self, login: str) -> bool:
        """
        Удалить пользователя по логину.
        Возвращает True, если пользователь был удален
        """
