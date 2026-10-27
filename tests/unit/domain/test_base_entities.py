from datetime import UTC, datetime, timedelta, timezone
from typing import Annotated

import pytest
from pydantic import Field, ValidationError

from app.domain.base import (
    DomainModel,
    Entity,
    MutableEntity,
    VersionedMutableEntity,
)
from app.domain.exceptions.base import (
    EntityIdentityImmutableError,
    InvalidDomainTimestampError,
)


class DummyModel(DomainModel):
    value: int


class DummyEntity(Entity):
    title: str


class DummyMutable(MutableEntity):
    name: Annotated[str, Field(default="initial")]


class DummyVersioned(VersionedMutableEntity):
    name: Annotated[str, Field(default="initial")]
    count: Annotated[int, Field(default=0, ge=0)]


def test_domain_model_immutability() -> None:
    model = DummyModel(value=10)
    attr_name = "value"
    with pytest.raises(ValidationError):
        setattr(model, attr_name, 20)


def test_domain_model_forbids_extra() -> None:
    with pytest.raises(ValidationError):
        DummyModel.model_validate({"value": 10, "extra_field": "forbidden"})


def test_domain_model_copy_validates() -> None:
    model = DummyModel(value=10)
    updated = model.model_copy(update={"value": 20})
    assert updated.value == 20

    with pytest.raises(ValidationError):
        model.model_copy(update={"value": "invalid"})


def test_domain_model_construct_forces_validation() -> None:
    with pytest.raises(ValidationError):
        DummyModel.model_construct(value="not_an_int")


def test_entity_requires_positive_id(now: datetime) -> None:
    with pytest.raises(ValidationError):
        DummyEntity(id=0, created_at=now, title="test")
    with pytest.raises(ValidationError):
        DummyEntity(id=-5, created_at=now, title="test")

    entity = DummyEntity(id=1, created_at=now, title="test")
    assert entity.id == 1


def test_entity_normalizes_created_at(now: datetime) -> None:
    east_now = now.astimezone(timezone(timedelta(hours=3)))
    entity = DummyEntity(id=1, created_at=east_now, title="test")
    assert entity.created_at.tzinfo is UTC
    assert entity.created_at == now


def test_entity_rejects_naive_created_at() -> None:
    naive_dt = datetime(2026, 10, 26, 12, 0, 0)
    with pytest.raises(InvalidDomainTimestampError):
        DummyEntity(id=1, created_at=naive_dt, title="test")


def test_mutable_entity_initial_state(now: datetime) -> None:
    entity = DummyMutable(id=1, created_at=now)
    assert entity.id == 1
    assert entity.created_at == now
    assert entity.updated_at is None


def test_mutable_entity_apply_changes_advances_state(now: datetime) -> None:
    entity = DummyMutable(id=1, created_at=now)
    later = now + timedelta(seconds=30)

    changed = entity._apply_changes(now=later, name="updated_name")

    assert changed is True
    assert entity.name == "updated_name"
    assert entity.updated_at == later


def test_mutable_entity_apply_changes_noop_returns_false(
    now: datetime,
) -> None:
    entity = DummyMutable(id=1, created_at=now)
    before = entity.model_dump()
    later = now + timedelta(seconds=30)

    changed = entity._apply_changes(now=later, name="initial")

    assert changed is False
    assert entity.updated_at is None
    assert entity.model_dump() == before


def test_mutable_entity_normalizes_updated_at_to_utc(now: datetime) -> None:
    entity = DummyMutable(id=1, created_at=now)
    later_east = (now + timedelta(hours=1)).astimezone(
        timezone(timedelta(hours=3))
    )

    entity._apply_changes(now=later_east, name="updated_name")

    assert entity.updated_at is not None
    assert entity.updated_at == now + timedelta(hours=1)
    assert entity.updated_at.tzinfo is UTC


def test_mutable_entity_rejects_naive_updated_at(now: datetime) -> None:
    entity = DummyMutable(id=1, created_at=now)

    with pytest.raises(InvalidDomainTimestampError):
        entity._apply_changes(
            now=datetime(2026, 10, 26, 13, 0, 0), name="updated_name"
        )


def test_mutable_entity_rejects_updated_at_preceding_created_at(
    now: datetime,
) -> None:
    earlier = now - timedelta(seconds=1)
    with pytest.raises(InvalidDomainTimestampError):
        DummyMutable(id=1, created_at=now, updated_at=earlier)

    entity = DummyMutable(id=1, created_at=now)
    with pytest.raises(InvalidDomainTimestampError):
        entity._apply_changes(now=earlier, name="updated_name")


def test_mutable_entity_rejects_updated_at_preceding_current_updated_at(
    now: datetime,
) -> None:
    entity = DummyMutable(id=1, created_at=now)
    later = now + timedelta(seconds=10)
    entity._apply_changes(now=later, name="step_1")

    earlier_than_later = now + timedelta(seconds=5)
    with pytest.raises(InvalidDomainTimestampError):
        entity._apply_changes(now=earlier_than_later, name="step_2")


def test_versioned_mutable_entity_increments_version(now: datetime) -> None:
    entity = DummyVersioned(id=1, created_at=now)
    assert entity.version == 1

    later1 = now + timedelta(seconds=10)
    changed = entity._apply_changes(now=later1, name="v2")
    assert changed is True
    assert entity.version == 2
    assert entity.name == "v2"
    assert entity.updated_at == later1

    later2 = later1 + timedelta(seconds=10)
    changed = entity._apply_changes(now=later2, count=5)
    assert changed is True
    assert entity.version == 3
    assert entity.count == 5


def test_versioned_mutable_entity_noop_preserves_version(
    now: datetime,
) -> None:
    entity = DummyVersioned(id=1, created_at=now)
    later = now + timedelta(seconds=10)

    changed = entity._apply_changes(now=later, name="initial")
    assert changed is False
    assert entity.version == 1
    assert entity.updated_at is None


def test_versioned_mutable_entity_atomic_rollback_on_invalid_change(
    now: datetime,
) -> None:
    entity = DummyVersioned(id=1, created_at=now)
    later = now + timedelta(seconds=10)

    with pytest.raises(ValidationError):
        entity._apply_changes(now=later, count=-1)  # violates ge=0

    assert entity.version == 1
    assert entity.count == 0
    assert entity.updated_at is None


def test_mutable_entity_rejects_id_mutation(now: datetime) -> None:
    entity = DummyMutable(id=1, created_at=now)
    later = now + timedelta(seconds=10)
    with pytest.raises(EntityIdentityImmutableError):
        entity._apply_changes(now=later, id=2)


def test_mutable_entity_rejects_created_at_mutation(now: datetime) -> None:
    entity = DummyMutable(id=1, created_at=now)
    later = now + timedelta(seconds=10)
    with pytest.raises(EntityIdentityImmutableError):
        entity._apply_changes(now=later, created_at=later)
