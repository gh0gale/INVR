# FinAI: Complete System Blueprint

> **The single source of truth.** Every algorithm, every schema, every file, every threshold, every API contract, and every planned feature is documented here. This project can be fully recreated from this document alone.

---

## Table of Contents

1. [Project Philosophy & Core Principle](#1-project-philosophy--core-principle)
2. [Tech Stack & Dependencies](#2-tech-stack--dependencies)
3. [Repository Structure](#3-repository-structure)
4. [Configuration & Environment](#4-configuration--environment)
5. [Database Schema (Supabase)](#5-database-schema-supabase)
6. [Pydantic Schemas & Data Contracts](#6-pydantic-schemas--data-contracts)
7. [The Pipeline Router (Stage 1)](#7-the-pipeline-router-stage-1)
8. [Bronze Layer — Data Fetching (Stage 2)](#8-bronze-layer--data-fetching-stage-2)
9. [Silver Layer — Indicator Computation (Stage 3)](#9-silver-layer--indicator-computation-stage-3)
10. [Gold Layer — The Decision Engine (Stage 4)](#10-gold-layer--the-decision-engine-stage-4)
11. [LangGraph Orchestrator & LLM Synthesis (Stage 5 & 6)](#11-langgraph-orchestrator--llm-synthesis-stage-5--6)
12. [Trade Setup Generation (Stage 7)](#12-trade-setup-generation-stage-7)
13. [Hybrid Ledger Logging (Stage 8)](#13-hybrid-ledger-logging-stage-8)
14. [The Tutor System (Stage 9)](#14-the-tutor-system-stage-9)
15. [Memory System](#15-memory-system)
16. [Caching Layer](#16-caching-layer)
17. [FastAPI Application & API Routes](#17-fastapi-application--api-routes)
18. [Authentication & Security](#18-authentication--security)
19. [Quantitative Engine Room (Stage 10)](#19-quantitative-engine-room-stage-10)
20. [CI/CD — GitHub Actions](#20-cicd--github-actions)
21. [Timeframe-Specific Data & Indicator Matrix](#21-timeframe-specific-data--indicator-matrix)
22. [End-to-End Request Lifecycle](#22-end-to-end-request-lifecycle)
23. [Testing](#23-testing)
24. [Implementation Tracker](#24-implementation-tracker)
25. [Known Issues & Audit Findings](#25-known-issues--audit-findings)
26. [Roadmap & Planned Features](#26-roadmap--planned-features)

---

## 1. Project Philosophy & Core Principle

Most AI financial tools hallucinate numbers or provide vague, non-actionable advice. FinAI solves this by strictly separating **Deterministic Math** from **Probabilistic Language**.

- **The Python engine computes the ground truth** — every verdict, confidence score, trade setup, and risk gate is determined by pure arithmetic.
- **The LLM only translates it** — it receives pre-computed results and converts them into personalized, human-readable explanations without inventing, modifying, or overriding any numbers.

The LLM never decides if a stock is a "Buy" or calculates a Stop Loss. All decisions, verdicts, and numeric calculations are done by the quantitative engine using strict **Hard Gates**.

### Foundational Data Source Hierarchy

1. **Primary:** Zerodha Kite Connect API (historical, live quotes, fundamentals) — *planned*.
2. **Secondary:** NSE/BSE direct feeds via `nsepython`.
3. **Current Default:** `yfinance` (free, no auth) with file-system-based TTL freshness validation.

### Deterministic Confidence

Confidence scores are strictly computed via weighted mathematical signal components (gate pass/fail ratio, gate severity weights), never LLM-generated.

---

## 2. Tech Stack & Dependencies

### Runtime

| Component | Technology | Version |
|---|---|---|
| Language | Python | 3.14+ |
| Backend Framework | FastAPI | ≥0.136.3 |
| ASGI Server | Uvicorn | ≥0.49.0 |
| Orchestration | LangGraph | ≥1.2.4 |
| LLM Chain Layer | LangChain Core | ≥1.4.6 |
| LLM Provider Binding | langchain-ollama | ≥1.1.0 |
| Local LLM Runtime | Ollama | `llama3.1` at `temperature=0.0` (analysis) / `0.3` (tutor) |
| Data Processing | Pandas | ≥3.0.3 |
| Numeric Computing | NumPy | (transitive via Pandas) |
| Validation | Pydantic | ≥2.13.4 |
| Settings Management | pydantic-settings | ≥2.14.1 |
| Database / Auth | Supabase (PostgreSQL + GoTrue Auth) | ≥2.31.0 |
| Market Data | yfinance | ≥1.4.1 |
| NSE Data | nsepython | ≥2.97 |
| Environment Variables | python-dotenv | ≥1.2.2 |
| Package Manager | uv | (lock file present) |
| CI/CD | GitHub Actions | `engine_room.yml` |

### Declared but Unused

| Package | Status |
|---|---|
| `redis>=8.0.0` | Declared in `pyproject.toml` but never imported. Placeholder for future cache migration. |

### Key Design Decisions

- **No external paid LLM API required** — runs fully local via Ollama. Production upgrade path to Anthropic Claude planned.
- **No Docker required for local dev** — file-based caching replaces Redis/Memcached.
- **Indian market focus** — all tickers appended with `.NS` suffix, NSE circuit breaker integration, INR currency throughout.

---

## 3. Repository Structure

```
INVR/
├── .git/
├── .github/
│   └── workflows/
│       └── engine_room.yml          # Scheduled CI: nightly grading + weekly drift analysis
├── .gitignore
├── audit_report.md                  # Full system audit
├── idea.md                          # Blueprint: Bronze/Silver metrics per timeframe
├── master_documentation.md          # THIS FILE
├── system_evaluation_prompt.md      # 9-phase audit prompt template
│
├── backend/
│   ├── .env                         # Secrets (gitignored)
│   ├── .env.example                 # Template for required env vars
│   ├── .local_cache/                # TTL-based file cache (gitignored)
│   ├── .venv/                       # Virtual environment (gitignored)
│   ├── main.py                      # FastAPI app entrypoint
│   ├── pyproject.toml               # Dependencies & project metadata
│   ├── uv.lock                      # Deterministic lock file
│   ├── requirements.txt             # Pip-compatible requirements
│   ├── test_pipeline.py             # End-to-end integration test (14 steps)
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── gate_thresholds.py       # Externalized numeric thresholds
│   │
│   ├── scripts/
│   │   ├── grade_ledger.py          # Midnight Grader: grades matured predictions against reality
│   │   ├── analyze_drift.py         # Statistical Drift Analyzer: detects threshold miscalibration
│   │   └── simulate_live_history.py # Time Machine: backfills 2y of graded production logs
│   │
│   └── app/
│       ├── __init__.py
│       ├── config.py                # Pydantic Settings (Supabase creds, market suffix)
│       ├── database.py              # Supabase client initialization (anon + admin)
│       ├── orchestrator.py          # Main LangGraph pipeline (3 nodes)
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deps.py              # Auth dependency (JWT verification)
│       │   └── routes/
│       │       ├── profile.py       # POST /api/v1/profiles/
│       │       ├── analytics.py     # POST /api/v1/analytics/process
│       │       └── tutor.py         # POST /api/v1/tutor/chat/stream
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── api.py               # PipelineRequest, PipelineResponse
│       │   ├── bronze.py            # BronzePayload
│       │   ├── silver.py            # SilverMetrics
│       │   ├── gold.py              # VerdictDraft, TradeSetup
│       │   ├── llm.py               # AnalysisOutput
│       │   ├── profile.py           # UserProfileRequest, UserProfileResponse
│       │   ├── state.py             # AnalysisState, UserProfile (TypedDicts)
│       │   └── tutor.py             # TutorState, ChatRequest
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── bronze_service.py    # Data fetching orchestrator
│       │   ├── silver_service.py    # Indicator computation engine
│       │   ├── gold_service.py      # Hard gate evaluation + verdict resolution
│       │   ├── cache_service.py     # File-based TTL cache
│       │   ├── ledger_service.py    # Supabase prediction logging
│       │   ├── memory_service.py    # Chat memory persistence + eviction
│       │   └── profile_service.py   # User profile creation + storage
│       │
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── router.py            # Timeframe → data manifest config
│       │   ├── tutor_graph.py       # Tutor LangGraph (semantic router → generation)
│       │   └── memory_graph.py      # Background memory extraction (LLM-based)
│       │
│       ├── integrations/
│       │   ├── __init__.py
│       │   └── market_data.py       # yfinance + nsepython wrappers
│       │
│       └── tools/
│           ├── __init__.py
│           └── market_data.py       # News fetching tool for tutor
│
└── frontend/                        # EMPTY — not yet implemented
```

---

## 4. Configuration & Environment

### Environment Variables (`.env`)

| Variable | Purpose | Required |
|---|---|---|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Public anon key for JWT verification | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Admin key (bypasses RLS) | Yes |
| `MARKET_SUFFIX` | Ticker suffix for exchange (default: `.NS` for NSE) | No |

**File:** `backend/app/config.py`

```python
class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    MARKET_SUFFIX: str = ".NS"
```

### Gate Thresholds (`config/gate_thresholds.py`)

All hard numeric thresholds used in the Gold Layer are externalized here for easy tuning:

| Constant | Value | Purpose |
|---|---|---|
| `death_cross_gap_pct` | `0.5` | Minimum SMA gap % to confirm a deep death cross |
| `rsi_oversold` | `30.0` | Below this = deeply oversold (WARN) |
| `rsi_overbought` | `70.0` | Above this = overbought (FAIL) |
| `sector_rs_min` | `-0.05` | Stock must not underperform sector by >5% |
| `volume_min_ratio` | `0.5` | Volume must be >50% of 20-period average |
| `debt_equity_max` | `1.5` | Long-term conservative D/E threshold |
| `roe_min` | `15.0` | Minimum ROE for positional/long-term quality |
| `revenue_cagr_min` | `0.10` | Target 10% revenue CAGR |
| `eps_cagr_min` | `0.12` | Target 12% EPS CAGR |
| `max_pe` | `50.0` | Hard valuation ceiling for PE ratio |

---

## 5. Database Schema (Supabase)

### Tables

#### `user_profiles`
Stores validated user profiles. Upserted via admin client (bypasses RLS).

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` (PK) | Supabase auth user ID |
| `experience` | `text` | `beginner` / `intermediate` / `advanced` |
| `goal` | `text` | `wealth_growth` / `dividend_income` / `capital_preservation` |
| `timeframe` | `text` | `intraday` / `swing` / `positional` / `long_term` |
| `risk` | `text` | `conservative` / `moderate` / `aggressive` |
| `portfolio` | `jsonb` | Asset class allocations `{"equities": 0.6, "debt": 0.3, ...}` |
| `capital` | `float8` | Available capital in INR |
| `profile_version_hash` | `text` | MD5 hash of serialized profile for change detection |
| `contradictions_flagged` | `jsonb` | Array of detected contradictions |
| `semantic_profile` | `jsonb` | Accumulated learning state from memory system |

#### `algorithmic_ledger`
Stores every prediction for backtesting and grading. One row per ticker × timeframe × date × pipeline_version.

| Column | Type | Description |
|---|---|---|
| `log_id` | `uuid` (PK) | Auto-generated |
| `ticker` | `text` | e.g., `RELIANCE.NS` |
| `timeframe` | `text` | e.g., `swing` |
| `date` | `date` | UTC date of prediction |
| `pipeline_version` | `text` | e.g., `v1.0.0` |
| `silver_state` | `jsonb` | Full SilverMetrics snapshot |
| `gold_verdict` | `jsonb` | Full VerdictDraft snapshot |
| `actual_outcome` | `text` | `PENDING` / `WIN` / `LOSS` / `DRAW` — graded by `grade_ledger.py` |
| `max_favorable_excursion` | `float8` | Highest price reached in the evaluation window |
| `max_adverse_excursion` | `float8` | Lowest price reached in the evaluation window |
| `created_at` | `timestamptz` | Auto-set |

#### `prediction_interactions`
Traces which user sessions viewed which predictions.

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` (PK) | Auto-generated |
| `log_id` | `uuid` (FK → `algorithmic_ledger`) | Which prediction was viewed |
| `session_id` | `text` | Chat session ID |
| `action_taken` | `text` | `viewed` / (future: `acted_on`, `dismissed`) |
| `created_at` | `timestamptz` | Auto-set |

#### `chat_sessions`
Persists tutor conversation state for each session.

| Column | Type | Description |
|---|---|---|
| `session_id` | `text` (PK) | Client-generated UUID |
| `user_id` | `uuid` (FK → `user_profiles`) | Owner |
| `working_memory` | `jsonb` | Array of `{role, content}` message pairs (sliding window) |
| `episodic_memory` | `jsonb` | Array of summarized conversation chunks |
| `created_at` | `timestamptz` | Auto-set |

#### `threshold_insights`
Stores automated suggestions from the Drift Analyzer for threshold recalibration.

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` (PK) | Auto-generated |
| `metric` | `text` | Gate threshold key (e.g., `rsi_overbought`, `volume_min_ratio`) |
| `timeframe` | `text` | Applicable timeframe |
| `current_threshold` | `float8` | Current configured threshold value |
| `suggested_threshold` | `float8` | Data-driven suggested threshold value |
| `confidence_score` | `float8` | Statistical confidence of the suggestion |
| `reasoning` | `text` | Human-readable explanation of the drift detection |
| `created_at` | `timestamptz` | Auto-set |

---

## 6. Pydantic Schemas & Data Contracts

### User Profile Input (`schemas/profile.py`)

```python
class UserProfileRequest(BaseModel):
    experience: Literal["beginner", "intermediate", "advanced"]
    goal: Literal["wealth_growth", "dividend_income", "capital_preservation"]
    timeframe: Literal["intraday", "swing", "positional", "long_term"]
    risk: Literal["conservative", "moderate", "aggressive"]
    portfolio: Dict[str, float]    # Must sum to 1.0 ± 0.01
    capital: float                 # INR, must be ≥ 0
```

**Validators:**
1. **Portfolio weight normalization** — rejects if `sum(weights)` not in `[0.99, 1.01]`.
2. **Contradiction detection** — flags (but doesn't reject) contradictions like `capital_preservation` + `aggressive` risk.

**Response** extends request with:
- `profile_version_hash` — MD5 of sorted JSON for immutable change detection.
- `contradictions_flagged` — list of detected contradictions.

### BronzePayload (`schemas/bronze.py`)

```python
class BronzePayload(BaseModel):
    ticker: str
    timeframe: str
    circuit_status: Optional[str] = "none"         # "none" | "upper" | "lower" | "unknown"
    price_history: pd.DataFrame                     # OHLCV DataFrame
    sector_history: Optional[pd.DataFrame] = None   # Sector index DataFrame
    fundamentals: Optional[Dict[str, Any]] = None   # Polymorphic financials dict
    institutional_activity: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
```

### SilverMetrics (`schemas/silver.py`)

A union schema that accommodates all timeframes. Fields are `Optional` — only the ones relevant to the current timeframe are populated.

| Field Group | Fields | Used By |
|---|---|---|
| **Identifiers** | `ticker`, `timeframe`, `current_price`, `current_volume` | All |
| **Macro Filter** | `market_regime` | Swing, Positional, Long-Term |
| **Core Technical** | `sma_20`, `sma_50`, `sma_200`, `rsi_14`, `atr_14`, `volume_avg_20`, `stock_vs_sector_rs`, `sma_gap_pct` | Varies by timeframe |
| **Swing Fundamentals** | `pe_vs_sector_avg`, `trailing_pe`, `debt_flag`, `institutional_bias` | Swing |
| **Positional Fundamentals** | `revenue_cagr_3y`, `profit_cagr_3y`, `opm_trend`, `roe_vs_cost_of_capital`, `valuation_comfort` | Positional |
| **Long-Term Compounder** | `revenue_cagr_5y`, `eps_cagr_5y`, `fcf_conversion`, `roe_consistency_5y`, `debt_trajectory`, `pe_band_vs_growth` | Long-Term |
| **Schema-Only (Unpopulated)** | `cfo_vs_net_profit`, `promoter_holding_trend`, `book_value_growth`, `promoter_conviction_trend`, `dividend_consistency` | Reserved for v2 |

### VerdictDraft (`schemas/gold.py`)

```python
class VerdictDraft(BaseModel):
    ticker: str
    timeframe: str
    verdict: Literal["STRONG BUY", "BUY ON DIP", "MONITOR", "CAUTION", "AVOID"]
    confidence_score: float        # Range: 50.0 – 95.0
    gate_results: Dict[str, str]   # e.g., {"trend": "PASS", "rsi": "WARN"}
    what_to_watch: List[str]       # Actionable monitoring conditions
    trade_setup: Optional[TradeSetup] = None
    primary_reason: str
```

### TradeSetup (`schemas/gold.py`)

```python
class TradeSetup(BaseModel):
    entry_zone_low: float
    entry_zone_high: float
    stop_loss: float
    target_1: float
    target_2: float
    suggested_position_size: float     # Integer shares
    risk_per_trade_inr: float          # Capital × 2%
    risk_reward_ratio: float
```

### AnalysisOutput (`schemas/llm.py`)

The schema the LLM is constrained to via `with_structured_output()`:

```python
class AnalysisOutput(BaseModel):
    personalized_reasoning: List[str]  # 3-4 brief sentences
    what_to_watch: List[str]           # Actionable monitoring conditions
    risk_warning: str                  # 1-sentence mandatory warning
    tutor_triggers: List[str]          # Financial jargon for tutor highlighting
```

**Post-LLM injection:** `verdict`, `confidence_score`, and `regulatory_disclaimer` are injected into the response dict *after* LLM inference to prevent hallucinated overrides.

### AnalysisState (`schemas/state.py`)

The LangGraph state object — a `TypedDict` (not Pydantic) serving as the single source of truth across all pipeline nodes:

```python
class AnalysisState(TypedDict):
    ticker: str
    timeframe: str
    user_profile: UserProfile          # {risk_tolerance, experience_level, goal, available_capital}
    bronze: Optional[BronzePayload]
    silver: Optional[SilverMetrics]
    gold: Optional[VerdictDraft]
    llm_output: Optional[Dict[str, Any]]
    errors: List[str]
```

### API Request/Response (`schemas/api.py`)

```python
class PipelineRequest(BaseModel):
    ticker: str                          # e.g., "RELIANCE"
    timeframe: str                       # "swing" | "positional" | "long_term"
    user_profile: Optional[APIUserProfile]   # Defaults provided
    session_id: Optional[str]            # For ledger interaction tracing

class PipelineResponse(BaseModel):
    success: bool
    ticker: str
    timeframe: str
    verdict: Optional[str]
    llm_analysis: Optional[Dict[str, Any]]
    errors: Optional[list[str]]
```

### Tutor Schemas (`schemas/tutor.py`)

```python
class TutorState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # Auto-appending
    analysis_state: Dict[str, Any]       # Phase 2 JSON tear sheet
    user_profile: Dict[str, Any]
    routed_mode: str                     # "definition" | "portfolio" | "scenario" | "news"
    tool_data: Optional[str]             # Scraped data from tools

class ChatRequest(BaseModel):
    message: str
    session_id: str
    analysis_context: Dict[str, Any]     # Phase 2 output
    user_profile: Dict[str, Any]
```

---

## 7. The Pipeline Router (Stage 1)

**File:** `backend/app/pipeline/router.py`

Pure Python deterministic routing. Maps a `timeframe` string to a **pipeline manifest** that controls which data sources are fetched and which indicators are computed.

### Pipeline Configuration Matrix

| Timeframe | Period | Interval | Sector | Fundamentals | Circuits | Institutional |
|---|---|---|---|---|---|---|
| `intraday` | `5d` | `5m` | ❌ | ❌ | ✅ | ❌ |
| `swing` | `6mo` | `1d` | ✅ | ✅ (lightweight) | ✅ | ✅ |
| `positional` | `1y` | `1d` | ✅ | ✅ (full) | ✅ | ❌ |
| `long_term` | `5y` | `1wk` | ✅ | ✅ (full) | ❌ | ❌ |

```python
def get_pipeline_manifest(timeframe: str) -> Dict[str, Any]:
    if timeframe not in PIPELINE_CONFIG:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return PIPELINE_CONFIG[timeframe]
```

---

## 8. Bronze Layer — Data Fetching (Stage 2)

**File:** `backend/app/services/bronze_service.py`

Orchestrates async concurrent data fetching from multiple sources and assembles a `BronzePayload`.

### Execution Flow

1. **Ticker normalization** — appends `MARKET_SUFFIX` (`.NS`) if not present.
2. **Price data fetch** — `yfinance` OHLCV with cache-first strategy.
3. **Concurrent optional fetches** — fundamentals, circuit status, gathered via `asyncio.gather()`.
4. **Sector data fetch** — requires fundamentals first (to determine sector), then fetches sector index.
5. **Institutional activity** — currently returns hardcoded mock data (`fii_net_activity: 125.5`, `dii_net_activity: -40.2`).

### Cache TTLs

| Data Type | Timeframe | TTL |
|---|---|---|
| Price data | Intraday | 5 minutes (300s) |
| Price data | Daily/Weekly | 12 hours (43,200s) |
| Fundamentals | All | 24 hours (86,400s) |

### Sector Index Mapping (Hardcoded)

```python
SECTOR_INDEX_MAP = {
    "Auto": "^CNXAUTO",
    "IT": "^CNXIT",
    "Bank": "^NSEBANK",
    "Financial Services": "^CNXFIN",
    "FMCG": "^CNXFMCG"
}
```

> **TODO:** Move to Supabase lookup table in production.

### Market Data Integration (`integrations/market_data.py`)

#### `fetch_yfinance_history(ticker, period, interval)`
- Primary fetch via `stock.history(period, interval)`.
- Fallback: exact date math using a `days_map` if yfinance returns empty.
- Raises `ValueError` if both attempts return empty.

#### `fetch_nse_circuit_status(ticker, current_price)`
- Uses `nsepython.nse_quote()` to get `priceInfo.upperCP` / `lowerCP`.
- Returns `"upper"` if price ≥ 99.5% of upper limit, `"lower"` if price ≤ 100.5% of lower limit, else `"none"`.
- Returns `"unknown"` on any exception (failsafe for NSE blocking).

#### `fetch_yfinance_fundamentals(ticker)`
Fetches multi-year financial statements and assembles a polymorphic dict:

| Data Source | Fields Extracted |
|---|---|
| `stock.info` | sector, trailingPE, debtToEquity, returnOnEquity, dividendYield, sharesOutstanding |
| `stock.financials` | Total Revenue (3y/5y), Net Income (3y/5y), EPS (computed from Net Income / shares) |
| `stock.cashflow` | Operating Cash Flow (3y/5y), Capital Expenditure (3y/5y, abs-converted) |
| `stock.balance_sheet` | Total Debt (5y) |

**Nested `ratios` sub-dictionary** is now populated:
```python
"ratios": {
    "pe": info.get("trailingPE", 0),
    "roe_5y": [],          # Empty placeholder (5Y ROE history unavailable via yfinance free tier)
    "debt_to_equity_trend": []  # Empty placeholder
}
```

**Known mock data:** `sector_pe_median` hardcoded to `25.0`, `book_value_per_share` hardcoded to `[100, 110, 125, 140, 160]`.

---

## 9. Silver Layer — Indicator Computation (Stage 3)

**File:** `backend/app/services/silver_service.py`

All computations are pure, synchronous, vectorized Pandas operations. Offloaded to a background thread via `asyncio.to_thread()` in the orchestrator.

### CAGR Calculation

```python
def calculate_cagr(history_list: list) -> Optional[float]:
    # (end_val / start_val) ** (1 / periods) - 1
    # Returns None if: empty list, < 2 elements, start_val ≤ 0, end_val ≤ 0
```

### Core Technical Indicators

| Indicator | Formula | Data Requirement | Timeframes |
|---|---|---|---|
| **SMA-20** | `Close.rolling(20).mean()` | ≥ 20 rows | All |
| **SMA-50** | `Close.rolling(50).mean()` | ≥ 50 rows | All |
| **SMA-200** | `Close.rolling(200).mean()` | ≥ 200 rows | Positional, Long-Term |
| **RSI-14** | Wilder's EWMA: `alpha=1/14`, `100 - 100/(1+RS)`, epsilon `1e-9` | ≥ 15 rows | All |
| **ATR-14** | `max(H-L, |H-Cprev|, |L-Cprev|)` → EWMA `alpha=1/14` | ≥ 15 rows | All |
| **Volume Avg 20** | `Volume.rolling(20).mean()` | ≥ 20 rows | All |
| **SMA Gap %** | `(SMA50 - SMA200) / SMA200 × 100` | SMA50 + SMA200 | Positional, Long-Term |

### Relative Strength & Macro Regime

| Metric | Lookback | Formula | Timeframes |
|---|---|---|---|
| **Stock vs Sector RS** | 20 (swing), 50 (positional), 12 (long-term) | `stock_return - sector_return` over lookback period | Swing, Positional, Long-Term |
| **Market Regime** | 200 rows of sector history | `"bearish"` if index < SMA50 AND index < SMA200; `"bullish"` if index > both; else `"neutral"` | Swing, Positional, Long-Term |

### Timeframe-Specific Fundamental Metrics

#### Swing
| Metric | Source | Logic |
|---|---|---|
| `pe_vs_sector_avg` | `trailingPE - sector_pe_median` | Valuation relative to sector |
| `debt_flag` | `de > (TH["debt_equity_max"] * 100)` OR `(0 < de < 10 AND de > TH["debt_equity_max"])` | Dual-check: handles both percentage and ratio format from yfinance |
| `institutional_bias` | `fii_net + dii_net` | `>50` → "buyer", `<-50` → "seller", else "neutral" |

#### Positional
| Metric | Source | Logic |
|---|---|---|
| `revenue_cagr_3y` | `calculate_cagr(revenue_3y)` × 100, fallback to `revenueGrowth` | % CAGR |
| `profit_cagr_3y` | `calculate_cagr(net_profit_3y)` × 100, fallback to `earningsGrowth` | % CAGR |
| `opm_trend` | `opm_trend[]` from fundamentals | `"expanding"` / `"contracting"` / `"stable"` via monotonicity and V-shape checks |
| `roe_vs_cost_of_capital` | `returnOnEquity > roe_min (15.0)` | Boolean |
| `valuation_comfort` | `(pe - sector_pe) / sector_pe × 100` | % premium/discount |

#### Long-Term
| Metric | Source | Logic |
|---|---|---|
| `revenue_cagr_5y` | `calculate_cagr(income_statement_5y.revenue)` × 100 | % CAGR |
| `eps_cagr_5y` | `calculate_cagr(income_statement_5y.eps)` × 100 | % CAGR |
| `fcf_conversion` | `Σ(CFO - Capex) / Σ(Net Profit)` over 5y | Ratio (healthy > 0.6) |
| `roe_consistency_5y` | `min(roe_5y[]) > 18.0` → `"consistent_moat"`, fallback to single ROE check | `"consistent_moat"` / `"average"` / `"volatile"` |
| `debt_trajectory` | `debt_5y[-1] < debt_5y[0]` | `"deleveraging"` / `"leveraging"` / `"stable"` |
| `pe_band_vs_growth` | `PE / eps_cagr_5y` | PEG-like ratio |

---

## 10. Gold Layer — The Decision Engine (Stage 4)

**File:** `backend/app/services/gold_service.py`

Evaluates `SilverMetrics` against hard thresholds and user constraints. Produces a **5-state verdict** with a weighted confidence score and optional trade setup.

### Gate System

Each gate evaluates to one of three states: `PASS`, `WARN`, or `FAIL`. Some can evaluate to `BLOCK`.

#### Universal Gates (All Timeframes)

| Gate | Logic | States |
|---|---|---|
| `circuit` | `lower` → BLOCK, `upper` → WARN, else PASS | BLOCK / WARN / PASS |
| `volume` | `current_volume < volume_avg_20 × 0.5` → WARN | WARN / PASS |

#### Intraday Gates

| Gate | Logic |
|---|---|
| `micro_trend` | `price > sma_20` → PASS, else FAIL |
| `rsi` | `> 70` → FAIL, `< 30` → WARN, else PASS |
| `volume_spike` | `volume < avg × 1.5` → WARN, else PASS |

#### Swing Gates

| Gate | Logic |
|---|---|
| `trend` | `price > sma_20` → PASS, else FAIL |
| `sector` | `stock_vs_sector_rs < -0.05` → FAIL, else PASS |
| `rsi` | `> 70` → FAIL, `< 30` → WARN, else PASS |

#### Positional Gates

| Gate | Logic |
|---|---|
| `death_cross` | `sma_50 < sma_200` AND `abs(sma_gap_pct) > 0.5` → FAIL; small gap → WARN; else PASS |
| `revenue_growth` | `revenue_cagr_3y < 10%` → WARN, else PASS |

#### Long-Term Gates

| Gate | Logic |
|---|---|
| `secular_trend` | `price < sma_200` → WARN (then immediately overwritten to PASS — **known bug**) |
| `valuation` | `trailing_pe > 50` → FAIL, else PASS |
| `fcf_quality` | `fcf_conversion > 0.6` → PASS, else WARN |
| `eps_growth` | `eps_cagr_5y < 12%` → FAIL, else PASS |

### Verdict Resolution Logic

```
if any gate == "BLOCK"       → AVOID
elif failed_count >= 2       → CAUTION
elif failed_count == 1       → MONITOR
elif all gates PASS          → STRONG BUY
else                         → BUY ON DIP
```

### Dynamic Parameter-Based Primary Reason

The `primary_reason` field is dynamically generated based on gate results:
- **AVOID:** "Execution blocked due to Circuit Limits."
- **CAUTION:** Lists the specific failing/warning gates by human-readable name.
- **MONITOR:** Identifies the single lagging gate parameter.
- **STRONG BUY:** Lists the top 3 passing gates as strengths.
- **BUY ON DIP:** "Mixed technical signals, but supported by overall structural floors."

### Post-Verdict Overrides (Applied Sequentially)

1. **Institutional Volume Confirmation Override:**
   If `STRONG BUY` but `volume_ratio < 1.5x` → downgrade to `MONITOR`.

2. **Dynamic Buy Zone (Dip Support) Filter:**
   If `BUY ON DIP` but price is NOT within 3% of SMA-50 or SMA-200 → downgrade to `CAUTION` ("falling knife").

3. **Top-Down Macro Override (Final Authority):**
   If `market_regime == "bearish"` AND verdict is `STRONG BUY` or `BUY ON DIP` → downgrade to `CAUTION`.

### Weighted Confidence Score

Not all gates are equally important. Each gate has a severity weight:

| Gate | Weight |
|---|---|
| `circuit`, `death_cross` | 3.0 |
| `secular_trend`, `eps_growth`, `fcf_quality`, `valuation` | 2.0 |
| `volume`, `volume_spike`, `trend`, `sector` | 1.5 |
| `micro_trend`, `rsi`, `revenue_growth` | 1.0 |

**Formula:** `confidence = 50.0 + (passed_weight / total_weight) × 45.0`

**Range:** 50.0 (all fail) to 95.0 (all pass).

### Human-Readable Gate Names

Backend keys are mapped to display names for the LLM and user output:

```python
GATE_NAMES = {
    "circuit": "Circuit Limits",
    "volume": "Institutional Volume",
    "micro_trend": "Intraday Trend (100-min)",
    "rsi": "Momentum (RSI)",
    "volume_spike": "Intraday Volume Surge",
    "trend": "Short-Term Trend (20 DMA)",
    "sector": "Sector Relative Strength",
    "death_cross": "Moving Average Alignment (50/200 DMA)",
    "revenue_growth": "Revenue Compounding",
    "secular_trend": "Long-Term Trend (200 DMA)",
    "fcf_quality": "Free Cash Flow Conversion",
    "eps_growth": "EPS Compounding",
    "valuation": "Valuation Comfort Ceiling"
}
```

---

## 11. LangGraph Orchestrator & LLM Synthesis (Stage 5 & 6)

**File:** `backend/app/orchestrator.py`

### Main Analysis Graph

```
[fetch_data] → [quant_engine] → [llm_synthesizer] → END
```

Three nodes in a linear chain. No conditional edges. Error propagation is handled by checking `state.get("errors")` at the start of each node and returning early if errors exist.

#### Node 1: `fetch_data_node`
- Calls `build_bronze_payload(ticker, timeframe)`.
- Returns `{"bronze": bronze}` or `{"errors": [...]}`.

#### Node 2: `quant_engine_node`
- Offloads synchronous Pandas math to background threads via `asyncio.to_thread()`.
- Calls `compute_silver_metrics(bronze)` → `evaluate_hard_gates(silver, circuit_status, capital)`.
- Returns `{"silver": silver, "gold": gold}`.

#### Node 3: `llm_synthesizer_node`
- Initializes `ChatOllama(model="llama3.1", temperature=0.0)`.
- Uses `with_structured_output(AnalysisOutput)` for schema-constrained generation.
- **Prompt injection mitigation:** Sanitizes `silver_metrics` and `what_to_watch` by escaping `<` and `>` characters.
- **Post-LLM injection:** Forces `verdict`, `confidence_score`, and `regulatory_disclaimer` from the Gold layer output.
- **Fallback:** If LLM is offline/errors, returns a deterministic-only response with `"LLM_OFFLINE"` tutor trigger.

### LLM System Prompt Structure

The system prompt enforces:
1. No emoji output.
2. Every claim backed by exact numbers from the metrics.
3. `tutor_triggers` must be 2-4 single jargon words only.
4. Output structured in three sections:
   - **Investment Thesis & Profile Alignment** — 2 sentences on trajectory match, 2 on risk fit.
   - **Quantitative Scorecard** — 3 metrics with Value → PASS/FAIL/WATCH → explanation.
   - **Overall Verdict Rationale** — 4-5 sentence synthesis paragraph.

### Regulatory Disclaimer (Injected Post-LLM)

```
"This analysis is generated by an AI for educational purposes only.
It does not constitute financial advice.
Please consult a SEBI-registered investment advisor."
```

---

## 12. Trade Setup Generation (Stage 7)

Computed inside the Gold Layer (`gold_service.py`) when:
- Verdict = `STRONG BUY`
- Timeframe ∈ `{intraday, swing, positional}`
- `atr_14` is available

### Formulas

| Component | Intraday | Swing / Positional |
|---|---|---|
| **Entry Zone** | `price ± 0.5 × ATR` | `price ± 0.5 × ATR` |
| **Stop Loss** | `price - 1.5 × ATR` | `price - 2.0 × ATR` |
| **Target 1** | `price + 2.5 × ATR` | `price + 3.0 × ATR` |
| **Target 2** | `price + 4.0 × ATR` | `price + 5.0 × ATR` |
| **Position Size** | `(capital × 2%) / (price - stop_loss)` | Same |
| **Risk/Reward** | `(T1 - price) / risk_distance` | Same |

- **Risk per trade** is capped at 2% of available capital.
- `risk_distance` has a floor of ₹0.01 to prevent division by zero.

---

## 13. Hybrid Ledger Logging (Stage 8)

**File:** `backend/app/services/ledger_service.py`

Runs as a FastAPI `BackgroundTask` (fire-and-forget) after the analytics response is returned.

### Logic

1. **De-duplication check:** Queries `algorithmic_ledger` for an existing row matching `ticker + timeframe + today's date + pipeline_version`. If found, reuses that `log_id`.
2. **Write if new:** Inserts full `silver_state` (JSONB) and `gold_verdict` (JSONB) alongside metadata.
3. **Interaction trace:** Always writes a `prediction_interactions` row linking `log_id` ↔ `session_id` with `action_taken: "viewed"`.

**Pipeline Version:** `v1.0.0` — must be incremented whenever gate thresholds change.

**Note:** `ledger_service.py` creates its own Supabase client instance using `os.getenv()` + `create_client()` rather than importing from `database.py`. This is intentional for background task isolation but diverges from the centralized client pattern.

---

## 14. The Tutor System (Stage 9)

**File:** `backend/app/pipeline/tutor_graph.py`

A separate LangGraph pipeline for context-aware financial education.

### Tutor Graph Structure

```
START → [router] → (conditional edge) → [news_tool] → [generate] → END
                                       → [generate] → END
```

### Node 1: `semantic_router_node`
- Uses `ChatOllama(model="llama3.1", temperature=0.0)` with structured output to classify user intent.
- Classification schema: `RouteDecision(mode: Literal["definition", "portfolio", "scenario", "news"])`.
- **Routing rules (in system prompt):**
  - `"definition"` — what a term/acronym/metric means.
  - `"portfolio"` — personal risk, goals, or capital questions.
  - `"scenario"` — what to do next, buy/sell triggers, future conditions.
  - `"news"` — recent events or updates.

### Node 2: `news_tool_node` (Conditional)
- Only reached if `routed_mode == "news"`.
- Fetches top 3 headlines from `yfinance` (`stock.news[:3]`).
- Stores result in `state["tool_data"]`.

### Node 3: `generation_node`
- Uses `ChatOllama(model="llama3.1", temperature=0.3)`.
- System instruction includes:
  - Full analysis state (truncated to 2000 chars for context window safety).
  - User profile (experience level, goal).
  - Mode-specific instructions:
    - **definition:** Clear explanation with numeric example, not overall verdict.
    - **portfolio:** Evaluate against existing allocations and goals.
    - **scenario:** Break down `what_to_watch` triggers with mathematical mechanics.
    - **news:** Synthesize recent headlines with analysis state.
- **Critical directives:** Quote-first (anchor to exact numbers), analogy-mapping (match experience level), graceful fallback (define terms even if metric not in current analysis).
- Chat history limited to last 10 messages.
- Passes `config` to `.ainvoke()` for streaming support.

### News Tool (`tools/market_data.py`)

```python
async def fetch_stock_news(ticker: str) -> str:
    # Fetches top 3 headlines from yfinance
    # Returns formatted string: "- Headline (Publisher)"
    # Returns "No recent news found" or error message on failure
```

---

## 15. Memory System

### Session Memory (`services/memory_service.py`)

Manages chat persistence with a chunked eviction strategy. Uses the centralized `supabase_admin` client from `database.py`.

**Flow:**
1. **Fetch or create** session from `chat_sessions` table.
2. **Append** new `{role: "human/ai", content}` pairs to `working_memory`.
3. **Chunked Eviction** triggers when `len(working_memory) >= 16` OR `topic_changed`:
   - Extracts oldest 10 messages into a text chunk.
   - Runs LLM-based extraction to produce:
     - `episodic_summary` — 2-sentence dense summary.
     - `new_learned_concepts` — financial terms the user demonstrated understanding of.
     - `portfolio_updates` — explicit portfolio/risk changes mentioned.
   - Patches `user_profiles.semantic_profile` with new concepts.
   - Moves summary to `episodic_memory`, drops processed messages from `working_memory`.
4. **Standard save** if watermark not reached — just updates `working_memory`.

### Memory Extraction Graph (`pipeline/memory_graph.py`)

```python
class MemoryUpdate(BaseModel):
    episodic_summary: str              # 2-sentence chunk summary
    new_learned_concepts: List[str]    # Newly grasped jargon (e.g., ["CAGR", "RSI"])
    portfolio_updates: Optional[str]   # Explicit holding/capital/risk changes
```

Uses `ChatOllama(model="llama3.1", temperature=0.0)` for strict extraction against the user's current semantic profile.

---

## 16. Caching Layer

**File:** `backend/app/services/cache_service.py`

File-based caching using JSON serialization. Designed as a local-dev replacement for Redis.

### Implementation

- **Storage:** `backend/.local_cache/` directory.
- **Key format:** `type:ticker:period:interval` → sanitized to valid filename (`:` → `_`, `^` removed).
- **Expiry:** TTL-based using filesystem `mtime`. Checked on read.
- **I/O:** All filesystem operations wrapped in `asyncio.to_thread()` to avoid blocking the event loop.

### API

| Function | Purpose |
|---|---|
| `get_cached_dataframe(key, ttl)` | Read cached DataFrame (JSON orient="index") |
| `set_cached_dataframe(key, df, ttl)` | Write DataFrame to cache |
| `get_cached_dict(key, ttl)` | Read cached dict (JSON) |
| `set_cached_dict(key, data, ttl)` | Write dict to cache |

> **TODO:** Migrate to Redis in production.

---

## 17. FastAPI Application & API Routes

**File:** `backend/main.py`

```python
app = FastAPI(title="Algorithmic Portfolio Analyzer Engine", version="1.0.0")

app.include_router(profile.router,   prefix="/api/v1/profiles",  tags=["Phase 0: Ingestion"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Phase 2: Quant Engine"])
app.include_router(tutor.router,     prefix="/api/v1/tutor")
```

### Endpoints

#### `GET /health`
Returns system diagnostic status.

```json
{
    "status": "healthy",
    "cache_writable": true,
    "database_connected": true,
    "system": "FinAI Orchestrator"
}
```

#### `POST /api/v1/profiles/`
**Auth:** Required (JWT Bearer token via `Depends(get_current_user_id)`).

Creates or updates a user profile. Runs Pydantic validation (portfolio weights, contradiction detection), generates MD5 version hash, upserts to `user_profiles` table via admin client.

**Request:** `UserProfileRequest`
**Response:** `UserProfileResponse` (201 Created)

#### `POST /api/v1/analytics/process`
**Auth:** None currently (noted as a security issue).

Triggers the full Bronze → Silver → Gold → LLM pipeline.

1. Builds `AnalysisState` from `PipelineRequest`.
2. Invokes `pipeline_graph.ainvoke()` with `recursion_limit=10`.
3. On success, fires background `log_prediction_to_ledger` task.
4. Returns `PipelineResponse`.

**Request:** `PipelineRequest`
**Response:** `PipelineResponse`

#### `POST /api/v1/tutor/chat/stream`
**Auth:** None currently (noted as a security issue).

Streaming SSE endpoint for the tutor system.

1. Builds `TutorState` from `ChatRequest`.
2. Streams via `tutor_graph.astream(stream_mode="messages")`.
3. Filters tokens from the `generate` node only.
4. Emits `data: {"token": "..."}` events → final `data: [DONE]`.
5. Fires background `manage_session_memory` task after stream completes.

**Request:** `ChatRequest`
**Response:** `StreamingResponse` (SSE `text/event-stream`)

---

## 18. Authentication & Security

### Current Implementation

**File:** `backend/app/api/deps.py`

```python
async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    user_response = supabase.auth.get_user(token)
    return user_response.user.id
```

Uses Supabase GoTrue JWT verification via the anon client. Returns the authenticated user's UUID.

### Supabase Clients

| Client | Key Used | Purpose |
|---|---|---|
| `supabase` (anon) | `SUPABASE_ANON_KEY` | JWT verification |
| `supabase_admin` | `SUPABASE_SERVICE_ROLE_KEY` | Bypasses RLS for server-side writes |

### Known Security Gaps

| Issue | Status |
|---|---|
| Analytics endpoint has no `Depends(get_current_user_id)` | ⚠️ Open |
| Tutor endpoint has no auth | ⚠️ Open |
| Hardcoded `test_user_id` in tutor route (line 37) | ⚠️ Open |
| No CORS middleware configured | ⚠️ Open |
| No rate limiting on any endpoint | ⚠️ Open |
| No prompt injection protection beyond `<`/`>` escaping | ⚠️ Open |

---

## 19. Quantitative Engine Room (Stage 10)

**Directory:** `backend/scripts/`

A suite of offline scripts that operate on the `algorithmic_ledger` to create a self-improving feedback loop. These scripts run as scheduled CI/CD jobs and can also be triggered manually.

### 19.1 Midnight Grader (`scripts/grade_ledger.py`)

**Purpose:** Grades matured predictions against actual market reality.

**Execution:** Runs nightly at 23:00 UTC via GitHub Actions.

**Logic:**
1. Queries `algorithmic_ledger` for rows where `actual_outcome == "PENDING"` and the prediction date is older than the evaluation horizon.
2. For each pending prediction:
   - Fetches the actual price history for the evaluation window after the prediction date.
   - Calculates `max_favorable_excursion` (highest High) and `max_adverse_excursion` (lowest Low).
   - Evaluates **intent-based grading**:
     - For bullish verdicts (`STRONG BUY`, `BUY ON DIP`): WIN if `max_high >= entry × 1.05`, LOSS if `min_low <= entry × 0.95`.
     - For bearish verdicts (`CAUTION`, `AVOID`): WIN if `min_low <= entry × 0.95`, LOSS if `max_high >= entry × 1.05`.
     - Otherwise: DRAW.
3. Updates the ledger row with the graded outcome and excursion values.

**Evaluation Horizons:**

| Timeframe | Days to Wait |
|---|---|
| `swing` | 15 |

**Rate Limiting:** 0.5s sleep between yfinance API calls to avoid throttling.

### 19.2 Statistical Drift Analyzer (`scripts/analyze_drift.py`)

**Purpose:** Detects when the system's configured gate thresholds have drifted from what the data empirically shows works.

**Execution:** Runs weekly (Sundays at 06:00 UTC) via GitHub Actions.

**Logic:**
1. Fetches all graded (non-PENDING, non-DRAW) ledger rows.
2. Requires a minimum of 30 graded rows for statistical significance.
3. Separates data into WIN and LOSS cohorts.
4. Runs drift checks against `config/gate_thresholds.py`:

**Drift Check 1 — RSI Overbought Ceiling:**
- Calculates the P90 RSI of winning trades.
- If `P90_win_rsi < (current_rsi_gate - 3.0)`: fires an insight suggesting the overbought ceiling is too lenient.

**Drift Check 2 — Volume Minimum Ratio:**
- Calculates the median volume ratio of winning trades.
- If `median_win_vol > (current_vol_gate + 0.4)`: fires an insight suggesting the volume floor is too low.

5. Logs insights to the `threshold_insights` table with current threshold, suggested threshold, confidence score, and reasoning.

### 19.3 Time Machine Simulator (`scripts/simulate_live_history.py`)

**Purpose:** Backfills the `algorithmic_ledger` with 2 years of historically-graded predictions to bootstrap the drift analysis engine.

**Execution:** Manual one-time run.

**Logic:**
1. Downloads 2 years of daily OHLCV for 5 blue-chip tickers: `RELIANCE.NS`, `HDFCBANK.NS`, `TCS.NS`, `INFY.NS`, `ICICIBANK.NS`.
2. Walk-forward simulation starting at day 200 (to allow SMAs to warm up):
   - Builds a `BronzePayload` from the historical slice up to each date.
   - Runs the **actual `compute_silver_metrics()` function** on the slice.
   - Evaluates basic gates (RSI, volume ratio) against production thresholds.
   - If gates pass: looks ahead 15 days to determine the actual outcome (WIN/LOSS/DRAW).
   - Only records WIN and LOSS outcomes to avoid noise.
3. Batch upserts all graded rows to `algorithmic_ledger`.

**Ticker Set:** `["RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "INFY.NS", "ICICIBANK.NS"]`

---

## 20. CI/CD — GitHub Actions

**File:** `.github/workflows/engine_room.yml`

### Workflow: Quantitative Engine Room Maintenance

| Schedule | Job | Script |
|---|---|---|
| `0 23 * * *` (Daily 23:00 UTC) | Midnight Grading | `backend/scripts/grade_ledger.py` |
| `0 6 * * 0` (Sundays 06:00 UTC) | Statistical Drift Analysis | `backend/scripts/analyze_drift.py` |
| Manual (`workflow_dispatch`) | Both jobs | Both scripts |

**Environment:** Ubuntu latest, Python 3.12 (not 3.14 — CI uses stable Python for compatibility).

**Secrets Required:** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (configured in GitHub repo settings).

**Dependencies Installed:** `yfinance pandas numpy supabase python-dotenv` (minimal subset — no Ollama/LangGraph needed for offline scripts).

---

## 21. Timeframe-Specific Data & Indicator Matrix

### Summary — What Matters by Timeframe

| | Intraday | Swing | Positional | Long-Term |
|---|---|---|---|---|
| **Config** | `5d / 5m` (~375 candles) | `6mo / 1d` (~126 candles) | `1y / 1d` (~252 candles) | `5y / 1wk` (~260 candles) |
| **Technical weight** | 100% | 70% | 30% | 10% |
| **Fundamental weight** | 0% | 30% | 70% | 90% |
| **Key technical signal** | ATR stop + volume spike | SMA-20/50 + RSI entry | SMA-200 structure + death cross | Weekly SMA-200 + 5yr RS |
| **Key fundamental signal** | Circuit status (gate only) | Debt flag + institutional bias | ROE, revenue CAGR, OPM trend | EPS CAGR, FCF conversion, ROE consistency |
| **Stop-loss basis** | 1.5 × ATR | 2 × ATR | % drawdown tolerance | Portfolio % allocation |
| **Sector RS lookback** | N/A | 20 days | 50 days | 12 weeks |
| **Market regime** | N/A | ✅ (requires 200 sector rows — often unavailable for 6mo) | ✅ | ✅ |

### Bronze Payload Contents by Timeframe

| Field | Intraday | Swing | Positional | Long-Term |
|---|---|---|---|---|
| `price_history` | ~375 rows (5m) | ~126 rows (daily) | ~252 rows (daily) | ~260 rows (weekly) |
| `sector_history` | None | ✅ | ✅ | ✅ |
| `fundamentals` | None | Lightweight (PE, D/E, revenue growth) | Full (3y financials, OPM, ROE) | Full (5y income, balance sheet, cash flow) |
| `circuit_status` | ✅ | ✅ | ✅ | None |
| `institutional_activity` | None | Mock data | None | None |

### Silver Metrics Populated by Timeframe

| Metric | Intraday | Swing | Positional | Long-Term |
|---|---|---|---|---|
| `sma_20` | ✅ | ✅ | ✅ (low weight) | — |
| `sma_50` | ✅ | ✅ | ✅ | ✅ (weekly) |
| `sma_200` | — | — (unreliable) | ✅ | ✅ (weekly) |
| `rsi_14` | ✅ | ✅ | ✅ | ✅ (low weight) |
| `atr_14` | ✅ | ✅ | ✅ (low weight) | — |
| `volume_avg_20` | ✅ | ✅ | ✅ | — |
| `stock_vs_sector_rs` | — | ✅ (20d) | ✅ (50d) | ✅ (12w) |
| `market_regime` | — | ✅* | ✅ | ✅ |
| `sma_gap_pct` | — | — | ✅ | — |
| `pe_vs_sector_avg` | — | ✅ | — | — |
| `debt_flag` | — | ✅ | — | — |
| `institutional_bias` | — | ✅ | — | — |
| `revenue_cagr_3y` | — | — | ✅ | — |
| `profit_cagr_3y` | — | — | ✅ | — |
| `opm_trend` | — | — | ✅ | — |
| `roe_vs_cost_of_capital` | — | — | ✅ | — |
| `valuation_comfort` | — | — | ✅ | — |
| `revenue_cagr_5y` | — | — | — | ✅ |
| `eps_cagr_5y` | — | — | — | ✅ |
| `fcf_conversion` | — | — | — | ✅ |
| `roe_consistency_5y` | — | — | — | ✅ |
| `debt_trajectory` | — | — | — | ✅ |
| `pe_band_vs_growth` | — | — | — | ✅ |

*Swing market regime requires 200 sector data points but only has ~126 — will default to "neutral".

---

## 22. End-to-End Request Lifecycle

### Analytics Pipeline (`POST /api/v1/analytics/process`)

```
Client Request
    ↓
FastAPI Route (analytics.py)
    ↓ Build initial AnalysisState dict
    ↓
LangGraph Pipeline (orchestrator.py)
    ├─ [Node 1: fetch_data]
    │   ├─ router.get_pipeline_manifest(timeframe)
    │   ├─ Cache check → fetch_yfinance_history()
    │   ├─ asyncio.gather(fundamentals, circuit_status)
    │   ├─ Sector fetch (requires fundamentals.sector first)
    │   └─ Return BronzePayload
    │
    ├─ [Node 2: quant_engine]
    │   ├─ asyncio.to_thread(compute_silver_metrics(bronze))
    │   ├─ asyncio.to_thread(evaluate_hard_gates(silver, circuit, capital))
    │   └─ Return SilverMetrics + VerdictDraft
    │
    └─ [Node 3: llm_synthesizer]
        ├─ ChatOllama(llama3.1, temp=0.0).with_structured_output(AnalysisOutput)
        ├─ Sanitize silver/watch data (escape HTML)
        ├─ Prompt template with system + human messages
        ├─ await chain.ainvoke(...)
        ├─ Inject verdict, confidence, disclaimer post-LLM
        └─ Return llm_output dict
    ↓
Background Task: log_prediction_to_ledger()
    ↓
Return PipelineResponse to Client
    ↓
[Nightly] grade_ledger.py grades matured predictions
    ↓
[Weekly] analyze_drift.py detects threshold miscalibration
```

### Tutor Chat (`POST /api/v1/tutor/chat/stream`)

```
Client Request (SSE)
    ↓
FastAPI Route (tutor.py)
    ↓ Build initial TutorState
    ↓
Tutor LangGraph Pipeline
    ├─ [Node: router] → Classify intent → routed_mode
    ├─ (if "news") → [Node: news_tool] → fetch headlines → tool_data
    └─ [Node: generate] → LLM response with mode-specific instructions
    ↓
Stream tokens via SSE: data: {"token": "..."}\n\n
    ↓
data: [DONE]\n\n
    ↓
Background Task: manage_session_memory()
```

---

## 23. Testing

**File:** `backend/test_pipeline.py`

A comprehensive 14-step end-to-end integration test that simulates a full user journey. Uses raw `urllib` (no test framework dependencies).

### Test Steps

| Step | Feature Tested |
|---|---|
| 1 | Health check endpoint with all fields |
| 2 | Analytics pipeline (RELIANCE, swing) — cache MISS |
| 3 | Ledger write + interaction trace verification |
| 4 | Analytics repeat — cache HIT (should be faster) |
| 5 | Ledger de-duplication (2 calls → 1 row) |
| 6 | Analytics different timeframe (long_term) — new ledger entry |
| 7 | Disclaimer presence check |
| 8 | Deterministic verdict injection check |
| 9 | Tutor "definition" route (CAGR explanation) |
| 10 | Tutor "scenario" route (buy triggers) |
| 11 | Tutor "news" tool node (yfinance headlines) |
| 12 | Session memory persistence (chat_sessions table) |
| 13 | Episodic eviction check (16+ messages threshold) |
| 14 | Final health check |

### Running Tests

```bash
cd backend
# Start the server first:
uvicorn main:app --reload
# In another terminal:
python test_pipeline.py
```

### Known Test Limitations

- Uses `print()` output + color codes, not assertion-based (pytest).
- Hardcoded `TEST_USER_ID` and `TEST_SESSION` UUIDs.
- Requires Ollama running locally with `llama3.1` model pulled.
- Requires Supabase configured with correct tables for full verification.

---

## 24. Implementation Tracker

| Feature / Component | Status | Notes |
|:---|:---|:---|
| **Repository Structure** | ✅ Done | Clean separation: api / schemas / services / pipeline / integrations / tools / scripts |
| **Pipeline Router (Stage 1)** | ✅ Done | 4 timeframes fully configured |
| **Data Ingestion — Bronze (Stage 2)** | ✅ Done | yfinance OHLCV, fundamentals, sector, circuit status |
| **Feature Engineering — Silver (Stage 3)** | ✅ Done | SMAs, RSI, ATR, CAGRs, RS, Market Regime, FCF |
| **Gate Logic — Gold (Stage 4)** | ✅ Done | Intraday, Swing, Positional, Long-Term evaluation matrices |
| **Weighted Confidence Scoring** | ✅ Done | 13 gates with severity weights |
| **Post-Verdict Overrides** | ✅ Done | Volume confirmation, buy zone filter, macro override |
| **Trade Setup Generation (Stage 7)** | ✅ Done | ATR-based entry/stop/target with Kelly-adjacent sizing |
| **LangGraph Orchestrator (Stage 5)** | ✅ Done | 3-node linear graph with error propagation |
| **LLM Synthesis — Platinum (Stage 6)** | ✅ Done | Structured output with post-LLM injection |
| **LLM Offline Fallback** | ✅ Done | Returns deterministic verdict if Ollama is down |
| **Prompt Injection Mitigation** | ✅ Done | HTML entity escaping on user-facing data |
| **Regulatory Disclaimer** | ✅ Done | Injected post-LLM into every response |
| **Local File Cache** | ✅ Done | TTL-based with per-timeframe expiry |
| **Hybrid Ledger Logging (Stage 8)** | ✅ Done | De-duplicated daily, interaction trace |
| **User Profile System (Stage 0)** | ✅ Done | Pydantic validation, contradiction detection, MD5 hash, Supabase upsert |
| **JWT Authentication** | ✅ Done | `deps.py` with Supabase GoTrue — applied to profile route |
| **Tutor System (Stage 9)** | ✅ Done | 4-mode semantic router + streaming generation |
| **Tutor News Tool** | ✅ Done | yfinance headlines injection |
| **Session Memory Persistence** | ✅ Done | Supabase chat_sessions with working + episodic memory |
| **Chunked Memory Eviction** | ✅ Done | 16-message watermark → LLM summarization → semantic profile patch |
| **Health Check Endpoint** | ✅ Done | Cache, DB, system status |
| **End-to-End Integration Test** | ✅ Done | 14-step user journey covering all features |
| **`.env.example`** | ✅ Done | Template for 3 required env vars |
| **`.gitignore`** | ✅ Done | Covers .env, cache, venv, pycache, node_modules |
| **Midnight Grader (Stage 10a)** | ✅ Done | Grades matured predictions against market reality |
| **Statistical Drift Analyzer (Stage 10b)** | ✅ Done | Detects threshold miscalibration from win/loss data |
| **Time Machine Simulator (Stage 10c)** | ✅ Done | Backfills 2y of graded production logs for bootstrapping |
| **GitHub Actions CI/CD** | ✅ Done | Nightly grading + weekly drift analysis |
| **`threshold_insights` Table** | ✅ Done | Stores drift analyzer suggestions |
| **`ratios` Sub-Dictionary** | ✅ Done | Populated in `fetch_yfinance_fundamentals()` |
| **FCF Conversion Calculation** | ✅ Done | Σ(CFO - Capex) / Σ(Net Profit) over 5y |
| **Memory Service Client Fix** | ✅ Done | Now uses centralized `supabase_admin` from `database.py` |
| **Death Cross `abs()` Fix** | ✅ Done | Uses `abs(sma_gap_pct)` for gap comparison |
| **Debt Flag Dual-Check** | ✅ Done | Handles both percentage and ratio format from yfinance |
| **Auth on Analytics Endpoint** | ❌ Missing | `Depends(get_current_user_id)` not added |
| **Auth on Tutor Endpoint** | ❌ Missing | Hardcoded test user ID in production code |
| **CORS Middleware** | ❌ Missing | No CORS configured on FastAPI |
| **Rate Limiting** | ❌ Missing | No rate limiting on any endpoint |
| **Structured Logging** | ✅ Done | Replaced `print()` with `logging` module across the app |
| **Unit Tests (pytest)** | ✅ Done | Added assertion-based tests for financial math (`test_silver_math.py`) |
| **Frontend** | ❌ Not Started | `frontend/` directory is empty |
| **RAG Vector Search** | ❌ Not Started | Tutor uses pure LLM, no pgvector/embedding retrieval |
| **Redis Cache** | ❌ Not Started | Declared as dependency but not implemented |
| **Intraday Timeframe** | ⏸️ Deferred (v2) | VWAP, real-time feeds, sub-minute execution logic |
| **Peer Comparison** | ⏸️ Deferred (v2) | Relative valuation against specific industry peers |
| **Real Institutional Data** | ⏸️ Deferred | Currently mock — needs NSE bulk/block deal scraping |
| **Zerodha Kite Connect** | ⏸️ Deferred | Primary data source planned but not integrated |
| **Claude/Anthropic API** | ⏸️ Deferred | Production LLM upgrade from local Ollama |
| **Monte Carlo Simulation** | ⏸️ Deferred | All projections currently single-path deterministic |
| **Inflation Adjustment** | ⏸️ Deferred | No FV calculations account for inflation |

---

## 25. Known Issues & Audit Findings

### Critical

| ID | Description | Impact |
|---|---|---|
| P5-01 | Hardcoded `test_user_id` in tutor endpoint (line 37) | All chat saved under one UUID — destroys data isolation |

### High Priority

| ID | Description | Impact |
|---|---|---|
| P3-01 | Analytics endpoint has no authentication | Any unauthenticated caller can run the full pipeline |
| P3-02 | Tutor endpoint has no authentication | Any caller can trigger LLM inference |
| P4-01 | No CORS middleware configured | API accepts requests from any origin |
| P1-03 | `sector_pe_median` hardcoded to `25.0` | P/E vs sector comparison always uses static fiction |

### Medium Priority

| ID | Description | Impact |
|---|---|---|
| P0-06 | `redis` declared but never imported | Unnecessary dependency weight |
| P6-01 | No rate limiting (Middleware missing) | Single client can flood expensive LLM calls |

### Low Priority / Optimizations

| ID | Description |
|---|---|
| P9-04 | MD5 for profile hashing — should be SHA-256 |
| P5-03 | `Settings` class mixes `os.getenv()` with `pydantic_settings` |
| P1-01 | Institutional activity data is entirely hardcoded mock |
| P1-02 | Book value per share is hardcoded mock data |
| P4-03 | Analysis state truncated to 2000 chars in tutor — no token counting |

---

## 26. Roadmap & Planned Features

### v1.1 — Security & Correctness

- [ ] Add `Depends(get_current_user_id)` to analytics and tutor endpoints
- [ ] Remove hardcoded test user ID from tutor route
- [ ] Add CORS middleware (restrict to frontend origin)
- [ ] Add rate limiting via `slowapi` (10/minute for analytics, 30/minute for tutor)
- [x] Fix secular_trend gate PASS overwrite bug
- [ ] Remove or document mock data (institutional activity, sector PE, BVPS)
- [ ] Replace MD5 with SHA-256 for profile hashing
- [x] Replace `print()` with structured `logging` module
- [x] Fix `ledger_service.py` to use centralized Supabase client from `database.py`
- [ ] Fix `Settings` class to use pydantic-settings properly (remove `os.getenv()` calls)

### v1.2 — Testing & Quality

- [x] Create `tests/` directory with pytest unit tests for:
  - `calculate_cagr()` edge cases (negative, zero, single element)
  - RSI calculation against known reference values
  - ATR calculation verification
  - Gold Layer gate evaluation (all timeframes)
  - Confidence score computation
  - Trade setup arithmetic
- [ ] Add integration tests with mock data (no external API calls)
- [ ] Pin exact dependency versions

### v1.3 — Engine Room Expansion

- [x] Add positional (90-day) and long-term (365-day) grading horizons to `grade_ledger.py`
- [x] Use actual ATR-based trade setup targets for win/loss grading instead of fixed ±5%
- [x] Run full `evaluate_hard_gates()` in `simulate_live_history.py` instead of partial gate checks
- [x] Add more drift checks: death cross gap, sector RS threshold, valuation ceiling, EPS CAGR floor
- [x] Align CI/CD Python version with project requirement (3.14+)
- [ ] Build admin dashboard for viewing `threshold_insights` data

### v2.0 — Frontend & UX

- [ ] Build React/Next.js frontend
- [ ] Dashboard with analysis results display
- [ ] Interactive tutor chat with SSE streaming
- [ ] Profile creation/editing forms
- [ ] Historical analysis viewer (from ledger data)
- [ ] Mobile-responsive design

### v2.1 — Advanced Features

- [ ] **Intraday Timeframe** — VWAP indicator, real-time WebSocket feeds, sub-minute execution logic
- [ ] **Peer Comparison** — relative valuation against industry peer group
- [ ] **Real Institutional Data** — NSE bulk/block deal scraping, FII/DII flow integration
- [ ] **RAG Tutor** — pgvector embeddings of financial education corpus for retrieval-augmented teaching
- [ ] **Zerodha Kite Connect** — live quotes, authenticated order data, real portfolio sync

### v3.0 — Production Scale

- [ ] Migrate cache to Redis
- [ ] Claude/Anthropic API integration for production LLM
- [ ] Monte Carlo simulation for probabilistic projections
- [ ] Inflation-adjusted future value calculations
- [ ] Prompt versioning and A/B testing
- [ ] LLM response caching for identical queries
- [ ] Supabase RLS policies for all tables
- [ ] Background worker queue (Celery/ARQ) for heavy LLM inference
- [ ] Deployment to cloud (Docker + Supabase hosted)

---

## Appendix A: How to Run Locally

### Prerequisites

- Python 3.14+
- [Ollama](https://ollama.ai) installed with `llama3.1` model pulled
- Supabase project with tables created (see Section 5)
- `uv` package manager (recommended) or `pip`

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd INVR/backend

# Create .env from example
cp .env.example .env
# Fill in your Supabase credentials

# Install dependencies
uv sync
# OR: pip install -r requirements.txt

# Pull Ollama model
ollama pull llama3.1

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Quick Test

```bash
# Health check
curl http://localhost:8000/health

# Run full integration test
python test_pipeline.py
```

### Running Engine Room Scripts

```bash
# Bootstrap ledger with historical data (one-time)
python scripts/simulate_live_history.py

# Grade matured predictions manually
python scripts/grade_ledger.py

# Run drift analysis manually
python scripts/analyze_drift.py
```

### Sample API Call

```bash
curl -X POST http://localhost:8000/api/v1/analytics/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "RELIANCE",
    "timeframe": "swing",
    "user_profile": {
      "experience_level": "intermediate",
      "goal": "wealth_growth",
      "risk_tolerance": "moderate",
      "available_capital": 250000.0
    }
  }'
```

---

## Appendix B: Supabase Table Creation SQL

```sql
-- User Profiles
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    experience TEXT NOT NULL,
    goal TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    risk TEXT NOT NULL,
    portfolio JSONB NOT NULL DEFAULT '{}',
    capital FLOAT8 NOT NULL DEFAULT 0,
    profile_version_hash TEXT,
    contradictions_flagged JSONB DEFAULT '[]',
    semantic_profile JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Algorithmic Ledger
CREATE TABLE algorithmic_ledger (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    date DATE NOT NULL,
    pipeline_version TEXT NOT NULL,
    silver_state JSONB,
    gold_verdict JSONB,
    actual_outcome TEXT NOT NULL DEFAULT 'PENDING',
    max_favorable_excursion FLOAT8,
    max_adverse_excursion FLOAT8,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prediction Interactions
CREATE TABLE prediction_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_id UUID REFERENCES algorithmic_ledger(log_id),
    session_id TEXT NOT NULL,
    action_taken TEXT NOT NULL DEFAULT 'viewed',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat Sessions
CREATE TABLE chat_sessions (
    session_id TEXT PRIMARY KEY,
    user_id UUID REFERENCES user_profiles(id),
    working_memory JSONB DEFAULT '[]',
    episodic_memory JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Threshold Insights (Drift Analyzer Output)
CREATE TABLE threshold_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    current_threshold FLOAT8 NOT NULL,
    suggested_threshold FLOAT8 NOT NULL,
    confidence_score FLOAT8 DEFAULT 0.0,
    reasoning TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

*Last updated: 2026-06-20 | Pipeline Version: v1.0.0 | Python 3.14+ | FastAPI 0.136.3+ | LangGraph 1.2.4+*
