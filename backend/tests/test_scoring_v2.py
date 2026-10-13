"""Verdict engine v2: factor library and scorer (docs/verdict_engine_plan.md)."""
import pytest

from app.services.factors import FACTORS, ramp
from app.services.scoring_service import score_v2
from config.factor_weights import COVERAGE_FLOOR, FACTOR_WEIGHTS
from config.gate_thresholds import GATE_THRESHOLDS as TH
from tests.conftest import make_silver

VOCAB = {"STRONG BUY", "BUY ON DIP", "MONITOR", "CAUTION", "AVOID"}


# ------------------------------------------------------------------ factors

def test_ramp_hits_its_three_anchors_and_clips():
    assert ramp(0, 0, 5, 10) == -1
    assert ramp(5, 0, 5, 10) == 0
    assert ramp(10, 0, 5, 10) == 1
    assert ramp(-99, 0, 5, 10) == -1 and ramp(99, 0, 5, 10) == 1


def test_every_weighted_factor_exists():
    for horizon, weights in FACTOR_WEIGHTS.items():
        assert set(weights) <= set(FACTORS), horizon


@pytest.mark.parametrize("name", sorted(FACTORS))
def test_factor_returns_none_on_missing_data_and_bounds_otherwise(name):
    empty = make_silver(sma_20=None, sma_50=None, rsi_14=None, atr_14=None, volume_avg_20=None,
                        stock_vs_sector_rs=None, market_regime=None)
    assert FACTORS[name](empty).score is None
    full = make_silver(sma_200=2500.0, sma_gap_pct=1.0, revenue_cagr_3y=12.0, revenue_cagr_5y=9.0,
                       profit_cagr_3y=20.0, eps_cagr_5y=15.0, roe_pct=18.0, debt_to_equity=0.4,
                       trailing_pe=30.0, fcf_conversion=0.8, pe_band_vs_growth=2.0,
                       opm_trend="expanding", roe_consistency_5y="average", debt_trajectory="leveraging")
    score = FACTORS[name](full).score
    assert score is not None and -1.0 <= score <= 1.0


def test_threshold_maps_to_zero():
    assert FACTORS["rsi"](make_silver(rsi_14=TH["rsi_overbought"])).score == pytest.approx(0)
    assert FACTORS["roe"](make_silver(roe_pct=TH["roe_min"])).score == pytest.approx(0)
    assert FACTORS["leverage"](make_silver(debt_to_equity=TH["debt_equity_max"])).score == pytest.approx(0)
    assert FACTORS["valuation"](make_silver(trailing_pe=TH["max_pe"])).score == pytest.approx(0)


def test_factor_direction():
    assert FACTORS["rsi"](make_silver(rsi_14=85)).score < 0 < FACTORS["rsi"](make_silver(rsi_14=55)).score
    assert FACTORS["leverage"](make_silver(debt_to_equity=3.0)).score < 0
    assert FACTORS["trend_20"](make_silver(current_price=2600.0)).score < 0


def test_oversold_rsi_is_a_warning_not_a_verdict():
    assert FACTORS["rsi"](make_silver(rsi_14=5)).score == pytest.approx(-0.5)


def test_only_negative_factors_carry_a_watch_item():
    assert FACTORS["rsi"](make_silver(rsi_14=55)).watch_item is None
    assert FACTORS["rsi"](make_silver(rsi_14=85)).watch_item


# ------------------------------------------------------------------- scorer

def test_clean_swing_profile_is_strong_buy_with_levels(silver):
    v = score_v2(silver, "none")
    assert v.verdict == "STRONG BUY"
    assert v.price_levels is not None and v.price_levels.stop_loss < silver.current_price
    assert not hasattr(v.price_levels, "suggested_position_size")


def test_missing_factor_counts_as_zero_not_dropped():
    full = score_v2(make_silver(debt_to_equity=0.0), "none")
    missing = score_v2(make_silver(debt_to_equity=None), "none")
    assert missing.composite < full.composite
    assert missing.coverage < full.coverage == 1.0


def test_low_coverage_caps_at_monitor():
    thin = make_silver(sma_20=None, rsi_14=None, stock_vs_sector_rs=None)
    v = score_v2(thin, "none")
    assert v.coverage < COVERAGE_FLOOR
    assert v.verdict in {"MONITOR", "CAUTION", "AVOID"}


def test_lower_circuit_forces_avoid(silver):
    assert score_v2(silver, "lower").verdict == "AVOID"


def test_upper_circuit_caps_at_monitor(silver):
    assert score_v2(silver, "upper").verdict == "MONITOR"


def test_bearish_regime_suppresses_bullish(silver):
    v = score_v2(make_silver(market_regime="bearish"), "none")
    assert v.verdict == "CAUTION"
    assert any("bearish" in c for c in v.caps_applied)


def test_thin_volume_demotes_strong_buy():
    v = score_v2(make_silver(current_volume=2_800_000.0, debt_to_equity=0.0), "none")
    assert v.verdict != "STRONG BUY"


def test_weak_profile_scores_negative_and_explains_why():
    weak = make_silver(current_price=2500.0, rsi_14=88.0, stock_vs_sector_rs=-0.12,
                       current_volume=500_000.0, debt_to_equity=3.5)
    v = score_v2(weak, "none")
    assert v.composite < 0
    assert v.verdict in {"CAUTION", "AVOID"}
    assert v.primary_reason.startswith("Held back by")
    assert v.what_to_watch


@pytest.mark.parametrize("tf", sorted(FACTOR_WEIGHTS))
def test_every_horizon_yields_vocabulary_and_bounded_confidence(tf):
    v = score_v2(make_silver(timeframe=tf), "none")
    assert v.verdict in VOCAB
    assert 50.0 <= v.confidence_score <= 95.0
    assert -1.0 <= v.composite <= 1.0


def test_deterministic(silver):
    assert score_v2(silver, "none") == score_v2(silver, "none")


# ------------------------------------------------------------- shadow wiring

def test_shadow_v2_is_a_plain_dict_for_the_ledger(silver):
    from app.orchestrator import _shadow_v2
    shadow = _shadow_v2(silver, "none")
    assert shadow["ruleset"] == "v2.0.0"
    assert shadow["verdict"] in VOCAB
    assert isinstance(shadow["factors"], list)


def test_shadow_v2_failure_returns_none_instead_of_raising(silver, monkeypatch):
    import app.orchestrator as orch

    def boom(*_):
        raise RuntimeError("v2 bug")

    monkeypatch.setattr(orch, "score_v2", boom)
    assert orch._shadow_v2(silver, "none") is None
