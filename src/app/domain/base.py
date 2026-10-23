import uuid
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from typing import Annotated, Any, ClassVar, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.domain.clock import ensure_utc
from app.domain.exceptions.base import (
    EntityIdentityImmutableError,
    InvalidDomainTimestampError,
)


class DomainModel(BaseModel):
    """проверенное состояние предметной области с запретом прямого изменения полей"""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        from_attributes=True,
        validate_assignment=True,
        validate_default=True,
        revalidate_instances="always",
        arbitrary_types_allowed=False,
        populate_by_name=True,
        ser_json_bytes="base64",
        ser_json_timedelta="iso8601",
    )

    def model_copy(
        self, *, update: Mapping[str, Any] | None = None, deep: bool = False
    ) -> Self:
        values = self.model_dump(round_trip=True)
        if update is not None:
            values.update(update)
        # noinspection PyTypeChecker
        return type(self).model_validate(deepcopy(values) if deep else values)

    @classmethod
    def model_construct(
        cls, _fields_set: set[str] | None = None, **values: Any
    ) -> Self:
        return cls.model_validate(values)


class Entity(DomainModel):
    """базовая сущность с идентификатором и временем создания"""

    id: Annotated[
        uuid.UUID | int,
        Field(
            description="Уникальный идентификатор сущности",
        ),
    ]
    created_at: Annotated[
        datetime,
        Field(
            description="Дата и время создания сущности (UTC)",
        ),
    ]

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: uuid.UUID | int) -> uuid.UUID | int:
        if isinstance(value, int) and value <= 0:
            raise ValueError("ID must be positive")
        return value

    @field_validator("created_at")
    @classmethod
    def _normalize_created_at(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class MutableEntity(Entity):
    """изменяемая сущность с меткой updated_at и атомарными мутациями"""

    __hash__ = None

    _IGNORED_COMPARE_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"id", "created_at", "updated_at"}
    )

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        # pydantic генерирует hash заново для frozen-подклассов
        # изменяемые агрегаты сохраняют frozen-защиту полей, но не являются ключами
        cls.__hash__ = None

    updated_at: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Дата и время последнего обновления сущности (UTC)",
        ),
    ]

    @field_validator("updated_at")
    @classmethod
    def _normalize_updated_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)

    @model_validator(mode="after")
    def _validate_timestamps(self) -> Self:
        if self.updated_at is not None and self.updated_at < self.created_at:
            raise InvalidDomainTimestampError()
        return self

    def _update_metadata(self, now: datetime) -> dict[str, Any]:
        """служебные поля времени и версии для обновления"""
        return {"updated_at": now}

    def _create_candidate(self, *, now: datetime, **changes: Any) -> Self:
        """создание и валидация кандидата нового состояния с проверкой времени"""
        candidate = self.__class__.model_validate(
            {
                **self.model_dump(),
                **changes,
                **self._update_metadata(now),
            }
        )
        if (
            self.updated_at is not None
            and candidate.updated_at is not None
            and candidate.updated_at < self.updated_at
        ):
            raise InvalidDomainTimestampError()
        return candidate

    def _replace_state(self, candidate: Self) -> None:
        """применение проверенного состояния к текущему объекту"""
        object.__setattr__(self, "__dict__", candidate.__dict__.copy())
        object.__setattr__(
            self, "__pydantic_fields_set__", candidate.model_fields_set.copy()
        )

    def _apply_changes(self, *, now: datetime, **changes: Any) -> bool:
        """атомарное применение изменений к сущности с валидацией инвариантов"""
        if "id" in changes or "created_at" in changes:
            raise EntityIdentityImmutableError()

        candidate = self._create_candidate(now=now, **changes)

        has_business_changes = any(
            getattr(candidate, field) != getattr(self, field)
            for field in type(self).model_fields
            if field not in self._IGNORED_COMPARE_FIELDS
        )

        if not has_business_changes:
            return False

        self._replace_state(candidate)
        return True


class VersionedMutableEntity(MutableEntity):
    """изменяемая сущность с оптимистической блокировкой версий"""

    _IGNORED_COMPARE_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"id", "created_at", "updated_at", "version"}
    )

    version: Annotated[
        int,
        Field(
            default=1,
            ge=1,
            strict=True,
            description="Номер версии сущности (изменяется вместе с updated_at)",
        ),
    ]

    def _update_metadata(self, now: datetime) -> dict[str, Any]:
        """служебные поля времени и инкремента версии"""
        return {
            "updated_at": now,
            "version": self.version + 1,
        }
