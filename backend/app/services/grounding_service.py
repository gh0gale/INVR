"""Does the narrative cite only numbers the engine produced?

improvements #6, audit NARR-01. `validate_synthesis_node` overwrites the
verdict, the confidence and the disclaimer from the Gold layer, but the prose
around them is the model's own. A figure in that prose which traces to no
Silver metric, Gold figure or configured threshold is a figure the model
invented, and nothing measured how often that happened. It matters more now
that the model can change underneath the same prompt (app/llm.py).

This measures and never blocks. The path is user-facing, and a false positive
(a figure derived in a way not listed here) must not cost the user their tear
sheet. The score rides on the ledger row and the span, so a provider or prompt
change that moves it is visible in the Engine Room.
"""
import re
from typing import Any, Iterable, List, Optional

from config.gate_thresholds import GATE_THRESHOLDS

TEXT_FIELDS = ("personalized_reasoning", "what_to_watch", "risk_warning")

# 1,23,456.78 (Indian grouping), 2,847.50, 58.2, 70
NUMBER = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)")
# Any hyphen or dash. gpt-oss writes "20‑day" with U+2011, and a plain "-"
# pattern let every such period through as an ungrounded figure.
_DASH = "\\-\u2010\u2011\u2012\u2013\u2014\u2015"
# "20-day", "50 DMA", "200-week": a period, not a claim
PERIOD_AFTER = re.compile(rf"^\s?[{_DASH}]?\s?(day|days|week|weeks|month|months|year|years|period|periods|bar|bars|dma|sma|ema|session|sessions)\b", re.I)
# "SMA 20", "RSI(14)", "NIFTY 50": part of a name - but only for the whole
# numbers such names actually take. "RSI 58.2" is a reading, not a period.
PERIOD_BEFORE = re.compile(rf"(sma|dma|ema|rsi|atr|nifty|sensex)\s?[{_DASH}(]?\s?$", re.I)
# "1.8 million", "2.1M", "3 lakh", "4,500 crore": the figure is scaled.
SCALE = re.compile(r"^\s?(million|mn|m|lakhs?|lacs?|crores?|cr|billion|bn|b|thousand|k)\b", re.I)
SCALE_FACTOR = {"million": 1e6, "mn": 1e6, "m": 1e6, "lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5,
                "crore": 1e7, "crores": 1e7, "cr": 1e7, "billion": 1e9, "bn": 1e9, "b": 1e9,
                "thousand": 1e3, "k": 1e3}
NAMED_PERIODS = {5, 7, 9, 10, 12, 14, 20, 21, 26, 30, 50, 100, 200, 500}

MAX_LISTED = 8


def _numbers_in(text: str) -> List[tuple]:
    """(value, as written) for every figure in the text that is a claim."""
    found = []
    for m in NUMBER.finditer(text):
        raw = m.group(1)
        value = float(raw.replace(",", ""))
        after, before = text[m.end():m.end() + 12], text[max(0, m.start() - 8):m.start()]
        is_integer = "." not in raw
        if PERIOD_AFTER.match(after):
            continue
        if is_integer and value in NAMED_PERIODS and PERIOD_BEFORE.search(before):
            continue
        if is_integer and 1900 <= value <= 2100 and "," not in raw:
            continue                      # a year
        scale = SCALE.match(after)
        if scale:
            value *= SCALE_FACTOR[scale.group(1).lower()]
        elif is_integer and value <= 3 and not after.lstrip().startswith(("%", "x")):
            continue                      # "2 sentences", "1 of 3"
        found.append((value, raw))
    return found


def _floats(obj: Any) -> Iterable[float]:
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        if obj == obj:                    # not NaN
            yield float(obj)
    elif isinstance(obj, str):
        for value, _ in _numbers_in(obj):
            yield value
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _floats(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _floats(v)


def _as_dict(obj: Any) -> dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj if isinstance(obj, dict) else {}


def reference_values(silver: Any, gold: Any) -> List[float]:
    """Every figure the narrative may legitimately quote."""
    s, g = _as_dict(silver), _as_dict(gold)
    # Gold's own text (watch list, reason) counts: its figures are engine-made,
    # e.g. the volume target is volume_avg_20 x the configured ratio.
    refs = list(_floats(s)) + list(_floats(g)) + list(_floats(GATE_THRESHOLDS))

    # Figures a tear sheet routinely derives from two engine numbers.
    price = s.get("current_price")
    for key in ("sma_20", "sma_50", "sma_200"):
        if price and s.get(key):
            refs.append((price - s[key]) / s[key] * 100)
    if s.get("current_volume") and s.get("volume_avg_20"):
        refs.append(s["current_volume"] / s["volume_avg_20"])

    expanded = []
    for r in refs:
        expanded += [r, abs(r)]
        if abs(r) <= 1.0:
            expanded.append(abs(r) * 100)  # a fraction quoted as a percentage
    return expanded


def _grounded(value: float, refs: List[float]) -> bool:
    # 0.051 absorbs rounding to one decimal place; 1% absorbs rounding of
    # large figures (a price quoted to the rupee, a volume to the lakh).
    return any(abs(value - r) <= max(0.051, abs(r) * 0.01) for r in refs)


def score_grounding(narrative: dict, silver: Any, gold: Any) -> dict:
    """{score, checked, ungrounded_count, ungrounded}. score is None when the prose has no figures."""
    refs = reference_values(silver, gold)
    texts: List[str] = []
    for field in TEXT_FIELDS:
        value = (narrative or {}).get(field)
        texts.extend(value if isinstance(value, list) else [value] if value else [])

    checked, missing = 0, []
    for text in texts:
        for value, raw in _numbers_in(str(text)):
            checked += 1
            if not _grounded(value, refs):
                missing.append(raw)

    score: Optional[float] = round((checked - len(missing)) / checked, 3) if checked else None
    return {
        "score": score,
        "checked": checked,
        "ungrounded_count": len(missing),
        "ungrounded": missing[:MAX_LISTED],
    }
