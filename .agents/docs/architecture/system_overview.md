# 🧠 Complete AI Investment System: End-to-End Architecture Blueprint

## 🎯 1. System Overview
This document defines the architecture for an AI-powered Investment System. The system operates on a **Hybrid Architecture**: strictly deterministic Python scripts handle all mathematical analysis (The 6 Pillars), while a LangChain ReAct Agent (The Lead PM) synthesizes these findings with the user's personal context to generate personalized, human-readable advice and provide ongoing financial education.

### Core Tech Stack
* **Framework:** FastAPI (Backend)
* **AI Orchestration:** LangChain (`AgentExecutor`, `@tool` decorators)
* **LLM:** Groq API (Llama-3-70B for tool calling and JSON generation)
* **Database:** Supabase (PostgreSQL for user state, `pgvector` for RAG)
* **Data Providers:** yfinance, Upstox/Dhan APIs (for OHLCV/Options), News APIs.

---

## 🔄 2. The End-to-End Execution Flow

### Phase 1: Onboarding & State Persistence
1. **User Input:** User completes onboarding MCQs (income, goals, risk appetite, current portfolio).
2. **Normalization:** `app/services/portfolio_normalizer.py` converts raw text into structured sector weights.
3. **Scoring:** `app/services/persona_engine.py` calculates a Risk Score and assigns a Persona (e.g., Aggressive Growth).
4. **Storage:** Data is written to Supabase (`user_profiles`, `user_personas`, `portfolio_models`).

### Phase 2: Just-In-Time Stock Query & Data Fetching
1. **Trigger:** User asks: *"Should I buy Reliance?"*
2. **Fetch:** `app/etl/market_fetcher.py` is triggered. It fetches **only** the data required for Reliance at that exact moment:
   * *Financials:* Quarterly/Annual statements (Income, Balance, Cash Flow).
   * *Market Data:* Daily/Weekly OHLCV (Open, High, Low, Close, Volume).
   * *Derivatives:* Live options chain (if applicable).
   * *Macro/News:* Recent headlines and current India VIX/Repo rates.

### Phase 3: The 6 Deterministic Analysts
The raw data is passed to `app/services/analysts/`. Each analyst calculates specific metrics and normalizes the final result to a `0-100` score.
* **Fundamental (`fundamental.py`):** Calculates ROE, ROCE, DuPont, Debt-to-Equity, Current Ratio, Altman Z-Score, FCF Yield.
* **Valuation (`valuation.py`):** Calculates Forward P/E vs Historical, EV/EBITDA, P/B, PEG Ratio, DCF Margin of Safety, Dividend Yield.
* **Technical (`technical.py`):** Calculates RSI, MACD, 50/200 EMA Crossovers, ADX, VWAP, Bollinger Bands.
* **Quantitative (`quantitative.py`):** Calculates Beta vs Nifty 50, Sharpe Ratio, Sortino Ratio, Max Drawdown, Value at Risk (VaR).
* **Derivative (`derivative.py`):** Calculates Put-Call Ratio (PCR), IV Percentile, OI Buildup, Max Pain.
* **Sentiment/Macro (`sentiment.py`):** Calculates FinBERT News Score, FII/DII Net Activity, Repo Rate impact, India VIX context.

#FOR ANALYSTS
🏛️ 1. The Fundamental Analyst (The Accountant)
Objective: Determine the underlying business quality, efficiency, and financial survival capability.
Data Needed: Quarterly/Annual Financial Statements (Income Statement, Balance Sheet, Cash Flow Statement).

Comprehensive Metrics:

Profitability & Efficiency:

Return on Equity (ROE) & Return on Capital Employed (ROCE): Is management generating good returns on the money given to them?

DuPont Analysis: Breaks down ROE into profit margin, asset turnover, and financial leverage to see why ROE is high (are they just taking on debt, or actually selling more?).

Operating Margin Growth: Are margins expanding or shrinking quarter-over-quarter?

Financial Health & Solvency:

Debt-to-Equity & Interest Coverage Ratio: Can they comfortably pay the interest on their debt? (Crucial in high-interest rate environments).

Current Ratio & Quick Ratio: Do they have enough cash to survive a sudden 12-month crisis?

Altman Z-Score: A mathematical formula that predicts the probability of a company going bankrupt within 2 years.

Cash is King:

Free Cash Flow (FCF) Yield: Earnings can be manipulated; cash in the bank cannot. How much actual cash is the business spinning off?

⚖️ 2. The Valuation Analyst (The Deal Hunter)
Objective: Determine if the stock is cheap or expensive compared to its intrinsic value, its peers, and its own history.
Data Needed: Current market cap, historical price multiples, peer group multiples, forward EPS estimates.

Comprehensive Metrics:

Relative Valuation:

Forward P/E vs. Historical P/E: Is it cheaper today than its 5-year historical average?

EV/EBITDA: Better than P/E because it accounts for the company's debt and cash (Enterprise Value).

