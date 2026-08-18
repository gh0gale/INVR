"""The ledger version must track the ruleset that produced a prediction.

Audit finding NEW-BE-06: the version sat at v1.0.0 while gate thresholds moved,
so the Engine Room graded predictions from different rulesets as one cohort.
The threshold half of the version is now derived, and these tests assert it
actually changes when the rules do.
"""
import hashlib
import json

from config.gate_thresholds import GATE_THRESHOLDS
from app.services.ledger_service import PIPELINE_VERSION, RULESET_VERSION


def _fingerprint(thresholds: dict) -> str:
    return hashlib.sha256(
        json.dumps(thresholds, sort_keys=True).encode("utf-8")
    ).hexdigest()[:8]


def test_version_combines_ruleset_and_threshold_fingerprint():
    assert PIPELINE_VERSION.startswith(RULESET_VERSION + "-")
    assert PIPELINE_VERSION.endswith(_fingerprint(GATE_THRESHOLDS))


def test_changing_any_threshold_changes_the_version():
    """This is the whole point: a silent rule change must not reuse a version."""
    moved = dict(GATE_THRESHOLDS)
    moved["rsi_overbought"] = GATE_THRESHOLDS["rsi_overbought"] + 1.0
    assert _fingerprint(moved) != _fingerprint(GATE_THRESHOLDS)


def test_fingerprint_is_stable_across_key_ordering():
    """Dict ordering must not produce a spurious new version."""
    shuffled = dict(reversed(list(GATE_THRESHOLDS.items())))
    assert _fingerprint(shuffled) == _fingerprint(GATE_THRESHOLDS)


def test_version_is_no_longer_the_stale_literal():
    assert PIPELINE_VERSION != "v1.0.0"
