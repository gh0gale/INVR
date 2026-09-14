"""A gate decides on data, or it does not decide.

Audit DATA-01..03 (2026-09-13). A coverage probe across 10 large caps and three
horizons showed most of the verdict machinery running on defaults while
looking fully populated:

  DATA-01  NSE was queried as 'RELIANCE.NS', failed every time, and the
           resulting 'unknown' circuit status scored a PASS (weight 3.0).
  DATA-02  missing fundamentals arrived as 0 or a hardcoded 25.0 sector P/E,
           and missing growth as 0%, so gates passed or failed on no data.
  DATA-03  the sector map never matched a yfinance sector name, and its one
           match had no history, so relative strength and the bearish
           override never ran; market_regime defaulted to "neutral".

Each test here pins one of those shut. No network: yfinance and NSE are faked.
"""
import asyncio
from datetime import date

import numpy as np
import pandas as pd
import pytest

from app.integrations import market_data
from app.schemas.bronze import BronzePayload
from app.services import bronze_service
from app.services.gold_service import evaluate_hard_gates
from app.services.silver_service import compute_silver_metrics
from tests.conftest import make_silver


# ------------------------------------------------------------------ helpers

def _prices(end: date, rows: int = 300, start_price: float = 100.0, drift: float = 0.001) -> pd.DataFrame:
    idx = pd.bdate_range(end=pd.Timestamp(end), periods=rows, tz="Asia/Kolkata")
    close = start_price * np.cumprod(np.full(rows, 1 + drift))
    return pd.DataFrame({"Open": close, "High": close * 1.01, "Low": close * 0.99,
                         "Close": close, "Volume": np.full(rows, 1_000_000.0)}, index=idx)


TODAY = date(2026, 9, 11)


class _FakeTicker:
    def __init__(self, info, financials=None, balance_sheet=None, cashflow=None):
        self.info = info
        self.financials = financials if financials is not None else pd.DataFrame()
        self.balance_sheet = balance_sheet if balance_sheet is not None else pd.DataFrame()
        self.cashflow = cashflow if cashflow is not None else pd.DataFrame()


def _statement(rows: dict) -> pd.DataFrame:
    """Newest period first, as yfinance returns it."""
    years = [pd.Timestamp(f"{y}-03-31") for y in (2026, 2025, 2024, 2023)]
    return pd.DataFrame({y: [rows[k][i] for k in rows] for i, y in enumerate(years)}, index=list(rows))


def _fundamentals(info, **frames):
    fake = _FakeTicker(info, **frames)
    original = market_data.yf.Ticker
    market_data.yf.Ticker = lambda symbol: fake
    try:
        return asyncio.run(market_data.fetch_yfinance_fundamentals("TEST.NS"))
    finally:
        market_data.yf.Ticker = original


# ------------------------------------------------------------ DATA-01 circuit

class TestCircuit:
    @pytest.mark.parametrize("status", ["unknown", "not_checked", None, "garbage"])
    def test_a_status_nse_did_not_report_is_not_scored(self, status):
        draft = evaluate_hard_gates(make_silver(), status, 100000.0)
        assert "circuit" not in draft.gate_results

    def test_a_reported_clear_band_passes(self):
        assert evaluate_hard_gates(make_silver(), "none", 100000.0).gate_results["circuit"] == "PASS"

    def test_lower_circuit_still_blocks(self):
        draft = evaluate_hard_gates(make_silver(), "lower", 100000.0)
        assert draft.gate_results["circuit"] == "BLOCK"
        assert draft.verdict == "AVOID"

    def test_nse_is_asked_for_the_bare_symbol(self, monkeypatch):
        import nsepython

        asked = []

        def fake_quote(symbol):
            asked.append(symbol)
            return {"priceInfo": {"upperCP": 110.0, "lowerCP": 90.0}}

        monkeypatch.setattr(nsepython, "nse_quote", fake_quote)
        status = asyncio.run(market_data.fetch_nse_circuit_status("RELIANCE.NS", 109.9))
        assert asked == ["RELIANCE"]
        assert status == "upper"

    def test_no_band_from_nse_is_unknown_not_invented(self, monkeypatch):
        """The old code used the intraday high as the upper circuit and 90% of it as the lower."""
        import nsepython

        monkeypatch.setattr(nsepython, "nse_quote",
                            lambda s: {"priceInfo": {"intraDayHighLow": {"value": 105.0}}})
        assert asyncio.run(market_data.fetch_nse_circuit_status("X.NS", 104.9)) == "unknown"

    def test_long_term_bronze_marks_circuit_not_checked(self, monkeypatch):
        _fake_sources(monkeypatch, sector="Technology")
        bronze = asyncio.run(bronze_service.build_bronze_payload("TEST", "long_term"))
        assert bronze.circuit_status == "not_checked"


# -------------------------------------------------------- DATA-02 fundamentals

