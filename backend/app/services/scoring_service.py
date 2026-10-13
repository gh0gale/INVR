"""Verdict engine v2: weighted factor scores to one of the five verdicts.

docs/verdict_engine_plan.md, Phase 1. Runs in shadow beside v1
(`gold_service.evaluate_hard_gates`); users see v1 until the cutover.

1. Score every factor the horizon weights (`config/factor_weights.py`).
2. Composite = weighted mean, a missing factor counting as 0, so composites
   stay comparable across tickers. Coverage = weight share that had data.
3. Composite to verdict through fixed cutoffs.
4. Caps, in order: low coverage, circuit, v1's volume confirmation and dip
   support rules, bearish regime. A cap only ever lowers a verdict.
"""
from app.schemas.gold import PriceLevels, ScoredVerdict
from app.schemas.silver import SilverMetrics
from app.services.factors import FACTORS, VOLUME_STRONG_RATIO
from app.services.gold_service import atr_levels
from config.factor_weights import (
    COVERAGE_FLOOR, FACTOR_WEIGHTS, FALLBACK_VERDICT, RULESET_V2, VERDICT_CUTOFFS,
)

ORDER = ["AVOID", "CAUTION", "MONITOR", "BUY ON DIP", "STRONG BUY"]
BULLISH = ("STRONG BUY", "BUY ON DIP")
DIP_SUPPORT_BUFFER = 0.03     # as v1: within 3% of the 50 or 200 SMA


def _from_composite(composite: float) -> str:
    for verdict, cutoff in VERDICT_CUTOFFS:
        if composite >= cutoff:
            return verdict
    return FALLBACK_VERDICT


def _near_support(s: SilverMetrics) -> bool:
    return any(
        sma and sma * (1 - DIP_SUPPORT_BUFFER) <= s.current_price <= sma * (1 + DIP_SUPPORT_BUFFER)
        for sma in (s.sma_50, s.sma_200)
    )


def _apply_caps(verdict: str, s: SilverMetrics, circuit_status: str, coverage: float) -> tuple[str, list[str]]:
    caps = []

    def cap(ceiling: str, why: str) -> None:
        nonlocal verdict
        if ORDER.index(verdict) > ORDER.index(ceiling):
            verdict = ceiling
            caps.append(why)

    if coverage < COVERAGE_FLOOR:
        cap("MONITOR", f"Insufficient data: {coverage:.0%} of the factor weight had inputs.")
    if circuit_status == "lower":
        cap("AVOID", "Lower circuit: entry is blocked until limits normalise.")
    elif circuit_status == "upper":
        cap("MONITOR", "Upper circuit: wait for the stock to exit it to ensure liquidity.")
    if verdict == "STRONG BUY" and s.current_volume and s.volume_avg_20 \
            and s.current_volume / s.volume_avg_20 < VOLUME_STRONG_RATIO:
        cap("MONITOR", "Strong score, but volume does not confirm institutional participation.")
    if verdict == "BUY ON DIP" and not _near_support(s):
        cap("CAUTION", "Dip candidate is not near 50/200 SMA support.")
    if s.market_regime == "bearish" and verdict in BULLISH:
        cap("CAUTION", "Market regime is bearish; bullish setups are suppressed.")
    return verdict, caps


def score_v2(silver: SilverMetrics, circuit_status: str) -> ScoredVerdict:
    tf = silver.timeframe
    weights = FACTOR_WEIGHTS[tf]
    factors = [FACTORS[name](silver).model_copy(update={"weight": w}) for name, w in weights.items()]

    total = sum(weights.values())
    covered = [f for f in factors if f.score is not None]
    composite = sum(f.score * f.weight for f in covered) / total
    coverage = sum(f.weight for f in covered) / total

    verdict, caps = _apply_caps(_from_composite(composite), silver, circuit_status, coverage)

    # Agreement: weight share of scored factors on the composite's side.
    sign = 1 if composite >= 0 else -1
    agree_w = sum(f.weight for f in covered if f.score * sign > 0)
    agreement = agree_w / sum(f.weight for f in covered) if covered else 0.0
    confidence = 50.0 + 45.0 * coverage * (0.5 * abs(composite) + 0.5 * agreement)

    ranked = sorted(covered, key=lambda f: f.score * f.weight)
    if caps:
        reason = caps[-1]
    elif composite >= 0:
        reason = "Led by " + ", ".join(f.reason for f in reversed(ranked[-2:]) if f.score > 0) + "." \
            if any(f.score > 0 for f in ranked) else "No factor is clearly positive."
    else:
        reason = "Held back by " + ", ".join(f.reason for f in ranked[:2] if f.score < 0) + "."

    # Levels only where v1 emits them, so the shared grading rule reads both alike.
    levels = None
    if verdict == "STRONG BUY" and tf != "long_term" and silver.atr_14:
        levels = PriceLevels(**atr_levels(silver.current_price, silver.atr_14, tf))

    return ScoredVerdict(
        ruleset=RULESET_V2,
        ticker=silver.ticker,
        timeframe=tf,
        verdict=verdict,
        composite=round(composite, 4),
        coverage=round(coverage, 4),
        confidence_score=round(confidence, 1),
        primary_reason=reason,
        caps_applied=caps,
        factors=factors,
        what_to_watch=[f.watch_item for f in ranked if f.watch_item] + caps,
        price_levels=levels,
    )
