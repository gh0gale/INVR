# FinAI: Complete Project Overview & Architecture

> A comprehensive guide to understanding the FinAI project, its philosophy, working mechanisms, financial logic, and implementation state.

---

## 1. Project Overview & Philosophy

### The Problem
Most AI financial tools fall into one of two traps:
1. **Hallucination:** They let Language Models (LLMs) do math, leading to fabricated price targets and incorrect position sizes.
2. **Vagueness:** They output passive, non-actionable advice (e.g., "The stock looks good but carries risk").

### The FinAI Solution
FinAI solves this by strictly separating **Deterministic Math** from **Probabilistic Language**. 
The system operates on a rigid philosophy: **The Python engine computes the ground truth; the LLM only translates it.**

The pipeline never allows the LLM to decide if a stock is a "Buy" or to calculate a Stop Loss. All decisions, verdicts, and numbers are computed by a quantitative engine using strict "Hard Gates." The LLM's only job is to take that mathematical reality and explain it clearly to the user based on their experience level and risk profile.

---

## 2. System Architecture & Tech Stack

FinAI is built as a multi-stage pipeline orchestrated by **LangGraph**. Data flows linearly from raw ingestion up to the final AI synthesis.

### Tech Stack
* **Language:** Python 3.14+
* **Backend Framework:** FastAPI (for API routing)
* **Orchestration:** LangGraph (State management and pipeline routing)
* **LLM Engine:** Local execution via Ollama (`llama3.1`, temperature=0.0) & LangChain (`langchain-ollama`). Using a local model at 0 temperature ensures deterministic, private, and consistent outputs.
* **Data Processing:** Pandas (for vectorized indicator computations, EWMA smoothing) & NumPy.
* **Validation:** Pydantic (ensures data integrity at every step of the pipeline).

### Data Sources
* **Primary Asset Data:** `yfinance` is used to fetch raw Open, High, Low, Close, Volume (OHLCV) history, as well as basic fundamentals.
* **Market Benchmark:** The system simultaneously fetches the **Nifty 50 Index (`^NSEI`)** to gauge the broader market mood. We cannot evaluate a stock in isolation without knowing what the overall market is doing.

---

## 3. The 4-Layer Pipeline (How it Works)

The project processes every analysis request through four distinct layers:

### Stage 1: Bronze Layer (Raw Data Ingestion)
The pipeline begins by fetching raw data. It pulls historical price charts for the requested stock and the broader index benchmark. It also attempts to scrape whatever fundamental data is available (PE ratios, debt, margins). 
* **Output:** A `BronzePayload` object containing raw DataFrames and raw dictionaries.

### Stage 2: Silver Layer (Feature Engineering)
Raw data is useless without context. The Silver layer uses vectorized Pandas operations to transform raw prices into standard financial indicators. It calculates Moving Averages, Momentum (RSI), Volatility (ATR), and Revenue/Profit Growth rates. It adapts its calculations based on the user's timeframe (Intraday, Swing, Positional, Long-term).
* **Output:** A `SilverMetrics` object containing all computed financial indicators.

### Stage 3: Gold Layer (The Decision Engine)
This is the heart of the system. The Gold layer evaluates the `SilverMetrics` against a strict set of predefined thresholds (Hard Gates). If a stock's RSI is over 75, it fails the momentum gate. If the 50-day average crosses below the 200-day average, it fails the trend gate.
* **Output:** A deterministic `VerdictDraft` (e.g., STRONG BUY, AVOID) and a mathematically calculated `TradeSetup`.

### Stage 4: Platinum Layer (LLM Synthesis)
The pipeline passes the final `VerdictDraft` to the local Llama 3.1 model. The LLM is given a strict prompt: *Never contradict the math, never invent numbers.* The LLM looks at the user's profile (e.g., "Beginner, Conservative") and translates the dry mathematical verdict into a personalized, educational summary.
* **Output:** A human-readable `AnalysisOutput` JSON containing personalized reasoning and actionable things to watch.

---

## 4. Financial Logic & Parameters Explained

If you are reading the codebase, you will see many financial parameters. Here is the logic behind *why* they are computed and how they are used.

