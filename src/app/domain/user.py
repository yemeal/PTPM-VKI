import re

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.exceptions import (
    BlacklistedLoginError,
    EmptyLoginError,
    InvalidEmailFormatError,
    InvalidLoginCharactersError,
    InvalidPasswordCharactersError,
    InvalidPhoneFormatError,
    LoginTooShortError,
    PasswordNoDigitError,
    PasswordNoLowercaseError,
    PasswordNoSpecialError,
    PasswordNoUppercaseError,
    PasswordTooShortError,
)

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


class User(BaseModel):
    """Доменная бизнес-сущность пользователя."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    login: str
    password: str

    @field_validator("login")
    @classmethod
    def validate_login(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise EmptyLoginError()

        if value.casefold() in LOGIN_BLACKLIST:
            raise BlacklistedLoginError()

        # Валидный email
        if EMAIL_PATTERN.fullmatch(value):
            return value

        # Валидный телефон
        if PHONE_PATTERN.fullmatch(value):
            return value

        # Похоже на email, но формат неправильный
        if "@" in value:
            raise InvalidEmailFormatError()

        # Похоже на телефон, но формат неправильный
        if value.startswith("+"):
            raise InvalidPhoneFormatError()

        # Обычный логин
        if len(value) < 5:
            raise LoginTooShortError()

        if not SIMPLE_LOGIN_PATTERN.fullmatch(value):
            raise InvalidLoginCharactersError()

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 7:
            raise PasswordTooShortError()

        if not PASSWORD_PATTERN.fullmatch(value):
            raise InvalidPasswordCharactersError()

        if not LOWERCASE_PATTERN.search(value):
            raise PasswordNoLowercaseError()

        if not UPPERCASE_PATTERN.search(value):
            raise PasswordNoUppercaseError()

        if not DIGIT_PATTERN.search(value):
            raise PasswordNoDigitError()

        if not SPECIAL_PATTERN.search(value):
            raise PasswordNoSpecialError()

        return value
