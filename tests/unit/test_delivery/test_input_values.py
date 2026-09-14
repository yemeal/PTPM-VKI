import pytest

from delivery import calculate_delivery_cost


@pytest.mark.parametrize(
    argnames="weight",
    argvalues=[0.1, 0.2, 1, 25, 49, 50],
)
def test_valid_weight(
    weight: float,
    valid_distance: int,
    valid_package_type: str,
    valid_is_express: bool,
    invalid_result: tuple[int, str],
):
    result = calculate_delivery_cost(
        weight=weight,
        distance=valid_distance,
        package_type=valid_package_type,
        is_express=valid_is_express,
    )

    assert result != invalid_result


@pytest.mark.parametrize(
    argnames="weight",
    argvalues=[0.09, 0.0, -1.0, 50.1, 100.0],
)
def test_invalid_weight(
    weight: float,
    valid_distance: int,
    valid_package_type: str,
    valid_is_express: bool,
    invalid_result: tuple[int, str],
):
    result = calculate_delivery_cost(
        weight=weight,
        distance=valid_distance,
        package_type=valid_package_type,
        is_express=valid_is_express,
    )
    assert result == invalid_result


@pytest.mark.parametrize(
    argnames="distance",
    argvalues=[1, 2, 500, 4999, 5000],
)
def test_valid_distance(
    distance: int,
    valid_weight: float,
    valid_package_type: str,
    valid_is_express: bool,
    invalid_result: tuple[int, str],
):
    result = calculate_delivery_cost(
        weight=valid_weight,
        distance=distance,
        package_type=valid_package_type,
        is_express=valid_is_express,
    )
    assert result != invalid_result


@pytest.mark.parametrize(
    argnames="distance",
    argvalues=[0, -1, -1000, 0.1, 5001, 1000000],
)
def test_invalid_distance(
    distance: int,
    valid_weight: float,
    valid_package_type: str,
    valid_is_express: bool,
    invalid_result: tuple[int, str],
):
    result = calculate_delivery_cost(
        weight=valid_weight,
        distance=distance,
        package_type=valid_package_type,
        is_express=valid_is_express,
    )
    assert result == invalid_result


@pytest.mark.parametrize(
    argnames="package_type",
    argvalues=[
        "обычный",
        "хрупкий",
        "опасный",
    ],
)
def test_valid_package_type(
    package_type: str,
    valid_weight: float,
    valid_distance: int,
    valid_is_express: bool,
    invalid_result: tuple[int, str],
):
    result = calculate_delivery_cost(
        weight=valid_weight,
        distance=valid_distance,
        package_type=package_type,
        is_express=valid_is_express,
    )
    assert result != invalid_result


@pytest.mark.parametrize(
    argnames="package_type",
    argvalues=[
        "жидкий",  # неизвестный тип
        "документы",  # типичный тип доставки, которого нет в списке
        "",  # пустая строка
        "Обычный",  # с заглавной буквы (в коде нет .lower(), это ошибка)
        "ХРУПКИЙ",  # капс
        " обычный",  # с пробелом
        "123",  # числовая строка
    ],
)
def test_invalid_package_type(
    package_type: str,
    valid_weight: float,
    valid_distance: int,
    invalid_result: tuple[int, str],
):
    result = calculate_delivery_cost(
        weight=valid_weight,
        distance=valid_distance,
        package_type=package_type,
    )
    assert result == invalid_result


def test_default_is_express_is_false(
    valid_weight: float,
    valid_distance: int,
    valid_package_type: str,
):
    result_default = calculate_delivery_cost(
        weight=valid_weight,
        distance=valid_distance,
        package_type=valid_package_type,
    )
    result_explicit_false = calculate_delivery_cost(
        weight=valid_weight,
        distance=valid_distance,
        package_type=valid_package_type,
        is_express=False,
    )
    assert result_default == result_explicit_false


@pytest.mark.parametrize(
    ("weight", "distance", "package_type"),
    [
        (-1.0, 0, "неизвестный"),  # всё невалидно
        (0.0, -500, "обычный"),  # и вес, и дистанция
        (100.0, 100, "чужой"),  # и вес, и тип
        (5.0, 0, "неизвестный"),  # дистанция и тип
        (5.0, 6000, "пластик"),  # дистанция и тип
    ],
)
def test_multiple_invalid_inputs(
    weight: float,
    distance: int,
    package_type: str,
    invalid_result: tuple[int, str],
):
    result = calculate_delivery_cost(
        weight=weight,
        distance=distance,
        package_type=package_type,
    )
    assert result == invalid_result
