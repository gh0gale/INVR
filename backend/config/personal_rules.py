# config/personal_rules.py
#
# Per-profile numbers for the personal layer (app/services/personalise.py,
# docs/verdict_engine_plan.md Phase 3). The verdict is the same for every
# user; these only change what the output says to this user.
#
# PROPOSED values, awaiting the owner's confirmation (plan section 7).

RISK_PER_TRADE = {            # fraction of capital risked between entry and stop
    "conservative": 0.01,
    "moderate": 0.02,         # v1's fixed value
    "aggressive": 0.03,
}

POSITION_CAP = {              # max fraction of capital in one stock
    "conservative": 0.05,
    "moderate": 0.10,
    "aggressive": 0.15,
}

SETUP_SHOWN_FOR = {           # verdicts that get a trade setup, per risk level
    "conservative": ("STRONG BUY",),
    "moderate": ("STRONG BUY",),
    "aggressive": ("STRONG BUY", "BUY ON DIP"),
}

WATCH_ITEMS_FOR = {           # how many watch items to show; None = all
    "beginner": 3,
    "intermediate": 5,
    "advanced": None,
}

DEFAULT_RISK = "moderate"
DEFAULT_EXPERIENCE = "intermediate"
