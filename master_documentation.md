# FinAI: Master System Architecture & Execution Flow

> A comprehensive, unified guide to the FinAI project, detailing system design, execution pipeline, financial logic, and implementation tracking.

---

## 1. Project Overview & Philosophy

Most AI financial tools hallucinate numbers or provide vague, non-actionable advice. FinAI solves this by strictly separating **Deterministic Math** from **Probabilistic Language**.
- **The Python engine computes the ground truth.**
- **The LLM only translates it.**

The LLM never decides if a stock is a "Buy" or calculates a Stop Loss. All decisions, verdicts, and numeric calculations are done by the quantitative engine using strict "Hard Gates."

---

## 2. Foundational System Architecture & Tech Stack

FinAI is built as a multi-stage pipeline orchestrated by **LangGraph**.

### Tech Stack
* **Language:** Python 3.14+
* **Backend Framework:** FastAPI
* **Orchestration:** LangGraph (State management, conditional routing, parallel execution)
* **LLM Engine:** Local execution via Ollama (`llama3.1`, temperature=0.0) & LangChain. (Note: Production shift planned to Claude/Anthropic API `claude-sonnet-4-20250514` for nuanced financial communication).
* **Data Processing:** Pandas (vectorized operations, EWMA smoothing), NumPy.
* **Validation:** Pydantic.
* **Vector DB:** `pgvector` (via Supabase for RAG and logging).

### Foundational Principles
1. **Data Source Hierarchy:**
   - *Primary:* Zerodha Kite Connect API (historical, live quotes, fundamentals).
   - *Secondary:* NSE/BSE direct feeds.
   - *Fallback:* `yfinance` (with 15-minute freshness validation).
2. **Deterministic Confidence:** Confidence scores are strictly computed via mathematical signal components (gate pass/fail ratio, RSI distance, SMA divergence), never LLM-generated.

---

## 3. The Execution Pipeline (Stages 0 - 9)

### Stage 0: User Profile Ingestion & Validation
* **Tech:** FastAPI, Pydantic, Supabase.
* **Logic:** Validates and canonicalizes raw user input. Checks for contradictions (e.g., capital preservation goal with aggressive risk). Normalizes portfolio weights to 1.0.
* **Inputs Used:** Raw JSON request from frontend.
* **Outputs:** `UserProfile` object (experience, goal, timeframe, risk, portfolio, capital).
* **Who Uses It:** Used by Stage 1 (Router) and Stage 4 (Gold Layer constraints). Logged to Supabase with a version hash.

### Stage 1: The Router
* **Tech:** Pure Python deterministic routing.
* **Logic:** Determines the exact pipeline execution path based on the user's `timeframe`. It generates a config matrix defining which data fetcher, indicators, and hard gates are necessary.
* **Parameters Used:** `timeframe` (intraday, swing, positional, long_term).
* **Inputs Used:** `UserProfile.timeframe`.
* **Outputs:** Pipeline configuration dictionary.
* **Who Uses It:** Downstream stages (Bronze, Silver, Gold) to selectively run computations, preventing unnecessary calculations.

### Stage 2: Data Fetching Layer (Bronze)
* **Tech:** Async Python, external APIs (Kite, yfinance, NSE).
* **Logic:** Fetches raw data (prices, fundamentals, index benchmarks, circuit statuses, bulk/block deals) in a single batched async call. Implements freshness validation.
* **Inputs Used:** `ticker`, timeframe config.
* **Outputs:** `BronzePayload` (raw price history, fundamentals, sector index data, circuit breaker status).
* **Who Uses It:** Stage 3 (Silver Layer).

### Stage 3: Silver Layer (Indicator Computation)
* **Tech:** Python, Pandas, `pandas-ta` / `ta-lib`.
* **Logic:** Uses vectorized operations to transform raw prices into standard indicators based on the router config. Computes the deterministic Confidence Score. Calculates exact Death Cross divergence thresholds (>0.5% gap required).
* **Parameters Used:** 
  - SMAs: 20, 50, 200.
  - RSI (14), ATR (14).
  - Volume Average (20).
  - CAGRs (3y/5y), ROE.
* **Inputs Used:** `BronzePayload`.
* **Outputs:** `SilverMetrics` containing moving averages, momentum indicators, volatility metrics, revenue growth, sector relative strength, and the calculated Confidence Score.
* **Who Uses It:** Stage 4 (Gold Layer).

### Stage 4: Gold Layer (The Decision Engine)
* **Tech:** Pure Python evaluation matrix.
* **Logic:** Evaluates `SilverMetrics` against user constraints and hard thresholds. Produces a 5-state verdict: `STRONG BUY`, `BUY ON DIP`, `MONITOR`, `CAUTION`, `AVOID`.
* **Parameters/Gates Used:** 
  - Trend checks (Price vs SMAs).
  - Death Cross check.
  - RSI extreme checks.
  - Sector Momentum check (Stock vs Sector RS thresholds).
  - Volume validation (e.g. Volume > 1.5x average).
  - Concentration caps (Conservative: 25%, Moderate: 45%, Aggressive: 65%).
