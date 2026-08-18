"""ATR-derived trade setup arithmetic.

These levels are the most directly actionable thing the system emits, so the
relationships between them are asserted rather than trusted.
"""
from app.services.gold_service import evaluate_hard_gates
from tests.conftest import make_silver

CAPITAL = 100_000.0
RISK_FRACTION = 0.02


def _setup(**overrides):
    verdict = evaluate_hard_gates(make_silver(**overrides), "none", CAPITAL)
    assert verdict.trade_setup is not None, "fixture should clear every gate"
    return make_silver(**overrides), verdict.trade_setup


def test_levels_are_ordered_correctly():
    silver, s = _setup()
    assert s.stop_loss < s.entry_zone_low < s.entry_zone_high < s.target_1 < s.target_2
    assert s.stop_loss < silver.current_price < s.target_1


def test_entry_band_is_half_an_atr_either_side_of_price():
    silver, s = _setup()
    assert abs(s.entry_zone_low - (silver.current_price - 0.5 * silver.atr_14)) < 0.01
    assert abs(s.entry_zone_high - (silver.current_price + 0.5 * silver.atr_14)) < 0.01


def test_swing_stop_is_two_atr_below_price():
    silver, s = _setup()
    assert abs(s.stop_loss - (silver.current_price - 2.0 * silver.atr_14)) < 0.01


def test_position_size_risks_exactly_two_percent_of_capital():
    silver, s = _setup()
    risk_distance = silver.current_price - s.stop_loss
    expected = int((CAPITAL * RISK_FRACTION) / risk_distance)
    assert s.suggested_position_size == expected
    # And the money actually at risk matches the declared fraction.
    assert abs(s.risk_per_trade_inr - CAPITAL * RISK_FRACTION) < 0.01


def test_position_size_scales_with_capital():
    _, small = _setup()
    big = evaluate_hard_gates(make_silver(), "none", CAPITAL * 4).trade_setup
    assert big is not None
    assert big.suggested_position_size > small.suggested_position_size


def test_reward_to_risk_is_positive_and_matches_the_levels():
    silver, s = _setup()
    risk_distance = silver.current_price - s.stop_loss
    expected = round((s.target_1 - silver.current_price) / risk_distance, 2)
    assert s.risk_reward_ratio == expected
    assert s.risk_reward_ratio > 1.0


def test_higher_volatility_widens_the_stop_and_shrinks_the_position():
    _, calm = _setup(atr_14=40.0)
    _, wild = _setup(atr_14=120.0)
    assert wild.stop_loss < calm.stop_loss
    assert wild.suggested_position_size < calm.suggested_position_size


def test_long_term_horizon_never_produces_a_setup():
    """Setups are only generated for tradeable horizons."""
    verdict = evaluate_hard_gates(
        make_silver(timeframe="long_term", sma_200=2500.0, trailing_pe=20.0),
        "none",
        CAPITAL,
    )
    assert verdict.trade_setup is None
