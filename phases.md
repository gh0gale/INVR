# FinAI — Pipeline Architecture & Execution Flow

> Complete system design reference. Every phase, every decision, every detail.

---

## Table of Contents


6. [Stage 4 — Gold Layer: The Hard Gate Evaluator](#stage-4--gold-layer-the-hard-gate-evaluator)
7. [Stage 5 — The LangGraph State Object](#stage-5--the-langgraph-state-object)
8. [Stage 6 — The Single LLM Call](#stage-6--the-single-llm-call)
9. [Stage 7 — Trade Setup](#stage-7--trade-setup)
10. [Stage 8 — Logging to Supabase](#stage-8--logging-to-supabase)
11. [Stage 9 — The Tutor System](#stage-9--the-tutor-system)
12. [What to Cut or Defer](#what-to-cut-or-defer)

---



## Stage 4 — Gold Layer: The Hard Gate Evaluator

This is the most important stage in the pipeline. Pure Python logic evaluates the Silver layer metrics against the user's specific constraints and produces a deterministic `VerdictDraft`. The LLM never touches this logic.

### Complete Gate Suite (Positional Timeframe)

```python
def evaluate_positional_gates(silver_data: SilverMetrics, user_profile: UserProfile) -> VerdictDraft:

    gates = {}

    # Gate 1: Trend Gate
    gates["trend"] = "PASS" if silver_data.price > silver_data.sma_50 else "FAIL"

    # Gate 2: Death Cross Gate (uses threshold, not binary)
    cross_status = check_death_cross(silver_data.sma_50, silver_data.sma_200, silver_data.price)
    if cross_status == "CONFIRMED_DEATH_CROSS":
        gates["death_cross"] = "FAIL"
    elif cross_status == "IMMINENT_DEATH_CROSS":
        gates["death_cross"] = "WARN"
    else:
        gates["death_cross"] = "PASS"

    # Gate 3: RSI Gate
    if silver_data.rsi < 25:
        gates["rsi"] = "WARN"           # deeply oversold — potential reversal, not a hard fail
    elif silver_data.rsi > 75:
        gates["rsi"] = "FAIL"           # overbought — late entry risk
    else:
        gates["rsi"] = "PASS"

    # Gate 4: Portfolio Concentration Gate
    asset_class       = silver_data.asset_class
    current_exposure  = user_profile.portfolio.get(asset_class, 0)
    risk_caps         = {"conservative": 0.25, "moderate": 0.45, "aggressive": 0.65}
    cap               = risk_caps[user_profile.risk]
    gates["concentration"] = "FAIL" if current_exposure >= cap else "PASS"

    # Gate 5: Sector Momentum Gate (new — not in original design)
    gates["sector"] = "FAIL" if silver_data.stock_vs_sector_rs < -0.05 else "PASS"

    # Gate 6: Circuit Breaker Gate (new — India-specific)
    gates["circuit"] = "BLOCK" if silver_data.circuit_status == "lower" else "PASS"

    # Gate 7: Volume Validation Gate (new)
    gates["volume"] = "WARN" if silver_data.volume < silver_data.avg_volume * 0.5 else "PASS"

    # ── Verdict Logic ──────────────────────────────────────────────────────────

    if "BLOCK" in gates.values():
        verdict = "AVOID"
        reason  = "circuit_breaker"

    elif sum(1 for v in gates.values() if v == "FAIL") >= 2:
        verdict = "WAIT"

    elif sum(1 for v in gates.values() if v == "FAIL") == 1:
        verdict = "CAUTION"

    elif all(v == "PASS" for v in gates.values()):
        verdict = "BUY_SETUP"

    else:
        verdict = "MONITOR"

    return VerdictDraft(verdict=verdict, gates=gates)
```

### The Five Verdict States

| Verdict | Meaning |
|---|---|
| `BUY_SETUP` | All gates pass. Trade setup is populated. |
| `CAUTION` | Exactly one gate failing. User should watch that specific condition. |
| `MONITOR` | Mixed WARN signals, no hard FAILs. Worth tracking. |
| `WAIT` | Two or more gates failing. Entry is premature. |
| `AVOID` | Circuit breaker active, or fundamental violation so severe that entry is dangerous. |

`CAUTION` and `MONITOR` are the critical additions the original design lacks. A binary `WAIT/BUY` system is not actionable. A user seeing `CAUTION` knows exactly which one condition to watch — that is real information, not a wall of caveats.

### All Numeric Thresholds

All magic numbers live in `config/gate_thresholds.py`. None are hardcoded inline in gate logic.

```python
GATE_THRESHOLDS = {
    "death_cross_gap_pct":     0.5,     # minimum SMA gap % to confirm death cross
    "rsi_oversold":            25,      # below this = deeply oversold (WARN)
    "rsi_overbought":          75,      # above this = overbought (FAIL)
    "sector_rs_min":          -0.05,    # stock must not underperform sector by > 5%
    "volume_min_ratio":        0.5,     # volume must be > 50% of average
    "debt_equity_max":         1.5,     # long-term conservative threshold
    "roe_min":                 0.12,    # minimum ROE for long-term quality filter
    "risk_caps": {
        "conservative":        0.25,
        "moderate":            0.45,
        "aggressive":          0.65,
    }
}
```

---

## Stage 5 — The LangGraph State Object

This is the single source of truth passed between every node in the graph. All data computed in Stages 0–4 lives here before the LLM is invoked. All LLM output is written back into it after Stage 6.

### The Full State Schema

```python
AnalysisState:

  # ── Input ──────────────────────────────────────────────────────────────────
  ticker:           str
  user_profile:     UserProfile

  # ── Bronze ─────────────────────────────────────────────────────────────────
  bronze:           BronzePayload

  # ── Silver ─────────────────────────────────────────────────────────────────
  silver:           SilverMetrics

  # ── Gold ───────────────────────────────────────────────────────────────────
  gates:            Dict[str, GateResult]
  verdict_draft:    VerdictDraft
  confidence_score: float                   # computed in Stage 3, never LLM-generated

  # ── LLM Output (populated in Stage 6) ─────────────────────────────────────
  final_verdict:    str
  reasoning:        List[str]
  trade_setup:      Optional[TradeSetup]
  tutor_triggers:   List[str]

  # ── Metadata ───────────────────────────────────────────────────────────────
  pipeline_version: str
  computed_at:      datetime
```

### The Actual LangGraph Graph Structure

The original design treats LangGraph as a linear chain. That is wasteful and misses the core value of the library. The correct graph uses **conditional edges** and **parallel branches**:

```
[Ingest] → [Route]
               ↓
        [Fetch Data] → [Compute Indicators]
               ↓
        [Run Hard Gates]
               ↓
    ┌──────────┴──────────┐
    ↓                     ↓
[Fundamental Node]  [Technical Node]   ← parallel branches
    ↓                     ↓
    └──────────┬──────────┘
               ↓
         [Merge Results]
               ↓
         [LLM Synthesis]
               ↓
         [Output + Log]
```

**Conditional edge logic:**
- For `long_term` timeframe → both branches run in parallel
- For `intraday` timeframe → Fundamental Node is skipped entirely via a conditional edge
- For `swing` and `positional` → Technical Node runs first; Fundamental Node runs a lightweight check only

This is where LangGraph justifies its place in the stack. A simple function pipeline cannot do conditional parallel branching with shared state cleanly. LangGraph's `Send` API handles this natively.

---

## Stage 6 — The Single LLM Call

One call per analysis. Structured output enforced via a Pydantic model. The LLM synthesizes what the Python engine already determined — it does not reason about the math, it explains it.

### System Prompt

```
You are a financial analysis synthesizer. You receive pre-computed quantitative
verdicts from a deterministic Python engine and translate them into clear,
accurate, personalized explanations.

CRITICAL RULES:
- Never contradict the quantitative verdict. The math is ground truth.
- Never invent price targets, percentages, or dates not present in the input data.
- Never use phrases like "I think" or "possibly" about the verdict — it is determined.
- You MAY express uncertainty only about future price movement.
- Vocabulary level: {experience_level}
- User goal: {goal}
```

### User Prompt Template

```
Stock: {ticker} | Current Price: ₹{price}
Verdict: {verdict} | Confidence: {confidence_score}%

Gate Results:
{gate_results_formatted}

Key Metrics:
{silver_metrics_formatted}

Portfolio Context:
Current {asset_class} exposure: {current_exposure}% | Risk cap: {risk_cap}%
Available capital: ₹{capital}

Generate the analysis JSON. For tutor_triggers, flag ONLY terms that a
{experience_level} user would benefit from understanding more deeply.
```

### Pydantic Output Schema

```python
class AnalysisOutput(BaseModel):
    verdict:                Literal["BUY_SETUP", "CAUTION", "MONITOR", "WAIT", "AVOID"]
    confidence_score:       float             # passed through from Stage 3, not re-generated
    personalized_reasoning: List[str]         # 3-4 sentences max per item
    what_to_watch:          List[str]         # conditions that would change the verdict
    trade_setup:            Optional[TradeSetup]  # populated only for BUY_SETUP verdict
    risk_warning:           str               # mandatory — always present regardless of verdict
    tutor_triggers:         List[str]         # terms to highlight for the tutor system
```

### The `what_to_watch` Field

This field is the most important addition to the output schema that the original design lacks entirely.

For a `WAIT` verdict, telling the user *"this verdict changes to CAUTION if RSI drops below 30 and price holds above ₹140"* is infinitely more useful than just saying wait. It converts a passive verdict into an active monitoring checklist. The user knows exactly what to watch for — they do not need to come back and re-run the analysis blindly every day.

**Example `what_to_watch` output for a WAIT verdict on Ashok Leyland:**
```json
[
  "RSI drops below 30 AND price holds above ₹140 → verdict upgrades to CAUTION",
  "50-day SMA gap vs 200-day SMA widens beyond 2% → death cross confirmed, do not enter",
  "Mid-cap portfolio exposure drops below 40% → concentration gate clears"
]
```

### Prompt Versioning

All prompts are stored as `.jinja2` / `.txt` files in `backend/app/prompts/`. They are never hardcoded as Python strings. When prompt tuning is needed, you edit a text file — no Python diff noise, no logic changes, easy to version and A/B test.

---

## Stage 7 — Trade Setup

This stage only executes when `verdict == "BUY_SETUP"` — i.e., all hard gates have passed. All values are computed by Python. The LLM never generates any number in the trade setup.

### The TradeSetup Object

```python
class TradeSetup(BaseModel):
    entry_zone_low:          float    # price - (0.5 × ATR)
    entry_zone_high:         float    # price + (0.5 × ATR)
    stop_loss:               float    # price - (2 × ATR)
    target_1:                float    # price + (3 × ATR)   →  ~1:1.5 risk-reward
    target_2:                float    # price + (5 × ATR)   →  ~1:2.5 risk-reward
    suggested_position_size: float    # (capital × 0.02) / (price - stop_loss)
    risk_per_trade_inr:      float    # capital × 0.02
    risk_reward_ratio:       float    # (target_1 - entry) / (entry - stop_loss)
```

### Why This Must Never Touch the LLM

Position sizing via `(capital × risk%) / (entry − stop_loss)` is standard Kelly-adjacent risk management logic. It is pure arithmetic. Letting an LLM produce these numbers introduces two risks:

1. **Hallucination risk** — the model may invent a plausible-looking but mathematically wrong position size
2. **Liability risk** — fabricated financial numbers shown to real users making real capital decisions

A beginner seeing *"suggested position size: 47 shares | max risk: ₹2,400 on ₹1.2L capital"* is learning proper risk management by simply using the product. The math teaches them. That is only possible if the math is correct.

---

## Stage 8 — Logging to Supabase

Every analysis is persisted. This is the long-term moat of the product.

### The `analysis_logs` Table

```python
{
    "id":                 uuid,
    "user_id":            str,
    "ticker":             str,
    "verdict":            str,
    "confidence_score":   float,
    "gate_results":       jsonb,       # full gate breakdown
    "silver_metrics":     jsonb,       # price, RSI, SMAs, sector RS at time of analysis
    "user_profile_hash":  str,         # not PII — hash for grouping, not identification
    "computed_at":        timestamp,
    "pipeline_version":   str          # enables A/B testing between pipeline versions
}
```

### Why `pipeline_version` Is Non-Negotiable

When gate thresholds are tuned or the confidence formula is adjusted, you need to know which analyses were run under which version of the pipeline. Without this field, backtesting is polluted — you cannot tell whether a change in accuracy came from a better pipeline or from different market conditions during the test period.

### The Backtesting Loop

Over time, the `analysis_logs` table enables a backtesting script (`scripts/backtest.py`) that:

1. Queries all `BUY_SETUP` verdicts from 30 days ago
2. Fetches the stock's actual price 30 days later
3. Computes directional accuracy (did the price go up?)
4. Segments by pipeline version, timeframe, and risk profile

This is how the product moves from *"trust the system"* to *"the system has 67% directional accuracy over 6 months on positional calls for moderate-risk users."* That evidence is the difference between a tool and a product people pay for.

---

## Stage 9 — The Tutor System

The tutor is a parallel track — it does not block or delay the main analysis pipeline. It runs on-demand when the user interacts with the output.

### Three Tutor Modes

#### Mode 1 — Term Explainer (core feature)

User clicks a highlighted term (e.g., "Death Cross") → system fetches from pgvector corpus → LLM summarizes in context → returns to sidebar.

This is the original design. Keep it.

#### Mode 2 — Context-Aware Follow-up (new)

User types a free-form question: *"why does my portfolio concentration matter here?"*

The `/api/tutor` endpoint receives the **full `AnalysisState`** as context alongside the question. The LLM answers specifically about this stock and this user's portfolio — not generically. This is the difference between a glossary and an actual tutor.

#### Mode 3 — Scenario Explainer (new)

User asks: *"what would change this to a BUY?"*

The system pulls the `what_to_watch` field from the logged `AnalysisState` and explains each condition in language calibrated to the user's `experience_level`. No extra LLM reasoning is required — the conditions are already computed. The tutor just translates them.

### The Fixed RAG Pipeline

The original design embeds only the bare term. This produces weak retrieval when the term has multiple meanings across different trading contexts.

```python
# Wrong: bare term embedding
query = "Death Cross"

# Correct: contextualised embedding
query = f"{term} in the context of {timeframe} trading for {goal} investors"

# Retrieve top-3 chunks, not top-1
chunks = supabase.rpc("match_documents", {"query": embed(query), "k": 3})
```

### The Tutor LLM Prompt

```python
prompt = f"""
Using ONLY the following verified financial definitions, explain '{term}'
to a {experience_level} investor in the context of {ticker}'s current analysis.

Retrieved definitions:
{chunks}

If the retrieved content does not contain enough information to answer,
say: "I don't have a verified definition for this term yet."
Do NOT invent definitions.
"""
```

### The Fallback Rule

The *"I don't have a verified definition for this term yet"* fallback is not optional. Without it, the RAG system will hallucinate when the corpus does not cover a queried term — which defeats the entire purpose of using RAG over direct LLM generation. The hallucination-free guarantee the system makes to users only holds if this fallback is present and enforced.

---



*Document version: 1.0 | Last updated: June 2026*
