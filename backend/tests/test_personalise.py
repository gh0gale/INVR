"""Personal layer: same verdict, output fitted to the user (docs/verdict_engine_plan.md D1)."""
import pytest

from app.services.gold_service import atr_levels
from app.services.personalise import personalise
from config.personal_rules import POSITION_CAP, RISK_PER_TRADE
from tests.conftest import make_silver

CAPITAL = 1_000_000.0


def _plan(verdict="STRONG BUY", silver=None, **profile):
    silver = silver or make_silver()
    levels = atr_levels(silver.current_price, silver.atr_14, silver.timeframe)
    watch = [f"item {i}" for i in range(8)]
    return personalise(verdict, silver, levels, watch, {"capital": CAPITAL, **profile})


@pytest.mark.parametrize("risk", ["conservative", "moderate", "aggressive"])
def test_size_risks_the_profile_fraction_and_respects_the_cap(risk):
    plan = _plan(risk=risk)
    entry = (plan.setup["entry_zone_low"] + plan.setup["entry_zone_high"]) / 2
    loss_at_stop = plan.position_size * (entry - plan.setup["stop_loss"])
    assert loss_at_stop <= CAPITAL * RISK_PER_TRADE[risk] + 1e-6
    assert plan.position_value_inr <= CAPITAL * POSITION_CAP[risk] + 1e-6


def test_higher_risk_never_sizes_smaller():
    sizes = [_plan(risk=r).position_size for r in ("conservative", "moderate", "aggressive")]
    assert sizes == sorted(sizes)


def test_cap_binds_when_the_stop_is_tight():
    tight = make_silver(atr_14=2.0)
    plan = _plan(silver=tight, risk="moderate")
    assert plan.capped_by_limit
    assert plan.position_value_inr <= CAPITAL * POSITION_CAP["moderate"] + 1e-6


@pytest.mark.parametrize("capital", [0, -5, float("nan"), None, "abc"])
def test_bad_or_zero_capital_gives_no_size(capital):
    silver = make_silver()
    levels = atr_levels(silver.current_price, silver.atr_14, "swing")
    plan = personalise("STRONG BUY", silver, levels, [], {"capital": capital})
    assert plan.position_size is None and plan.setup is not None


def test_buy_on_dip_gets_a_staged_setup_only_when_aggressive():
    near_floor = make_silver(current_price=2660.0, sma_50=2650.0)
    aggressive = _plan("BUY ON DIP", near_floor, risk="aggressive")
    conservative = _plan("BUY ON DIP", near_floor, risk="conservative")
    assert aggressive.staged_entry and aggressive.setup["entry_zone_low"] < 2650.0 < aggressive.setup["entry_zone_high"]
    assert conservative.setup is None and conservative.position_size is None
    assert any("STRONG BUY" in n for n in conservative.fit_notes)


@pytest.mark.parametrize("verdict", ["MONITOR", "CAUTION", "AVOID"])
def test_non_bullish_verdicts_get_no_setup_at_any_risk(verdict):
    assert _plan(verdict, risk="aggressive").setup is None


def test_capital_preservation_flags_leverage_and_the_contradiction():
    levered = make_silver(debt_to_equity=3.0)
    plan = _plan(silver=levered, goal="capital_preservation", risk="aggressive")
    assert any("Debt/equity" in n for n in plan.fit_notes)
    assert any("aggressive" in n for n in plan.fit_notes)


def test_dividend_goal_never_claims_dividends():
    notes = _plan(goal="dividend_income").fit_notes
    assert notes == ["Dividend data is not part of this analysis. Check the payout record before relying on income."]


def test_watch_depth_follows_experience():
    assert len(_plan(experience="beginner").what_to_watch) == 3
    assert len(_plan(experience="advanced").what_to_watch) == 8


def test_api_profile_shape_is_read_too():
    plan = personalise("STRONG BUY", make_silver(),
                       atr_levels(2800.0, 40.0, "swing"), [],
                       {"risk_tolerance": "conservative", "available_capital": CAPITAL})
    assert plan.risk_level == "conservative" and plan.position_size


def test_unknown_risk_falls_back_to_moderate():
    assert _plan(risk="yolo").risk_level == "moderate"
