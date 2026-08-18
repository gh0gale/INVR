"""One grading rule, shared by the live grader and the historical simulator.

Audit findings NEW-BE-09 and NEW-BE-10.

Before this module, `grade_ledger.py` scored against the stored ATR trade setup
while `simulate_live_history.py` scored against a flat ±5%. Two different rules
fed the same drift analysis, so backtest and live outcomes were not comparable.
`MONITOR` also had no definition at all and always fell through to DRAW, which
quietly excluded a growing share of predictions from the track record.

The semantics are written down here so they are auditable rather than implied.
"""
from typing import Optional

# Verdicts that express a directional expectation.
BULLISH = ("STRONG BUY", "BUY ON DIP")
BEARISH = ("CAUTION", "AVOID")

# Fallback band when a prediction carries no ATR setup (for example a
# non-STRONG BUY verdict, where the engine deliberately generates no levels).
DEFAULT_TARGET_PCT = 0.05
DEFAULT_STOP_PCT = 0.05


def resolve_levels(entry_price: float, setup: Optional[dict]) -> tuple[float, float]:
    """The target and stop a prediction is judged against.

    Uses the setup the engine actually produced when there is one, so a graded
    outcome reflects the levels the user was shown.
    """
    if setup and setup.get("target_1") is not None and setup.get("stop_loss") is not None:
        return float(setup["target_1"]), float(setup["stop_loss"])
    return (
        entry_price * (1 + DEFAULT_TARGET_PCT),
        entry_price * (1 - DEFAULT_STOP_PCT),
    )


def resolve_outcome(
    verdict: str,
    entry_price: float,
    setup: Optional[dict],
    max_high: float,
    min_low: float,
) -> str:
    """Score one matured prediction as WIN, LOSS or DRAW.

    Semantics, stated explicitly:

    * **Bullish** (`STRONG BUY`, `BUY ON DIP`) asserts the target is reached.
      Target hit is a WIN, stop hit is a LOSS, neither is a DRAW.
    * **Bearish** (`CAUTION`, `AVOID`) asserts staying out was right. The stop
      being hit is a WIN, because avoiding it is what the call was for. The
      target being hit is a LOSS, because the caution cost a real move.
    * **`MONITOR`** asserts that no decisive move is coming yet. Price staying
      inside the band is a WIN. A decisive break in either direction means the
      wait-and-see call was wrong, so it is a LOSS.

    Known limitation: daily highs and lows carry no intraday sequence, so when
    both levels are touched in the same window the order is unknowable. Every
    branch below resolves that tie the same way, in the direction that counts
    against the prediction, so the record errs pessimistic rather than flattering.
    """
    if entry_price is None or entry_price <= 0:
        return "DRAW"

    target, stop = resolve_levels(entry_price, setup)
    hit_target = max_high >= target
    hit_stop = min_low <= stop

    verdict = (verdict or "").upper()

    if verdict in BULLISH:
        if hit_stop:
            return "LOSS"          # pessimistic tie-break
        if hit_target:
            return "WIN"
        return "DRAW"

    if verdict in BEARISH:
        if hit_target:
            return "LOSS"          # pessimistic tie-break: the caution cost a move
        if hit_stop:
            return "WIN"
        return "DRAW"

    if verdict == "MONITOR":
        return "LOSS" if (hit_target or hit_stop) else "WIN"

    return "DRAW"