class TestFundamentalsAreNeverInvented:
    def test_missing_info_fields_are_none_not_zero(self):
        funds = _fundamentals({"sector": "Technology"})
        for key in ("trailingPE", "returnOnEquity", "debtToEquity", "revenueGrowth", "earningsGrowth",
                    "roe_pct", "debt_to_equity_x"):
            assert funds[key] is None, f"{key} must be unknown, not a number"

    def test_debt_to_equity_is_converted_from_a_percentage_at_the_source(self):
        """INFY reports 9.541 (percent). It was read as 9.5x and failed the 1.5x ceiling (DATA-04)."""
        funds = _fundamentals({"debtToEquity": 9.541})
        assert funds["debt_to_equity_x"] == pytest.approx(0.09541)
        silver = compute_silver_metrics(_bronze("swing", funds))
        assert silver.debt_to_equity == pytest.approx(0.09541)
        assert silver.debt_flag is False

    def test_genuinely_high_leverage_is_still_flagged(self):
        silver = compute_silver_metrics(_bronze("swing", _fundamentals({"debtToEquity": 314.8})))
        assert silver.debt_to_equity == pytest.approx(3.148)
        assert silver.debt_flag is True

    def test_roe_above_100_percent_is_not_misread(self):
        """A fraction above 1.0 used to be taken as already being a percentage."""
        assert _fundamentals({"returnOnEquity": 1.25})["roe_pct"] == pytest.approx(125.0)

    def test_there_is_no_constant_sector_pe(self):
        """A hardcoded 25.0 stood in for every sector's P/E."""
        funds = _fundamentals({"sector": "Technology", "trailingPE": 30.0})
        assert funds.get("sector_pe_median") is None

    def test_a_non_positive_pe_is_unknown(self):
        assert _fundamentals({"trailingPE": -12.0})["trailingPE"] is None

    def test_roe_is_computed_from_statements_when_the_info_field_is_empty(self):
        fin = _statement({"Total Revenue": [1000, 900, 800, 700], "Operating Income": [200, 170, 150, 120],
                          "Net Income": [150, 130, 110, 90]})
        bs = _statement({"Stockholders Equity": [1000, 900, 800, 700], "Total Debt": [100, 120, 140, 160]})
        funds = _fundamentals({"sector": "Technology"}, financials=fin, balance_sheet=bs)
        assert funds["returnOnEquity"] == pytest.approx(0.15)
        assert funds["roe_pct"] == pytest.approx(15.0)
        assert funds["roe_source"] == "statements"
        assert funds["ratios"]["roe_5y"] == pytest.approx(
            [90 / 700 * 100, 110 / 800 * 100, 130 / 900 * 100, 15.0], abs=1e-3)

    def test_operating_margin_series_is_populated_oldest_first(self):
        fin = _statement({"Total Revenue": [1000, 900, 800, 700], "Operating Income": [200, 170, 150, 120],
                          "Net Income": [1, 1, 1, 1]})
        funds = _fundamentals({}, financials=fin)
        assert funds["opm_trend"] == pytest.approx(
            [120 / 700 * 100, 150 / 800 * 100, 170 / 900 * 100, 20.0], abs=1e-3)

    def test_reported_eps_is_preferred_over_net_income_per_share(self):
        fin = _statement({"Total Revenue": [1, 1, 1, 1], "Net Income": [100, 90, 80, 70],
                          "Diluted EPS": [10.0, 9.0, 8.0, 7.0]})
        funds = _fundamentals({"sharesOutstanding": 1.0}, financials=fin)
        assert funds["income_statement_5y"]["eps"] == [7.0, 8.0, 9.0, 10.0]

    def test_missing_share_count_does_not_divide_by_one(self):
        fin = _statement({"Total Revenue": [1, 1, 1, 1], "Net Income": [100, 90, 80, 70]})
        funds = _fundamentals({}, financials=fin)
        assert funds["income_statement_5y"]["eps"] == []


def _bronze(tf, fundamentals, sector_history=None):
    return BronzePayload(ticker="TEST.NS", timeframe=tf, circuit_status="none",
                         price_history=_prices(TODAY), sector_history=sector_history,
                         fundamentals=fundamentals, benchmark_index=None)


