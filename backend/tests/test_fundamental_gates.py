"""Guards the fundamental metrics that used to be computed and then ignored.

Audit findings FIX-01, FIX-02, FIX-03 (2026-08-23):

  FIX-01  `debt_equity_max` and `roe_min` were configured in gate_thresholds.py
          but read by no gate. Five Silver metrics were computed, written into
          every ledger row, and never influenced a verdict.
  FIX-02  yfinance returns `returnOnEquity` as a fraction (0.18) while
          `roe_min` is in percent (15.0). The comparison `0.18 > 15.0` was
          False for every stock ever analysed.
  FIX-03  `pe_vs_sector_avg` fell back to a hardcoded sector median of 25.0 and
          `institutional_bias` resolved an empty dict to a confident "neutral",
          both manufacturing a reading out of no data.
"""
import pytest

from app.services.gold_service import evaluate_hard_gates
from app.services.silver_service import _normalize_debt_to_equity, _normalize_roe_pct
from config.gate_thresholds import GATE_THRESHOLDS as TH
from tests.conftest import make_silver


class TestRoeUnitNormalisation:
    """FIX-02. The bug that made the ROE flag dead for every stock."""

    def test_yfinance_fraction_becomes_percent(self):
        assert _normalize_roe_pct(0.1845) == pytest.approx(18.45)

    def test_value_already_in_percent_is_left_alone(self):
        assert _normalize_roe_pct(18.45) == pytest.approx(18.45)

    def test_the_original_bug_no_longer_reproduces(self):
        """A healthy 18% ROE must clear a 15.0 threshold.

        Pre-fix this compared 0.18 > 15.0 and returned False, so a quality
        business scored the same as a value-destroying one.
        """
        assert _normalize_roe_pct(0.18) > TH["roe_min"]

    def test_missing_data_is_none_not_zero(self):
        """None means unknown. 0.0 would mean 'measured, and terrible'."""
        assert _normalize_roe_pct(None) is None

    def test_nan_is_none(self):
        assert _normalize_roe_pct(float("nan")) is None

    def test_garbage_is_none(self):
        assert _normalize_roe_pct("not a number") is None

    def test_negative_roe_is_preserved_as_percent(self):
        """Loss-making companies exist and must not be silently dropped."""
        assert _normalize_roe_pct(-0.05) == pytest.approx(-5.0)


class TestDebtUnitNormalisation:
    def test_yfinance_percentage_becomes_a_multiple(self):
        assert _normalize_debt_to_equity(150.0) == pytest.approx(1.5)

    def test_value_already_a_multiple_is_left_alone(self):
        assert _normalize_debt_to_equity(1.5) == pytest.approx(1.5)

    def test_missing_is_none(self):
        assert _normalize_debt_to_equity(None) is None

    def test_negative_is_none(self):
        """Negative equity makes the ratio meaningless rather than excellent."""
        assert _normalize_debt_to_equity(-50.0) is None


class TestBalanceSheetGate:
    """FIX-01, swing. `debt_equity_max` must decide something."""

    def test_high_leverage_warns(self):
        silver = make_silver(debt_flag=True, debt_to_equity=2.5)
        draft = evaluate_hard_gates(silver, "NORMAL", 100000.0)
        assert draft.gate_results["balance_sheet"] == "WARN"

    def test_low_leverage_passes(self):
        silver = make_silver(debt_flag=False, debt_to_equity=0.3)
        draft = evaluate_hard_gates(silver, "NORMAL", 100000.0)
        assert draft.gate_results["balance_sheet"] == "PASS"

    def test_unknown_leverage_creates_no_gate(self):
        """Absent data must not be scored as a pass.

        Adding the gate as PASS when the ratio is unknown would inflate the
        confidence score with evidence that does not exist.
        """
        silver = make_silver(debt_flag=None)
        draft = evaluate_hard_gates(silver, "NORMAL", 100000.0)
        assert "balance_sheet" not in draft.gate_results

    def test_leverage_warning_reaches_the_user(self):
        silver = make_silver(debt_flag=True, debt_to_equity=2.5)
        draft = evaluate_hard_gates(silver, "NORMAL", 100000.0)
        assert any("Debt/equity" in w for w in draft.what_to_watch)


class TestCapitalEfficiencyGate:
    """FIX-01, positional. `roe_min` must decide something."""

    def test_strong_roe_passes(self):
        silver = make_silver(timeframe="positional", roe_vs_cost_of_capital=True, roe_pct=22.0)
        draft = evaluate_hard_gates(silver, "NORMAL", 100000.0)
        assert draft.gate_results["capital_efficiency"] == "PASS"

    def test_weak_roe_warns(self):
        silver = make_silver(timeframe="positional", roe_vs_cost_of_capital=False, roe_pct=6.0)
        draft = evaluate_hard_gates(silver, "NORMAL", 100000.0)
        assert draft.gate_results["capital_efficiency"] == "WARN"

    def test_unknown_roe_creates_no_gate(self):
        silver = make_silver(timeframe="positional", roe_vs_cost_of_capital=None)
        draft = evaluate_hard_gates(silver, "NORMAL", 100000.0)
        assert "capital_efficiency" not in draft.gate_results


class TestEveryThresholdIsUsed:
    """The check that would have caught FIX-01 when it was introduced."""

    def test_no_configured_threshold_is_dead(self):
        """Every gate threshold must be read by gold_service.

        A threshold nothing reads is a lever with nothing attached: it looks
        tunable, the Engine Room proposes changes to it, an operator approves
        them, and no verdict ever moves.
        """
        import inspect

        from app.services import gold_service

        source = inspect.getsource(gold_service)
        # Thresholds consumed indirectly via a Silver boolean still count,
        # because the flag is computed from the threshold in silver_service.
        from app.services import silver_service

        combined = source + inspect.getsource(silver_service)

        unused = [name for name in TH if name not in combined]
        assert not unused, f"thresholds configured but never read: {unused}"
