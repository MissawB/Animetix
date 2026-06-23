import math

from core.domain.services import berrix_economy as econ


def test_anchors_have_expected_defaults():
    assert econ.BX_PRICE_USD_NET == 0.00043
    assert econ.TARGET_MARGIN == 0.10
    assert econ.AD_REVENUE_USD == 0.02
    assert econ.MINING_REWARD_BX == 10


def test_bx_cost_for_usd_rounds_up_and_guarantees_margin():
    # A feature costing $0.002 of compute must charge enough Bx that the compute
    # is at most (1 - margin) of the Bx value spent.
    price = econ.bx_cost_for_usd(0.002)
    assert price == math.ceil(0.002 / (0.00043 * 0.90))  # == 6
    # margin holds: compute <= (1 - margin) * value spent
    assert 0.002 <= price * econ.BX_PRICE_USD_NET * (1 - econ.TARGET_MARGIN)


def test_bx_cost_for_usd_is_never_zero_for_positive_cost():
    assert econ.bx_cost_for_usd(0.0000001) >= 1


def test_ad_reward_bx_keeps_margin_on_ad_funded_bx():
    reward = econ.ad_reward_bx()
    # Bx granted are worth at most (1 - margin) of the ad revenue.
    assert reward == math.floor(0.02 * (1 - 0.10) / 0.00043)  # == 41
    assert reward * econ.BX_PRICE_USD_NET <= econ.AD_REVENUE_USD * (
        1 - econ.TARGET_MARGIN
    )


def test_feature_bx_costs_floor():
    """Every entry in FEATURE_BX_COSTS must be >= bx_cost_for_usd of its USD anchor.

    This is the margin-cushion guarantee: if we charge fewer Bx than required by
    the margin model, the treasury loses money on that call.
    """
    assert hasattr(econ, "FEATURE_COMPUTE_USD"), "FEATURE_COMPUTE_USD table missing"
    assert hasattr(econ, "FEATURE_BX_COSTS"), "FEATURE_BX_COSTS table missing"
    assert econ.FEATURE_COMPUTE_USD, "FEATURE_COMPUTE_USD must not be empty"
    assert econ.FEATURE_BX_COSTS, "FEATURE_BX_COSTS must not be empty"
    assert (
        econ.FEATURE_COMPUTE_USD.keys() == econ.FEATURE_BX_COSTS.keys()
    ), "FEATURE_COMPUTE_USD and FEATURE_BX_COSTS must have identical key sets"
    for key, usd in econ.FEATURE_COMPUTE_USD.items():
        floor = econ.bx_cost_for_usd(usd)
        charged = econ.FEATURE_BX_COSTS[key]
        assert charged >= floor, (
            f"Feature '{key}': charges {charged} Bx but margin floor is {floor} Bx "
            f"(compute cost ${usd:.4f})"
        )
