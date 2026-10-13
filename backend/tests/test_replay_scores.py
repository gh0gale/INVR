"""Pure parts of scripts/replay_scores.py. No network."""
import numpy as np
import pandas as pd
import pytest

from scripts.replay_scores import (
    VERDICT_ORDINAL,
    block_bootstrap_ci,
    excess_return,
    forward_close,
    per_date_ic,
)


def test_verdict_ordinal_covers_the_vocabulary_in_order():
    assert list(VERDICT_ORDINAL) == ["STRONG BUY", "BUY ON DIP", "MONITOR", "CAUTION", "AVOID"]
    assert list(VERDICT_ORDINAL.values()) == [2, 1, 0, -1, -2]


def test_excess_return_subtracts_the_benchmark_move():
    assert excess_return(100, 110, 1000, 1050) == pytest.approx(0.05)


def test_forward_close_takes_first_bar_on_or_after_target_and_none_past_data():
    idx = pd.to_datetime(["2026-01-01", "2026-01-05", "2026-01-20"])
    closes = pd.Series([1.0, 2.0, 3.0], index=idx)
    assert forward_close(closes, idx[0], 3) == 2.0
    assert forward_close(closes, idx[0], 19) == 3.0
    assert forward_close(closes, idx[0], 30) is None


def _samples(scores, excess, date="2026-01-01"):
    return pd.DataFrame({"date": date, "ticker": range(len(scores)),
                         "score": scores, "excess": excess})


def test_per_date_ic_is_one_for_a_perfect_ranking_and_minus_one_reversed():
    up = _samples(list(range(10)), [x / 100 for x in range(10)], "d1")
    down = _samples(list(range(10)), [-x / 100 for x in range(10)], "d2")
    ics = per_date_ic(pd.concat([up, down]), "score")
    assert ics["d1"] == pytest.approx(1.0)
    assert ics["d2"] == pytest.approx(-1.0)


def test_per_date_ic_drops_thin_dates_and_constant_scores():
    thin = _samples([1, 2, 3], [0.1, 0.2, 0.3], "thin")
    flat = _samples([0] * 12, [x / 100 for x in range(12)], "flat")
    assert per_date_ic(pd.concat([thin, flat]), "score").empty


def test_block_bootstrap_interval_brackets_the_mean_and_is_deterministic():
    values = np.random.default_rng(1).normal(0.05, 0.1, 200)
    lo, hi = block_bootstrap_ci(values, block=4)
    assert lo < values.mean() < hi
    assert (lo, hi) == block_bootstrap_ci(values, block=4)
    assert all(np.isnan(block_bootstrap_ci(np.array([]), block=4)))
