"""The shared grading rule.

Audit findings NEW-BE-09 (grader and simulator disagreed) and NEW-BE-10
(`MONITOR` was never scored). These assertions pin the semantics down so a
future edit has to change a test to change the meaning of the track record.
"""
import pytest

from scripts._grading import resolve_levels, resolve_outcome

ENTRY = 2800.0
SETUP = {"target_1": 2920.0, "stop_loss": 2720.0}


# ------------------------------------------------------------------- levels

def test_stored_setup_levels_are_used_when_present():
    target, stop = resolve_levels(ENTRY, SETUP)
    assert (target, stop) == (2920.0, 2720.0)


def test_falls_back_to_a_five_percent_band_without_a_setup():
    target, stop = resolve_levels(ENTRY, None)
    assert target == pytest.approx(ENTRY * 1.05)
    assert stop == pytest.approx(ENTRY * 0.95)


# ------------------------------------------------------------------ bullish

@pytest.mark.parametrize("verdict", ["STRONG BUY", "BUY ON DIP"])
def test_bullish_target_hit_is_a_win(verdict):
    assert resolve_outcome(verdict, ENTRY, SETUP, max_high=2950.0, min_low=2790.0) == "WIN"


@pytest.mark.parametrize("verdict", ["STRONG BUY", "BUY ON DIP"])
def test_bullish_stop_hit_is_a_loss(verdict):
    assert resolve_outcome(verdict, ENTRY, SETUP, max_high=2850.0, min_low=2700.0) == "LOSS"


def test_bullish_range_bound_is_a_draw():
    assert resolve_outcome("STRONG BUY", ENTRY, SETUP, max_high=2900.0, min_low=2750.0) == "DRAW"


# ------------------------------------------------------------------ bearish

@pytest.mark.parametrize("verdict", ["CAUTION", "AVOID"])
def test_bearish_call_wins_when_the_drop_it_warned_about_happens(verdict):
    assert resolve_outcome(verdict, ENTRY, SETUP, max_high=2850.0, min_low=2700.0) == "WIN"


@pytest.mark.parametrize("verdict", ["CAUTION", "AVOID"])
def test_bearish_call_loses_when_the_stock_runs_to_target(verdict):
    assert resolve_outcome(verdict, ENTRY, SETUP, max_high=2950.0, min_low=2790.0) == "LOSS"


# ------------------------------------------------------------------ MONITOR

def test_monitor_wins_when_nothing_decisive_happens():
    """The whole claim of MONITOR is that no decisive move is coming yet."""
    assert resolve_outcome("MONITOR", ENTRY, SETUP, max_high=2900.0, min_low=2750.0) == "WIN"


@pytest.mark.parametrize(
    "max_high,min_low",
    [(2950.0, 2790.0), (2850.0, 2700.0)],   # broke up, broke down
)
def test_monitor_loses_on_a_decisive_break_either_way(max_high, min_low):
    assert resolve_outcome("MONITOR", ENTRY, SETUP, max_high, min_low) == "LOSS"


def test_monitor_is_no_longer_always_a_draw():
    """Regression for NEW-BE-10: MONITOR used to be unmeasurable by construction."""
    outcomes = {
        resolve_outcome("MONITOR", ENTRY, SETUP, 2900.0, 2750.0),
        resolve_outcome("MONITOR", ENTRY, SETUP, 2950.0, 2790.0),
    }
    assert "DRAW" not in outcomes
    assert outcomes == {"WIN", "LOSS"}


# --------------------------------------------------------------- tie-breaks

def test_both_levels_touched_resolves_against_the_prediction():
    """Daily bars carry no intraday order, so ties must not flatter the record."""
    assert resolve_outcome("STRONG BUY", ENTRY, SETUP, 2950.0, 2700.0) == "LOSS"
    assert resolve_outcome("AVOID", ENTRY, SETUP, 2950.0, 2700.0) == "LOSS"


# ----------------------------------------------------------------- degenerate

@pytest.mark.parametrize("price", [0.0, -1.0, None])
def test_missing_or_impossible_entry_price_is_a_draw(price):
    assert resolve_outcome("STRONG BUY", price, SETUP, 2950.0, 2700.0) == "DRAW"


def test_unknown_verdict_is_a_draw():
    assert resolve_outcome("SOMETHING ELSE", ENTRY, SETUP, 2950.0, 2700.0) == "DRAW"