### Core Technical Indicators (Silver Layer)
* **SMA (Simple Moving Average - 20, 50, 200):** These act as structural floors and ceilings. We use the 20-day for short-term swing trends, the 50-day for medium trends, and the 200-day to anchor secular long-term trends.
* **RSI (Relative Strength Index - 14):** Measures momentum on a 0-100 scale. We use it to warn users if they are buying at the top (overbought > 75) or catching a falling knife (oversold < 25).
* **ATR (Average True Range - 14):** Measures daily volatility. **Crucial Logic:** We use ATR to calculate Stop Losses. Instead of a random "5% stop loss", we set the stop loss based on the stock's actual daily wiggles (e.g., 2x ATR).
* **Volume Average (20):** Retail traders move prices, but institutions move volume. We use this to confirm breakouts.

### Macro & Top-Down Filters (Silver/Gold Layer)
* **Market Regime:** The system checks if the Nifty 50 is above or below its own 50/200 SMAs. **Logic:** If the broader market is crashing (Bearish regime), the system suppresses all bullish verdicts to protect the user's capital.
* **Stock vs Sector RS (Relative Strength):** Measures if the stock is outperforming the index. We want to buy leaders, not laggards.

### Fundamental Parameters (Silver Layer)
* **Valuation (PE) & Debt Flag:** Protects long-term investors from severely overvalued companies or companies drowning in debt (Debt/Equity > 1.5).
* **CAGR (Compound Annual Growth Rate):** Calculates the actual 3-year or 5-year annualized growth for Revenues and Profits to ensure the company is a consistent compounder.
* **ROE (Return on Equity) > 15%:** Ensures the company generates high returns on the money it reinvests.

### The Verdict Resolution System (Gold Layer)
The gates spit out one of 5 definitive states:
1. **STRONG BUY:** All technical and fundamental gates pass perfectly.
2. **BUY ON DIP:** Mixed signals, but no critical failures. *Dynamic Override:* The system strictly enforces that a "Dip" must be within 3% of a structural moving average (50 or 200 SMA). Otherwise, it's just a falling stock mid-air.
3. **MONITOR:** Exactly one major gate is failing (e.g., good trend, but overbought).
4. **CAUTION:** Two or more gates are failing. The setup is breaking down.
5. **AVOID:** Execution is fundamentally blocked (e.g., the stock is locked in a circuit limit).

### Trade Setup & Risk Management (Gold Layer)
When a `STRONG BUY` is triggered, the system generates a Trade Setup. **This is pure arithmetic:**
* **Position Sizing:** `(Total Capital × 2% Risk) / (Entry Price - Stop Loss Price)`. **Logic:** This ensures that even if the trade hits the stop loss, the user only loses exactly 2% of their total portfolio.
* **Targets:** Target 1 is set at 3x the ATR, and Target 2 is set at 5x the ATR, ensuring a mathematically positive Risk-to-Reward ratio.

---

## 5. Project Roadmap: What is Implemented vs. Pending

### ✅ Fully Implemented (Currently in the Codebase)
* **Data Ingestion:** `yfinance` integrations for both the target asset and the benchmark index.
* **Feature Engineering:** Full calculation of SMAs, RSI, ATR, CAGRs, and Market Regime.
* **Gate Logic:** Strict evaluation matrices for all timeframes (Intraday, Swing, Positional, Long-Term).
* **Trade Math:** Dynamic, volatility-adjusted trade setup generation and position sizing.
* **LLM Integration:** LangGraph-based orchestration leveraging local `llama3.1` with strict structured Pydantic outputs.

### ⏳ Pending / Not Yet Implemented (Referencing `phases.md`)
1. **Parallel LangGraph Execution (Stage 5):**
   * *Current State:* The graph runs linearly (`Fetch` -> `Quant` -> `LLM`).
   * *To Do:* Implement parallel branching. The Fundamental node and Technical node should run simultaneously, and the Fundamental node should be conditionally bypassed for Intraday timeframes.
2. **Supabase Logging & Backtesting (Stage 8):**
   * *Current State:* Analyses are computed and returned, but not saved.
   * *To Do:* Log every `AnalysisState` to a Supabase database with a `pipeline_version` tag. This will enable automated backtesting scripts to grade the system's accuracy over time.
3. **The Tutor System & RAG (Stage 9):**
   * *Current State:* The LLM highlights complex terms in the `tutor_triggers` array, but they aren't clickable.
   * *To Do:* Build a `pgvector` powered Retrieval-Augmented Generation (RAG) system. When a user asks "Why did the RSI fail?", the Tutor API will read the exact `AnalysisState` context and explain the reasoning dynamically.
