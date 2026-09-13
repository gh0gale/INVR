"""Shared fixtures for the Gold and trade-setup tests.

The builder returns a metric set that clears every swing gate, so each test
changes exactly one thing and asserts on the consequence. That keeps a failure
message pointing at the rule that broke rather than at the fixture.
"""
import pytest

from app.schemas.silver import SilverMetrics



@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Point the local file cache at a per-test directory.

    Without this the synthesis cache added for P4-06 persists in
    `backend/.local_cache/` between runs, so a cached narrative made
    `llm_synthesizer_node` return before it ever built a prompt - and the prompt
    tests asserted against an empty string. Hidden on-disk state deciding
    whether a test passes is exactly the failure mode the cache must not have.
    """
    monkeypatch.setenv("INVR_CACHE_DIR", str(tmp_path / "cache"))


def make_silver(**overrides) -> SilverMetrics:
    """A swing profile that passes every gate unless a test says otherwise."""
    base = dict(
        ticker="TEST.NS",
        timeframe="swing",
        current_price=2800.0,
        current_volume=5_000_000.0,   # 2.5x the 20-period average
        volume_avg_20=2_000_000.0,
        sma_20=2700.0,                # price above the 20 SMA
        sma_50=2650.0,
        rsi_14=55.0,                  # between the oversold and overbought gates
        atr_14=40.0,
        stock_vs_sector_rs=0.02,      # outperforming its sector
        market_regime="bullish",
    )
    base.update(overrides)
    return SilverMetrics(**base)


@pytest.fixture
def silver() -> SilverMetrics:
    return make_silver()
