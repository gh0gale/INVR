"""Narrative number grounding (improvements #6, audit NARR-01).

The verdict and confidence are forced from Gold; the prose is the model's. These
tests pin what counts as a figure the engine produced, what counts as noise
(periods, years, counting words), and what counts as invented.
"""
import json

import pytest

from app.orchestrator import validate_synthesis_node
from app.services.grounding_service import _numbers_in, score_grounding
from config.gate_thresholds import GATE_THRESHOLDS as TH

SILVER = {
    "current_price": 2847.5,
    "sma_20": 2700.0,
    "sma_50": 2650.0,
    "rsi_14": 58.24,
    "current_volume": 5_000_000.0,
    "volume_avg_20": 2_000_000.0,
    "roe_pct": 18.4,
}
GOLD = {
    "verdict": "MONITOR",
    "confidence_score": 78.4,
    "primary_reason": "Held back by lagging Momentum (RSI).",
    "what_to_watch": ["Wait for volume to cross 3,000,000 to confirm institutional participation."],
}


def _score(*sentences):
    return score_grounding({"personalized_reasoning": list(sentences)}, SILVER, GOLD)


class TestWhatCountsAsAClaim:
    def test_periods_and_names_are_not_claims(self):
        text = "Price is above the 20-day SMA and the 50 DMA, RSI(14) is firm, NIFTY 50 is flat."
        assert _numbers_in(text) == []

    def test_years_and_counting_words_are_not_claims(self):
        assert _numbers_in("Since 2024, two of 3 gates held.") == []

    def test_unicode_dashes_still_mark_a_period(self):
        """gpt-oss writes '20‑day' with a non-breaking hyphen (U+2011)."""
        assert _numbers_in("below the 20‑day SMA and the 50–day line") == []

    def test_scale_words_multiply_the_figure(self):
        values = [v for v, _ in _numbers_in("1.8 million shares, 3 lakh, 4,500 crore, 2.5M")]
        assert values == [1.8e6, 3e5, 4.5e10, 2.5e6]

    def test_percentages_prices_and_ratios_are_claims(self):
        values = [v for v, _ in _numbers_in("Up 5.5% to ₹2,847.50 on 2.5x volume")]
        assert values == [5.5, 2847.5, 2.5]


class TestGrounding:
    def test_engine_figures_are_grounded(self):
        g = _score("RSI sits at 58.2 with price at ₹2,847.50 and ROE of 18.4%.")
        assert g["score"] == 1.0
        assert g["ungrounded"] == []

    def test_a_derived_gap_to_a_moving_average_is_grounded(self):
        # (2847.5 - 2700) / 2700 = 5.46%
        assert _score("It trades 5.5% above its 20-day average.")["score"] == 1.0

    def test_volume_ratio_and_gold_watch_figures_are_grounded(self):
        assert _score("Volume is 2.5x normal; watch for 3,000,000 shares.")["score"] == 1.0

    def test_volumes_written_in_millions_are_grounded(self):
        assert _score("Volume of 5 million against a 2 million average.")["score"] == 1.0
        assert _score("Volume of 2.7 million today.")["ungrounded"] == ["2.7"]

    def test_configured_thresholds_are_grounded(self):
        assert _score(f"A reading above {TH['rsi_overbought']} would be overbought.")["score"] == 1.0

    def test_an_invented_figure_is_reported(self):
        g = _score("RSI is 58.2 and revenue grew 37.4% last year.")
        assert g["ungrounded"] == ["37.4"]
        assert g["score"] == 0.5
        assert g["checked"] == 2

    def test_prose_without_figures_has_no_score(self):
        g = _score("The trend is intact but momentum is fading.")
        assert g["score"] is None and g["checked"] == 0

    def test_all_three_text_fields_are_read(self):
        g = score_grounding(
            {"personalized_reasoning": ["RSI 58.2"], "what_to_watch": ["hold 99.9"], "risk_warning": "down 41.7%"},
            SILVER, GOLD,
        )
        assert g["checked"] == 3
        assert sorted(g["ungrounded"]) == ["41.7", "99.9"]


def test_validation_attaches_grounding_to_the_narrative():
    narrative = {
        "personalized_reasoning": ["RSI is 58.2, and margins expanded 44.4%."],
        "what_to_watch": ["Hold above ₹2,700.00."],
        "risk_warning": "Momentum could fade.",
        "tutor_triggers": ["RSI", "SMA"],
    }
    state = {"llm_output": {"raw_json_string": json.dumps(narrative)}, "silver": SILVER, "gold": GOLD, "errors": []}
    out = validate_synthesis_node(state)["llm_output"]
    assert out["verdict"] == "MONITOR", "Gold still overrides the verdict"
    assert out["grounding"]["checked"] == 3
    assert out["grounding"]["ungrounded"] == ["44.4"]
    assert out["grounding"]["score"] == pytest.approx(0.667)
