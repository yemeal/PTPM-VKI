class DomainError(Exception):
    """Базовое доменное исключение."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class DomainValidationError(DomainError, ValueError):
    """Базовая ошибка валидации доменных инвариантов."""


class LoginAlreadyTakenError(DomainError):
    """Исключение, выбрасываемое когда пользователь с указанным логином уже существует."""

    def __init__(self, message: str = "Логин уже занят") -> None:
        super().__init__(message)


# --- Ошибки логина ---


class InvalidLoginError(DomainValidationError):
    """Базовый класс ошибок валидации логина."""


class EmptyLoginError(InvalidLoginError):
    """Логин пустой."""

    def __init__(self, message: str = "Логин не может быть пустым") -> None:
        super().__init__(message)


class BlacklistedLoginError(InvalidLoginError):
    """Логин находится в черном списке."""

    def __init__(self, message: str = "Логин запрещен") -> None:
        super().__init__(message)


class InvalidEmailFormatError(InvalidLoginError):
    """Некорректный формат email."""

    def __init__(self, message: str = "Некорректный формат email") -> None:
        super().__init__(message)


class InvalidPhoneFormatError(InvalidLoginError):
    """Некорректный формат телефона."""

    def __init__(
        self,
        message: str = "Телефон должен соответствовать формату +x-xxx-xxx-xxxx",
    ) -> None:
        super().__init__(message)


class LoginTooShortError(InvalidLoginError):
    """Логин слишком короткий."""

    def __init__(
        self,
        message: str = "Логин должен содержать минимум 5 символов",
    ) -> None:
        super().__init__(message)


class InvalidLoginCharactersError(InvalidLoginError):
    """Логин содержит недопустимые символы."""

    def __init__(
        self,
        message: str = "Логин может содержать только латинские буквы, цифры и _",
    ) -> None:
        super().__init__(message)


# --- Ошибки пароля ---


class InvalidPasswordError(DomainValidationError):
    """Базовый класс ошибок валидации пароля."""


class PasswordTooShortError(InvalidPasswordError):
    """Пароль слишком короткий."""

    def __init__(
        self,
        message: str = "Пароль должен содержать минимум 7 символов",
    ) -> None:
        super().__init__(message)


class InvalidPasswordCharactersError(InvalidPasswordError):
    """Пароль содержит недопустимые символы."""

    def __init__(
        self,
        message: str = (
            "Пароль может содержать только кириллицу, цифры и спецсимволы"
        ),
    ) -> None:
        super().__init__(message)


class PasswordNoLowercaseError(InvalidPasswordError):
    """Пароль не содержит строчных букв."""

    def __init__(
        self,
        message: str = "Пароль должен содержать минимум одну строчную букву",
    ) -> None:
        super().__init__(message)


class PasswordNoUppercaseError(InvalidPasswordError):
    """Пароль не содержит заглавных букв."""

    def __init__(
        self,
        message: str = "Пароль должен содержать минимум одну заглавную букву",
    ) -> None:
        super().__init__(message)


class PasswordNoDigitError(InvalidPasswordError):
    """Пароль не содержит цифр."""

    def __init__(
        self,
        message: str = "Пароль должен содержать минимум одну цифру",
    ) -> None:
        super().__init__(message)


class PasswordNoSpecialError(InvalidPasswordError):
    """Пароль не содержит спецсимволов."""

    def __init__(
        self,
        message: str = "Пароль должен содержать минимум один спецсимвол",
    ) -> None:
        super().__init__(message)


class PasswordMismatchError(DomainValidationError):
    """Пароль и подтверждение пароля не совпадают."""

    def __init__(
        self,
        message: str = "Пароль и подтверждение пароля не совпадают",
    ) -> None:
        super().__init__(message)