* **Inputs Used:** `SilverMetrics`, `UserProfile`.
* **Outputs:** `VerdictDraft` (Verdict, gates status) and mathematically generated `TradeSetup` (if STRONG BUY).
* **Who Uses It:** Passed into the LangGraph state for Stage 6.

### Stage 5: The LangGraph State Object
* **Tech:** LangGraph (`StateGraph`).
* **Logic:** The single source of truth passed between nodes. Uses conditional edges and parallel branches (e.g., bypassing Fundamental nodes for Intraday).
* **Inputs Used:** Outputs from Stages 0-4.
* **Outputs:** Fully assembled `AnalysisState`.
* **Who Uses It:** The LLM Synthesis node (Stage 6) and Tutor System.

### Stage 6: The LLM Synthesis (Platinum Layer)
* **Tech:** `llama3.1` (local, temp=0.0) / Anthropic Claude.
* **Logic:** A single structured generation call enforcing JSON output via Pydantic. Translates quantitative verdicts into personalized explanations without contradicting math or inventing numbers. Extracts and surfaces `what_to_watch` triggers for passive tracking.
* **Inputs Used:** `AnalysisState` (Verdict, Confidence, Silver Metrics, Gates).
* **Outputs:** `AnalysisOutput` JSON (personalized reasoning, `what_to_watch` triggers, risk warning, `tutor_triggers`).
* **Who Uses It:** The frontend presentation layer and the Supabase logging mechanism.

### Stage 7: Trade Setup Generation
* **Tech:** Pure Python arithmetic (executed as part of the Gold Layer if applicable).
* **Logic:** Applies Kelly-adjacent risk management. Computes Entry zones, Stop Loss (based on ATR wiggles), Target zones, and exact Position Sizing ensuring maximum risk per trade equals 2% of total capital.
* **Parameters Used:** ATR (14), Total Capital, Risk Cap (2%), Timeframe-specific ATR Multipliers.
* **Inputs Used:** `SilverMetrics.atr`, `SilverMetrics.current_price`, `UserProfile.capital`.
* **Outputs:** `TradeSetup` object.
* **Who Uses It:** Displayed to the user within the `AnalysisOutput`.

### Stage 8: Logging to Supabase
* **Tech:** PostgreSQL / Supabase.
* **Logic:** Persists every analysis. Critical for enabling algorithmic backtesting tracking historical performance.
* **Inputs Used:** Final `AnalysisState`.
* **Outputs:** Database record in `analysis_logs` with `pipeline_version`.
* **Who Uses It:** Backtesting scripts and data science review systems.

### Stage 9: The Tutor System
* **Tech:** `pgvector`, Retrieval-Augmented Generation (RAG).
* **Logic:** Parallel, non-blocking track. Three modes: Term Explainer, Context-Aware Follow-up (using full `AnalysisState`), and Scenario Explainer (translating `what_to_watch`). Includes strict hallucination fallbacks if data doesn't exist in the corpus.
* **Inputs Used:** User questions, `AnalysisState`, vector embeddings.
* **Outputs:** Contextualized educational answers mapping directly to the user's specific asset analysis.
* **Who Uses It:** The end-user querying the UI.

---

## 4. Implementation Tracker

Maintains a live snapshot of what components are currently running in the repository vs. what remains in the roadmap.

| Feature / Stage | Description | Status |
| :--- | :--- | :--- |
| **Data Ingestion (Bronze)** | `yfinance` integration for target assets and benchmarks. | ✅ **Done** |
| **Feature Engineering (Silver)** | SMAs, RSI, ATR, CAGRs, Market Regime computations. | ✅ **Done** |
| **Gate Logic (Gold)** | Evaluation matrices for Swing, Positional, Long-Term timeframes. | ✅ **Done** |
| **Trade Math** | Volatility-adjusted trade setup and position sizing. | ✅ **Done** |
| **LLM Integration** | Orchestration via local `llama3.1` with Pydantic outputs. | ✅ **Done** |
| **Parallel LangGraph Routing** | Implementing parallel branches and conditional edge skipping (Stage 5). | ⏳ **Remaining** |
| **Supabase Logging (Stage 8)** | Storing `AnalysisState` and `pipeline_version` for backtesting. | ⏳ **Remaining** |
| **The Tutor System & RAG (Stage 9)** | `pgvector` RAG, interactive explanations, and Q&A context. | ⏳ **Remaining** |
<!-- | **Primary Data Source Migration** | Switching from `yfinance` to Zerodha Kite Connect API. | ⏳ **Remaining** |
| **Model Migration** | Transitioning from Ollama to Claude API (`claude-sonnet-4-20250514`). | ⏳ **Remaining** | -->
| **Intraday Timeframe** | VWAP, real-time feeds, sub-minute execution logic. | ⏸️ **Deferred (v2)** |
| **Peer Comparison** | Relative valuation and relative strength against specific industry peers. | ⏸️ **Deferred (v2)** |

