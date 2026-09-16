from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_camel

from app.domain.exceptions import PasswordMismatchError


class UserRegisterRequest(BaseModel):
    """Схема входных данных для регистрации пользователя."""

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

    @model_validator(mode="after")
    def validate_password_match(self) -> Self:
        if self.password != self.confirm_password:
            raise PasswordMismatchError()
        return self
