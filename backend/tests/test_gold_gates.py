"""Gold layer verdict logic.

This is the layer the product's credibility rests on: it decides what the user
is told to do. Before 2026-08-18 it had no test at all, which is how a capital
value of -500,000 reached position sizing and produced -125 shares.
"""
import pytest

from app.services.gold_service import evaluate_hard_gates
from tests.conftest import make_silver


# --------------------------------------------------------------- capital guard

@pytest.mark.parametrize("capital", [-500_000.0, -0.01, 0.0])
def test_non_positive_capital_produces_no_trade_setup(silver, capital):
    """Regression for NEW-P2-01. Sizing must never emit a negative share count."""
    verdict = evaluate_hard_gates(silver, "none", capital)
    assert verdict.trade_setup is None


def test_nan_capital_produces_no_trade_setup(silver):
    verdict = evaluate_hard_gates(silver, "none", float("nan"))
    assert verdict.trade_setup is None


def test_positive_capital_still_sizes_normally(silver):
    verdict = evaluate_hard_gates(silver, "none", 100_000.0)
    assert verdict.trade_setup is not None
    assert verdict.trade_setup.suggested_position_size > 0
    assert verdict.trade_setup.risk_per_trade_inr > 0


# ------------------------------------------------------------------- overrides

def test_bearish_regime_suppresses_bullish_verdict(silver):
    """Override 3: macro conditions outrank a clean technical setup."""
    bullish = evaluate_hard_gates(silver, "none", 100_000.0)
    assert bullish.verdict == "STRONG BUY"

    bearish = evaluate_hard_gates(
        make_silver(market_regime="bearish"), "none", 100_000.0
    )
    assert bearish.verdict == "CAUTION"
    assert "BEARISH" in bearish.primary_reason.upper()


def test_thin_volume_demotes_strong_buy_to_monitor():
    """Override 1: a breakout without institutional volume is not confirmed."""
    thin = make_silver(current_volume=2_200_000.0, volume_avg_20=2_000_000.0)  # 1.1x
    verdict = evaluate_hard_gates(thin, "none", 100_000.0)
    assert verdict.verdict == "MONITOR"
    assert verdict.trade_setup is None


def test_lower_circuit_blocks_entirely():
    verdict = evaluate_hard_gates(make_silver(), "lower", 100_000.0)
    assert verdict.verdict == "AVOID"
    assert verdict.gate_results["circuit"] == "BLOCK"


def test_overbought_rsi_fails_its_gate():
    verdict = evaluate_hard_gates(make_silver(rsi_14=78.0), "none", 100_000.0)
    assert verdict.gate_results["rsi"] == "FAIL"
    assert verdict.verdict != "STRONG BUY"


# ------------------------------------------------------------------ invariants

def test_verdict_is_always_from_the_closed_vocabulary(silver):
    allowed = {"STRONG BUY", "BUY ON DIP", "MONITOR", "CAUTION", "AVOID"}
    for circuit in ("none", "upper", "lower"):
        for regime in ("bullish", "bearish", "neutral"):
            v = evaluate_hard_gates(
                make_silver(market_regime=regime), circuit, 100_000.0
            )
            assert v.verdict in allowed


def test_confidence_score_stays_within_its_declared_range(silver):
    for rsi in (25.0, 55.0, 78.0):
        v = evaluate_hard_gates(make_silver(rsi_14=rsi), "none", 100_000.0)
        assert 50.0 <= v.confidence_score <= 95.0


def test_same_input_always_yields_the_same_verdict(silver):
    """Determinism is the product claim. Assert it rather than assume it."""
    runs = [evaluate_hard_gates(make_silver(), "none", 100_000.0) for _ in range(5)]
    assert len({r.verdict for r in runs}) == 1
    assert len({r.confidence_score for r in runs}) == 1
