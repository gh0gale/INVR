"""Shared fixtures for the Gold and trade-setup tests.

The builder returns a metric set that clears every swing gate, so each test
changes exactly one thing and asserts on the consequence. That keeps a failure
message pointing at the rule that broke rather than at the fixture.
"""
import pytest

from app.schemas.silver import SilverMetrics


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
