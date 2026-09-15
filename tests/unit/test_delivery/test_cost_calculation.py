import pytest

from delivery import calculate_delivery_cost


@pytest.mark.parametrize(
    argnames=("weight", "distance", "expected_cost"),
    argvalues=(
        (1.0, 1, 205),
        (2.0, 100, 700),
        (3.0, 500, 2700),
        (5.0, 1000, 5200),
    ),
)
def test_cost_weight_and_distance(
    weight: float | int,
    distance: int,
    expected_cost: int,
    valid_package_type: str,
):
    cost, _ = calculate_delivery_cost(
        weight=weight,
        distance=distance,
        package_type=valid_package_type,
        is_express=False,
    )

    assert cost == expected_cost


@pytest.mark.parametrize(
    argnames=("weight", "expected_cost"),
    argvalues=(
        # <= 5.0 кг (коэффициент 1.0 - без наценки)
        (0.1, 700),
        (5.0, 700),
        # 5.0 - 20.0 кг (коэффициент 1.2 - наценка +20%)
        (5.1, 840),
        (10.0, 840),
        (19.9, 840),
        # >= 20.0 кг (коэффициент 1.5 - наценка +50%)
        (20.0, 1050),
        (50.0, 1050),
    ),
)
def test_cost_weight_multipliers(
    weight: float,
    expected_cost: int,
    valid_distance: int,
    valid_package_type: str,
):
    cost, _ = calculate_delivery_cost(
        weight=weight,
        distance=valid_distance,
        package_type=valid_package_type,
    )

    assert cost == expected_cost


@pytest.mark.parametrize(
    argnames=("package_type", "expected_cost"),
    argvalues=(
        ("обычный", 700),
        ("хрупкий", 1000),
        ("опасный", 1700),
    ),
)
def test_cost_package_type_surcharge(
    package_type: str,
    expected_cost: int,
    valid_weight: float,
    valid_distance: int,
):
    cost, _ = calculate_delivery_cost(
        weight=valid_weight,
        distance=valid_distance,
        package_type=package_type,
    )

    assert cost == expected_cost


@pytest.mark.parametrize(
    argnames=("weight", "package_type", "expected_cost"),
    argvalues=(
        # 700 * 1.2 + 300 = 840 + 300 = 1140
        (10.0, "хрупкий", 1140),
        # 700 * 1.5 + 1000 = 1050 + 1000 = 2050
        (20.0, "опасный", 2050),
    ),
)
def test_cost_combined_weight_and_package_type(
    weight: float,
    package_type: str,
    expected_cost: int,
    valid_distance: int,
):
    cost, _ = calculate_delivery_cost(
        weight=weight,
        distance=valid_distance,
        package_type=package_type,
    )

    assert cost == expected_cost


@pytest.mark.xfail(
    reason="(41): экспресс уменьшает стоимость на 50% вместо наценки",
    strict=False,
)
def test_express_delivery_must_be_more_expensive_than_standard(
    valid_weight: float,
    valid_distance: int,
    valid_package_type: str,
):
    values: dict[str, float | int | str] = {
        "weight": valid_weight,
        "distance": valid_distance,
        "package_type": valid_package_type,
    }

    cost_standard, _ = calculate_delivery_cost(
        **values,
        is_express=False,
    )

    cost_express, _ = calculate_delivery_cost(
        **values,
        is_express=True,
    )

    assert cost_express > cost_standard
