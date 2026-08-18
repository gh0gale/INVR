"""Bootstrap machinery behind the drift analyser.

Audit finding NEW-BE-12: confidence used to be `50 + sample_size/500 * 45`,
which is a restatement of the row count wearing the clothes of a statistic.
These tests assert the replacement behaves like an interval estimator.
"""
import numpy as np
import pytest

from scripts.analyze_drift import bootstrap_quantile_ci, confidence_from_interval


def test_interval_brackets_the_point_estimate():
    values = np.random.default_rng(1).normal(60, 5, 400)
    low, high, point = bootstrap_quantile_ci(values, 0.90)
    assert low <= point <= high


def test_interval_narrows_as_evidence_grows():
    """More data should buy a tighter interval. The old formula could not do this."""
    rng = np.random.default_rng(2)
    small = bootstrap_quantile_ci(rng.normal(60, 5, 30), 0.50)
    large = bootstrap_quantile_ci(rng.normal(60, 5, 2000), 0.50)
    assert (large[1] - large[0]) < (small[1] - small[0])


def test_result_is_reproducible_across_runs():
    """A fixed generator means two analyses of one dataset agree."""
    values = np.linspace(40, 80, 200)
    assert bootstrap_quantile_ci(values, 0.90) == bootstrap_quantile_ci(values, 0.90)


def test_confidence_rewards_a_tight_interval():
    tight = confidence_from_interval(59.0, 61.0, 60.0)
    loose = confidence_from_interval(30.0, 90.0, 60.0)
    assert tight > loose


def test_confidence_stays_inside_its_declared_range():
    for low, high, point in [(0.0, 1000.0, 1.0), (59.9, 60.1, 60.0), (0.0, 0.0, 0.0)]:
        score = confidence_from_interval(low, high, point)
        assert 50.0 <= score <= 95.0


def test_confidence_is_not_merely_the_sample_size():
    """Same n, different spread, must not produce the same confidence."""
    rng = np.random.default_rng(3)
    tight_vals = rng.normal(60, 1, 300)
    wide_vals = rng.normal(60, 25, 300)
    tight = confidence_from_interval(*bootstrap_quantile_ci(tight_vals, 0.50))
    wide = confidence_from_interval(*bootstrap_quantile_ci(wide_vals, 0.50))
    assert tight > wide


@pytest.mark.parametrize("q", [0.10, 0.50, 0.90])
def test_quantile_estimate_tracks_the_requested_quantile(q):
    values = np.linspace(0, 100, 1000)
    _, _, point = bootstrap_quantile_ci(values, q)
    assert point == pytest.approx(q * 100, abs=2.0)