class TestSilverDoesNotScoreAbsence:
    def test_no_growth_data_means_no_growth_gate(self):
        silver = compute_silver_metrics(_bronze("positional", {}))
        assert silver.revenue_cagr_3y is None
        assert "revenue_growth" not in evaluate_hard_gates(silver, "none").gate_results

    def test_no_eps_data_means_no_eps_gate(self):
        """It used to become 0% growth and FAIL the long-term EPS gate."""
        silver = compute_silver_metrics(_bronze("long_term", {}))
        assert silver.eps_cagr_5y is None
        assert "eps_growth" not in evaluate_hard_gates(silver, "not_checked").gate_results

    def test_no_pe_means_no_valuation_gate(self):
        """A 0 P/E passed the ceiling for every loss-maker."""
        silver = compute_silver_metrics(_bronze("long_term", {"trailingPE": None}))
        assert silver.trailing_pe is None
        assert "valuation" not in evaluate_hard_gates(silver, "not_checked").gate_results

    def test_yoy_growth_is_used_when_there_is_no_multi_year_series(self):
        silver = compute_silver_metrics(_bronze("positional", {"revenueGrowth": 0.12}))
        assert silver.revenue_cagr_3y == pytest.approx(12.0)

    def test_margin_trend_is_unknown_without_data_and_real_with_it(self):
        assert compute_silver_metrics(_bronze("positional", {})).opm_trend is None
        rising = compute_silver_metrics(_bronze("positional", {"opm_trend": [12.0, 14.0, 17.0]}))
        assert rising.opm_trend == "expanding"

    def test_unknown_leverage_is_not_a_balance_sheet_pass(self):
        silver = compute_silver_metrics(_bronze("swing", {"debtToEquity": None}))
        assert silver.debt_flag is None
        assert "balance_sheet" not in evaluate_hard_gates(silver, "none").gate_results

    def test_no_sector_pe_means_no_relative_valuation(self):
        silver = compute_silver_metrics(_bronze("swing", {"trailingPE": 30.0}))
        assert silver.pe_vs_sector_avg is None

    def test_long_term_labels_are_unknown_without_data(self):
        silver = compute_silver_metrics(_bronze("long_term", {}))
        assert silver.roe_consistency_5y is None
        assert silver.debt_trajectory is None
        assert silver.pe_band_vs_growth is None


# ------------------------------------------------------------- DATA-03 benchmark

def _fake_sources(monkeypatch, sector, industry=None, fresh=("^NSEI", "^CNXIT")):
    """Fresh history for the tickers in `fresh`; the rest stop in July, like Yahoo's."""

    async def history(ticker, period, interval):
        if ticker.startswith("^"):
            end = TODAY if ticker in fresh else date(2026, 7, 17)
            return _prices(end, rows=400, drift=0.0005)
        return _prices(TODAY, rows=300)

    async def funds(ticker):
        return {"sector": sector, "industry": industry}

    async def circuit(ticker, price):
        return "unknown"

    monkeypatch.setattr(bronze_service, "fetch_yfinance_history", history)
    monkeypatch.setattr(bronze_service, "fetch_yfinance_fundamentals", funds)
    monkeypatch.setattr(bronze_service, "fetch_nse_circuit_status", circuit)


class TestBenchmark:
    def test_yfinance_sector_names_map_to_a_sector_index(self):
        assert bronze_service.benchmark_candidates({"sector": "Technology"}) == ["^CNXIT", "^NSEI"]

    def test_banks_use_the_bank_index(self):
        cands = bronze_service.benchmark_candidates({"sector": "Financial Services", "industry": "Banks - Regional"})
        assert cands[0] == "^NSEBANK"

    def test_unmapped_sector_falls_back_to_the_broad_market(self):
        assert bronze_service.benchmark_candidates({"sector": "Communication Services"}) == ["^NSEI"]
        assert bronze_service.benchmark_candidates(None) == ["^NSEI"]

    def test_a_fresh_sector_index_is_used(self, monkeypatch):
        _fake_sources(monkeypatch, sector="Technology")
        bronze = asyncio.run(bronze_service.build_bronze_payload("TEST", "swing"))
        assert bronze.benchmark_index == "NIFTY IT"

    def test_a_stale_sector_index_is_replaced_by_the_nifty_50(self, monkeypatch):
        """Yahoo's auto index stopped in July while still returning rows."""
        _fake_sources(monkeypatch, sector="Consumer Cyclical", industry="Auto Manufacturers")
        bronze = asyncio.run(bronze_service.build_bronze_payload("TEST", "swing"))
        assert bronze.benchmark_index == "NIFTY 50"

    def test_relative_strength_and_regime_are_actually_computed(self, monkeypatch):
        _fake_sources(monkeypatch, sector="Technology")
        bronze = asyncio.run(bronze_service.build_bronze_payload("TEST", "swing"))
        silver = compute_silver_metrics(bronze)
        assert silver.stock_vs_sector_rs is not None
        assert silver.market_regime in {"bullish", "bearish", "neutral"}
        assert silver.benchmark_index == "NIFTY IT"
        assert "sector" in evaluate_hard_gates(silver, bronze.circuit_status).gate_results

    def test_regime_is_unknown_without_a_benchmark_not_neutral(self):
        silver = compute_silver_metrics(_bronze("swing", {}))
        assert silver.market_regime is None

    def test_a_bearish_benchmark_suppresses_a_bullish_verdict(self):
        """The override that never fired, because the regime was never computed."""
        falling = _prices(TODAY, rows=300, start_price=200.0, drift=-0.002)
        bronze = BronzePayload(ticker="TEST.NS", timeframe="swing", circuit_status="none",
                               price_history=_prices(TODAY), sector_history=falling,
                               fundamentals={}, benchmark_index="NIFTY 50")
        assert compute_silver_metrics(bronze).market_regime == "bearish"
