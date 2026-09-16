import sqlite3
from typing import Self

from app.application.ports.repository import IUserRepository
from app.domain.user import User


class SqliteUserRepository(IUserRepository):
    """Реализация репозитория пользователей на базе SQLite."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._connection = sqlite3.connect(
            self.db_path, check_same_thread=False
        )
        self._init_db()

    def _init_db(self) -> None:
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    login TEXT PRIMARY KEY,
                    password TEXT NOT NULL
                );
                """
            )

    async def add(self, user: User) -> None:
        with self._connection:
            self._connection.execute(
                "INSERT INTO users (login, password) VALUES (?, ?);",
                (user.login, user.password),
            )

    async def get_by_login(self, login: str) -> User | None:
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT login, password FROM users WHERE login = ?;",
            (login,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return User(login=row[0], password=row[1])

    async def delete(self, login: str) -> bool:
        with self._connection:
            cursor = self._connection.execute(
                "DELETE FROM users WHERE login = ?;",
                (login,),
            )
            return cursor.rowcount > 0

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
