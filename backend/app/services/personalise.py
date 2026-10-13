"""The personal layer: one stock verdict, output fitted to one user.

docs/verdict_engine_plan.md, Phase 3, decision D1. The verdict word never
changes here. This decides what the verdict means for this user's money:
risk per trade, position size and cap, whether a setup is shown, fit notes,
a horizon note and how many watch items to show.

Pure: no I/O. Works on v1 and v2 output alike, because it reads only the
verdict, the stock-level price levels and Silver metrics. Nothing it returns
belongs in the owner-less ledger row; it is per user.
"""
import math
from typing import Any, List, Optional

from pydantic import BaseModel

from app.schemas.silver import SilverMetrics
from app.services.gold_service import atr_levels
from config.gate_thresholds import GATE_THRESHOLDS as TH
from config.personal_rules import (
    DEFAULT_EXPERIENCE, DEFAULT_RISK, POSITION_CAP, RISK_PER_TRADE,
    SETUP_SHOWN_FOR, WATCH_ITEMS_FOR,
)

HIGH_VOLATILITY_ATR_PCT = 3.0   # daily ATR above 3% of price


class PersonalPlan(BaseModel):
    risk_level: str
    risk_per_trade_pct: float
    risk_per_trade_inr: Optional[float] = None
    position_cap_inr: Optional[float] = None
    position_size: Optional[int] = None
    position_value_inr: Optional[float] = None
    capped_by_limit: bool = False
    setup: Optional[dict] = None
    staged_entry: bool = False
    fit_notes: List[str] = []
    horizon_note: Optional[str] = None
    what_to_watch: List[str] = []


def _pick(profile: dict, *keys: str, default: Any = None) -> Any:
    """Profiles arrive as the onboarding shape (risk, capital) or the API shape
    (risk_tolerance, available_capital); read whichever is present."""
    for key in keys:
        if profile.get(key) is not None:
            return profile[key]
    return default


def _capital(profile: dict) -> float:
    raw = _pick(profile, "capital", "available_capital", default=0.0)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return value if math.isfinite(value) and value > 0 else 0.0


def _staged_levels(s: SilverMetrics) -> Optional[dict]:
    """A dip entry anchored at the nearest moving-average floor below price."""
    floors = [sma for sma in (s.sma_50, s.sma_200) if sma and sma <= s.current_price]
    if not floors or not s.atr_14:
        return None
    return atr_levels(max(floors), s.atr_14, s.timeframe)


def _fit_notes(s: SilverMetrics, goal: Optional[str], risk: str, verdict: str) -> List[str]:
    notes = []
    if goal == "capital_preservation":
        if s.debt_to_equity is not None and s.debt_to_equity > TH["debt_equity_max"]:
            notes.append(f"Debt/equity of {s.debt_to_equity:.2f}x is above the {TH['debt_equity_max']}x "
                         "ceiling: a poor fit for capital preservation.")
        if s.atr_14 and s.current_price and s.atr_14 / s.current_price * 100 > HIGH_VOLATILITY_ATR_PCT:
            notes.append("This stock moves more than 3% on a typical day: a poor fit for capital preservation.")
        if risk == "aggressive":
            notes.append("Your profile pairs an aggressive risk level with a capital preservation goal.")
    if goal == "dividend_income":
        notes.append("Dividend data is not part of this analysis. Check the payout record before relying on income.")
    if risk == "conservative" and s.timeframe == "intraday":
        notes.append("Intraday trading carries the most risk of any horizon for a conservative profile.")
    if verdict == "BUY ON DIP" and verdict not in SETUP_SHOWN_FOR[risk]:
        notes.append(f"At a {risk} risk level, a trade setup is shown only for STRONG BUY.")
    return notes


def personalise(verdict: str, silver: SilverMetrics, levels: Optional[dict],
                what_to_watch: List[str], profile: dict) -> PersonalPlan:
    risk = _pick(profile, "risk", "risk_tolerance", default=DEFAULT_RISK)
    risk = risk if risk in RISK_PER_TRADE else DEFAULT_RISK
    experience = _pick(profile, "experience", "experience_level", default=DEFAULT_EXPERIENCE)
    capital = _capital(profile)

    plan = {
        "risk_level": risk,
        "risk_per_trade_pct": RISK_PER_TRADE[risk] * 100,
        "fit_notes": _fit_notes(silver, _pick(profile, "goal"), risk, verdict),
        "what_to_watch": what_to_watch[:WATCH_ITEMS_FOR.get(experience, WATCH_ITEMS_FOR[DEFAULT_EXPERIENCE])],
    }

    profile_tf = _pick(profile, "timeframe")
    if profile_tf and profile_tf != silver.timeframe:
        plan["horizon_note"] = (f"Your profile horizon is {profile_tf.replace('_', ' ')}; "
                                f"this is a {silver.timeframe.replace('_', ' ')} read.")

    setup = None
    if verdict in SETUP_SHOWN_FOR[risk]:
        if verdict == "BUY ON DIP":
            setup = _staged_levels(silver)
            plan["staged_entry"] = setup is not None
        else:
            setup = levels
    plan["setup"] = setup

    if setup and capital > 0:
        entry = (setup["entry_zone_low"] + setup["entry_zone_high"]) / 2
        risk_inr = capital * RISK_PER_TRADE[risk]
        cap_inr = capital * POSITION_CAP[risk]
        by_risk = int(risk_inr / max(entry - setup["stop_loss"], 0.01))
        by_cap = int(cap_inr / entry)
        size = max(0, min(by_risk, by_cap))
        plan.update(
            risk_per_trade_inr=round(risk_inr, 2),
            position_cap_inr=round(cap_inr, 2),
            position_size=size,
            position_value_inr=round(size * entry, 2),
            capped_by_limit=by_cap < by_risk,
        )

    return PersonalPlan(**plan)
