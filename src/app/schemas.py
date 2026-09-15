import re
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic.alias_generators import to_camel
from pydantic_core import PydanticCustomError

LOGIN_BLACKLIST: set[str] = {"admin", "moderator", "hacker"}

# Логин
EMAIL_PATTERN: re.Pattern[str] = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)
PHONE_PATTERN: re.Pattern[str] = re.compile(
    r"^\+[0-9]-[0-9]{3}-[0-9]{3}-[0-9]{4}$"
)
SIMPLE_LOGIN_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9_]+$")

# Пароль
LOWERCASE_PATTERN: re.Pattern[str] = re.compile(r"[а-яё]")
UPPERCASE_PATTERN: re.Pattern[str] = re.compile(r"[А-ЯЁ]")
DIGIT_PATTERN: re.Pattern[str] = re.compile(r"[0-9]")
SPECIAL_PATTERN: re.Pattern[str] = re.compile(
    r"[!@#$%^&*()_+\-=\[\]{};:'\",.<>/?\\|`~]"
)
PASSWORD_PATTERN: re.Pattern[str] = re.compile(
    r"^[А-Яа-яЁё0-9!@#$%^&*()_+\-=\[\]{};:'\",.<>/?\\|`~]+$"
)


class UserRegister(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        frozen=True,
        extra="forbid",
        validate_by_name=True,
        validate_by_alias=True,
    )

    login: str
    password: str
    confirm_password: str

    @field_validator("login")
    @classmethod
    def validate_login(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise PydanticCustomError(
                "login_empty",
                "Логин не может быть пустым",
            )

        if value.casefold() in LOGIN_BLACKLIST:
            raise PydanticCustomError(
                "login_blacklisted",
                "Логин запрещен",
            )

        # Валидный email
        if EMAIL_PATTERN.fullmatch(value):
            return value

        # Валидный телефон
        if PHONE_PATTERN.fullmatch(value):
            return value

        # Похоже на email, но формат неправильный
        if "@" in value:
            raise PydanticCustomError(
                "invalid_email",
                "Некорректный формат email",
            )

        # Похоже на телефон, но формат неправильный
        if value.startswith("+"):
            raise PydanticCustomError(
                "invalid_phone",
                "Телефон должен соответствовать формату +x-xxx-xxx-xxxx",
            )

        # Обычный логин
        if len(value) < 5:
            raise PydanticCustomError(
                "login_too_short",
                "Логин должен содержать минимум 5 символов",
            )

        if not SIMPLE_LOGIN_PATTERN.fullmatch(value):
            raise PydanticCustomError(
                "invalid_login_characters",
                "Логин может содержать только латинские буквы, цифры и _",
            )

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 7:
            raise PydanticCustomError(
                "password_too_short",
                "Пароль должен содержать минимум 7 символов",
            )

        if not PASSWORD_PATTERN.fullmatch(value):
            raise PydanticCustomError(
                "invalid_password_characters",
                "Пароль может содержать только кириллицу, цифры и спецсимволы",
            )

        if not LOWERCASE_PATTERN.search(value):
            raise PydanticCustomError(
                "password_no_lowercase",
                "Пароль должен содержать минимум одну строчную букву",
            )

        if not UPPERCASE_PATTERN.search(value):
            raise PydanticCustomError(
                "password_no_uppercase",
                "Пароль должен содержать минимум одну заглавную букву",
            )

        if not DIGIT_PATTERN.search(value):
            raise PydanticCustomError(
                "password_no_digit",
                "Пароль должен содержать минимум одну цифру",
            )

        if not SPECIAL_PATTERN.search(value):
            raise PydanticCustomError(
                "password_no_special",
                "Пароль должен содержать минимум один спецсимвол",
            )

        return value

    @model_validator(mode="after")
    def validate_password_match(self) -> Self:
        if self.password != self.confirm_password:
            raise PydanticCustomError(
                "passwords_mismatch",
                "Пароль и подтверждение пароля не совпадают",
            )

        return self