Price-to-Book (P/B): Crucial for valuing Banks and NBFCs.

Growth-Adjusted Valuation:

PEG Ratio (P/E to Growth): A stock with a P/E of 30 is cheap if it's growing at 40% (PEG < 1).

Intrinsic Valuation:

Discounted Cash Flow (DCF) Margin of Safety: The Python script runs a basic DCF model. If the calculated intrinsic value is ₹1000 and the stock is ₹800, it has a 20% margin of safety.

Dividend Yield: Is it paying you to wait?

📈 3. The Technical Analyst (The Trend Tracker)
Objective: Identify the optimal entry/exit points based on market psychology and price action momentum.
Data Needed: Daily/Weekly OHLCV (Open, High, Low, Close, Volume) time-series data.

Comprehensive Metrics:

Momentum & Oscillators:

Relative Strength Index (RSI): Is it overbought (>70) or oversold (<30)?

MACD (Moving Average Convergence Divergence): Is the short-term momentum accelerating faster than the long-term momentum?

Trend Following:

Moving Average Crossovers: 50-day EMA crossing above 200-day EMA (Golden Cross = Bullish) or below (Death Cross = Bearish).

ADX (Average Directional Index): Tells you how strong a trend is. (A stock might be going up, but if ADX is weak, it's a fake-out).

Volume & Support:

VWAP (Volume Weighted Average Price): The true average price based on volume.

Bollinger Bands: Measures volatility and mean-reversion. Is the stock trading outside its normal standard deviation?

🧮 4. The Quantitative Analyst (The Risk Manager)
Objective: Measure statistical risk and historical volatility. This analyst doesn't care about the company; it only cares about the math of the stock's movements.
Data Needed: 3-to-5 years of daily return data for the stock, and the benchmark index (e.g., Nifty 50).

Comprehensive Metrics:

Systematic Risk:

Beta: If Nifty drops 1%, does this stock drop 2% (Beta = 2.0, High Risk) or 0.5% (Beta = 0.5, Defensive)?

Risk-Adjusted Returns:

Sharpe Ratio: How much return are you getting for the amount of volatility you are enduring?

Sortino Ratio: Better than Sharpe. It only penalizes downside volatility (because nobody complains when a stock goes up volatility).

Tail Risk:

Maximum Drawdown: Historically, what is the worst peak-to-trough drop this stock has experienced?

Value at Risk (VaR): Statistically, what is the maximum amount of money you could lose in a single day with 95% confidence?

🔮 5. The Derivative Analyst (The Market Whisperer)
Objective: Read the "smart money." Retail investors buy stocks; institutions buy options. This analyzes options data to see where big players are placing their bets.
Data Needed: Live Options Chain data (Open Interest, Strike Prices, Implied Volatility). (Note: Only applies to F&O approved stocks).

Comprehensive Metrics:

Sentiment Indicators:

Put-Call Ratio (PCR): If PCR is > 1.0, more people are buying Puts (protection), meaning the market is fearful. Extreme fear often precedes a bounce.

Volatility Metrics:

Implied Volatility (IV) Percentile: Is the current premium on options extremely high compared to the last 52 weeks? (High IV means an earnings report or big event is coming).

Positioning:

Open Interest (OI) Buildup: Are traders aggressively writing Call options at ₹500? That means ₹500 is a massive resistance wall.

Max Pain Theory: The strike price where option buyers lose the most money and option sellers (institutions) make the most. Stocks often gravitate toward the Max Pain price near expiry.

📰 6. The Macro & Sentiment Analyst (The Economist)
Objective: Understand the environment the stock lives in. A great ship will still sink in a hurricane.
Data Needed: Macroeconomic API feeds, FII/DII data, News NLP Sentiment.

Comprehensive Metrics:

Liquidity & Flows (Crucial for India):

FII / DII Net Activity: Are Foreign Institutional Investors dumping Indian equities this week?

Macro Environment:

Interest Rates (RBI Repo Rate): High rates kill Capital Goods and Real Estate stocks, but help Banking margins.

India VIX: The fear index. If VIX is spiking above 20, the engine should automatically penalize aggressive tech/growth stocks.

Currency (USD/INR): A weakening Rupee is great for IT exporters (TCS, Infosys) but terrible for importers (Paints, Aviation).

Unstructured Sentiment:

FinBERT News Sentiment: Scanning the last 10 news headlines for the ticker and scoring them from -1.0 (Scandal/Fraud) to +1.0 (Blockbuster Earnings/Contract Win).

⚙️ How to Code This (The Scoring Mechanism)
For each of these 6 scripts, you will write a normalization function that maps these wildly different metrics onto a clean 0 to 100 scale.



### Phase 4: The LangChain ReAct Loop (Lead PM)
1. `app/api/v1/routes.py` initializes the LangChain agent (`app/agent/lead_pm.py`).
2. The Agent calls `@tool` functions in `app/agent/tools.py` to fetch the user's profile from Supabase and the 6 Analyst scores.
3. The Agent synthesizes the `0-100` scores against the user's specific constraints (e.g., rejecting a stock with a great Technical score if the Quantitative risk exceeds the user's Conservative profile).

