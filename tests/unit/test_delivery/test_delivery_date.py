import pytest

from delivery import calculate_delivery_cost


@pytest.mark.parametrize(
    argnames=("distance", "expected_date"),
    argvalues=(
        (500, "2026-09-04"),  # 1 день
        (1000, "2026-09-05"),  # 2 дня
        (1500, "2026-09-06"),  # 3 дня
        (5000, "2026-09-13"),  # 10 дней
    ),
)
def test_standard_delivery_date_exact_days(
    distance: int,
    expected_date: str,
    valid_weight: float,
    valid_package_type: str,
):
    _, delivery_date = calculate_delivery_cost(
        weight=valid_weight,
        distance=distance,
        package_type=valid_package_type,
        is_express=False,
    )

    assert delivery_date == expected_date


@pytest.mark.xfail(
    reason="(46): округление срока доставки вниз вместо округления вверх",
    strict=False,
)
@pytest.mark.parametrize(
    argnames=("distance", "expected_date"),
    argvalues=(
        (501, "2026-09-05"),  # > 500 км -> требуется 2 дня!
        (600, "2026-09-05"),
        (999, "2026-09-05"),
        (1001, "2026-09-06"),
    ),
)
def test_delivery_date_ceil_rounding_for_fractional_days(
    distance: int,
    expected_date: str,
    valid_weight: float,
    valid_package_type: str,
):
    _, delivery_date = calculate_delivery_cost(
        weight=valid_weight,
        distance=distance,
        package_type=valid_package_type,
        is_express=False,
    )
    # В коде 501 // 500 дает 1 день.
    assert delivery_date == expected_date


@pytest.mark.parametrize(
    argnames=("distance", "expected_express_date"),
    argvalues=(
        (2000, "2026-09-05"),  # 4 // 2 = 2 дня
        (3000, "2026-09-06"),  # 6 // 2 = 3 дня
        (5000, "2026-09-08"),  # 10 // 2 = 5 дней
    ),
)
def test_express_delivery_faster_than_standard_for_long_distance(
    distance: int,
    expected_express_date: str,
    valid_weight: float,
    valid_package_type: str,
):
    values: dict[str, float | int | str] = {
        "weight": valid_weight,
        "package_type": valid_package_type,
    }
    _, date_standard = calculate_delivery_cost(
        **values,
        distance=distance,
        is_express=False,
    )
    _, date_express = calculate_delivery_cost(
        **values,
        distance=distance,
        is_express=True,
    )

    assert date_express < date_standard
    assert date_express == expected_express_date


@pytest.mark.xfail(
    reason="(49): экспресс-доставка дает 0 дней при дистанциях <= 500 км",
    strict=False,
)
@pytest.mark.parametrize(
    argnames="distance",
    argvalues=(10, 100, 200, 500),
)
def test_express_delivery_must_not_be_zero_days(
    distance: int,
    valid_weight: float,
    valid_package_type: str,
):
    _, delivery_date = calculate_delivery_cost(
        weight=valid_weight,
        distance=distance,
        package_type=valid_package_type,
        is_express=True,
    )
    # Дата не должна быть днем отправки.
    # Должен быть минимум 1 день пути
    assert delivery_date != "2026-09-03"
    assert delivery_date == "2026-09-04"