### Phase 5: Output Generation (With Personalization)
The Agent forces the final output into a Pydantic schema. It **must** explicitly justify the decision based on the user's profile.

### Phase 6: Educational Follow-Up (RAG Layer)
If the user replies, *"What is a Put-Call Ratio?"*, the system bypasses the stock analysis pipeline. The Agent calls the RAG tool (`rag/4_retrieval_chain`), searches the Supabase `pgvector` knowledge base, and returns a contextual, jargon-free explanation.

---

## 📂 3. Directory Structure

```text
backend/
├── app/
│   ├── agent/                 # 🧠 The Brain
│   │   ├── __init__.py
│   │   ├── lead_pm.py         # LangChain AgentExecutor loop and PM Prompt
│   │   └── tools.py           # @tool wrappers (calls analysts, DB, and RAG)
│   │
│   ├── api/                   # 🌐 Endpoints
│   │   ├── v1/
│   │   │   ├── dependencies.py
│   │   │   └── routes.py      # POST /analyze, POST /chat
│   │
│   ├── db/                    # 💾 Persistence
│   │   ├── supabase_client.py 
│   │   └── thesis_repo.py     # Stores past LLM decisions for continuity
│   │
│   ├── etl/                   # 📥 Just-In-Time Data Ingestion
│   │   ├── market_fetcher.py  # Fetches APIs (yfinance, Upstox, News)
│   │   └── pipeline.py
│   │
│   ├── models/                # 🏗️ DB Schema / Enums
│   │   ├── enums.py
│   │   └── user.py
│   │
│   ├── rag/                   # 📚 Educational Knowledge Base
│   │   ├── 1_document_loaders/
│   │   ├── 2_embedder/
│   │   ├── 3_vector_store/    # Connects to Supabase pgvector
│   │   └── 4_retrieval_chain/
│   │
│   ├── schemas/               # 🛡️ Pydantic Validation
│   │   ├── request_models.py
│   │   └── response_models.py # Enforces JSON structure for the frontend
│   │
│   ├── scripts/               # 📜 One-off utilities
│   │   └── seed_investor_profile.py
│   │
│   ├── services/              # 🧮 Deterministic Math Layer
│   │   ├── analysts/
│   │   │   ├── fundamental.py 
│   │   │   ├── valuation.py   
│   │   │   ├── technical.py   
│   │   │   ├── quantitative.py
│   │   │   ├── derivative.py  
│   │   │   └── sentiment.py   
│   │   ├── persona_engine.py
│   │   ├── portfolio_normalizer.py
│   │   └── portfolio.py       # Calculates current sector allocations
│   │
│   └── main.py                # FastAPI Application Entry

---
##📜 4. Required Output Schema (Pydantic ResponseModel)
When the lead_pm.py agent resolves a stock query, it MUST return data conforming strictly to this JSON structure:

JSON
{
  "ticker": "RELIANCE.NS",
  "action": "BUY / HOLD / SELL",
  "conviction_score_0_to_100": 78,
  "recommended_allocation_percent": 5.0,
  "analysis_summary": {
    "fundamental": "Strong ROE of 18% and comfortable debt coverage.",
    "technical": "RSI at 42 indicates neutral momentum, crossing 50 EMA.",
    "macro_and_sentiment": "Positive FII inflow and favorable FinBERT news score."
  },
  "personal_justification": "Why this fits YOU: Based on your 'Aggressive Growth' profile and 60-month horizon, this stock's high Beta (1.4) aligns with your risk tolerance. Furthermore, you currently have only 5% exposure to the Energy sector, making this an optimal asset for diversification.",
  "educational_flags": ["Beta", "ROE", "50 EMA"] 
}
(Note: educational_flags are terms the frontend can highlight. If the user clicks them, it triggers the RAG pipeline for an explanation).
---

##🤖 5. Instructions for AI Coding Assistant
Strict Determinism: Never instruct the LLM to calculate RSI, DCF, or Beta. All calculations happen in app/services/analysts/. The LLM only reads the resulting 0-100 scores.

Just-In-Time Fetching: Ensure market_fetcher.py is invoked dynamically via tools.py during the ReAct loop, passing the specific ticker from the user prompt.

Personalization Enforcement: The system prompt in lead_pm.py must strongly instruct the agent to populate the personal_justification field by cross-referencing the Analyst scores with the user_personas data.

Tool Separation: Maintain clear boundaries in tools.py. Create analyze_stock_tool (triggers the 6 analysts) and financial_concept_tutor_tool (triggers the RAG pipeline). The LangChain agent will decide which to use based on whether the user asks for analysis or education.

---


