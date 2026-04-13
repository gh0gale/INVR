# 🧠 AI-Powered Personalized Investment Intelligence & Learning System

> **Project Specification Document (PS.md)**

---

## Table of Contents

1. [Problem Statement](#-1-problem-statement)
2. [Objective](#-objective)
3. [Proposed Solution](#-2-proposed-solution)
4. [Key Features](#-3-key-features)
   - 3.1 [Smart User Profiling](#-31-smart-user-profiling)
   - 3.2 [Privacy-Aware Portfolio Understanding](#-32-privacy-aware-portfolio-understanding)
   - 3.3 [Market Data Intelligence (ETL + Pipelines)](#-33-market-data-intelligence-etl--pipelines)
   - 3.4 [Portfolio Advisory System](#-34-portfolio-advisory-system)
   - 3.5 [Stock Analysis Engine](#-35-stock-analysis-engine)
   - 3.6 [AI Education Layer (RAG-Based)](#-36-ai-education-layer-rag-based)
   - 3.7 [AI Agent (ReAct Framework)](#-37-ai-agent-react-framework)
   - 3.8 [Continuous Monitoring & Alerts](#-38-continuous-monitoring--alerts)
5. [System Architecture](#-4-system-architecture)
6. [Technical Implementation](#-5-technical-implementation)
7. [Data Flow](#-6-data-flow-example)
8. [UX & Interaction Design](#-7-ux--interaction-design)
9. [Key Innovations](#-8-key-innovations)
10. [Constraints & Considerations](#-9-constraints--considerations)
11. [Future Enhancements](#-10-future-enhancements)
12. [Conclusion](#-11-conclusion)

---

## 📌 1. Problem Statement

Retail investors—especially **beginners and intermediate users**—face significant challenges in today's investment landscape:

| Challenge | Description |
|-----------|-------------|
| ❌ **No Personalized Guidance** | Generic advice fails to account for individual financial profiles, risk tolerance, or goals |
| ❌ **Over-reliance on Tips** | Dependence on social media, news, and unverified "hot tips" leads to poor decisions |
| ❌ **Financial Illiteracy** | Difficulty understanding core metrics like PE, PEG, RSI, Moving Averages, etc. |
| ❌ **No Evaluation Framework** | No structured, repeatable way to evaluate whether a stock is worth buying |
| ❌ **Tool Limitations** | Existing tools either require **full portfolio data** (privacy concern) or give **generic, non-personalized advice** |

---

## 🎯 Objective

Build an **AI-powered system** that:

- ✅ **Understands** a user's financial profile and partial portfolio context
- ✅ **Provides** data-driven investment suggestions
- ✅ **Performs** professional-grade stock analysis
- ✅ **Educates** the user alongside recommendations
- ✅ **Works** even with incomplete user data (**privacy-aware design**)

---

## 💡 2. Proposed Solution

A **hybrid AI system** combining:

| Layer | Technology |
|-------|-----------|
| **Data Engineering** | ETL pipelines + automated data ingestion |
| **LLM-Based Reasoning** | Natural language understanding & generation |
| **RAG** | Knowledge retrieval from curated financial content |
| **Rule-Based Financial Logic** | Existing prompt-driven scoring & analysis system |
| **Personalized User Modeling** | Risk profiling, persona classification, portfolio modeling |

### 🧠 Core Philosophy

> *"Not an AI that tells users what to buy,*
> *but an AI that teaches users **how to think like an investor**."*

---

## 🧩 3. Key Features

### 🔹 3.1 Smart User Profiling

Captures and processes user financial context to generate a personalized investor persona.

```
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────────────────────┐
│     👤 INPUT         │     │   ⚙️ PROCESSING       │     │      📊 OUTPUT                │
│                     │     │                      │     │                              │
│ • Age               │ ──▶ │ • Risk score         │ ──▶ │ • "Aggressive Growth         │
│ • Income            │     │   calculation        │     │    Investor"                 │
│ • Monthly invest    │     │ • Investor persona   │     │ • Risk level                 │
│   capacity          │     │   classification     │     │ • Investment strategy        │
│ • Risk appetite     │     │                      │     │   baseline                   │
│ • Investment        │     │                      │     │                              │
│   horizon           │     │                      │     │                              │
│ • Portfolio sectors  │     │                      │     │                              │
│   (optional, rough) │     │                      │     │                              │
└─────────────────────┘     └──────────────────────┘     └──────────────────────────────┘
```

**Key Details:**
- Users provide basic demographic and financial information
- Risk appetite and investment horizon drive persona classification
- Portfolio sector input is **optional** — the system works without it
- Output includes a descriptive persona label, quantified risk level, and a strategy baseline

#### 🗄️ Data Storage Design

User profile data is stored across **two layers** in Supabase:

**Layer 1 — Static Profile** (`user_profiles` table, set at onboarding, rarely changes):

| Field | Type | Description |
|-------|------|-------------|
| `age` | integer | User's age |
| `income_bracket` | enum | Annual income range (e.g. ₹5–10L, ₹10–25L, ₹25L+) |
| `monthly_investable` | integer | Monthly surplus available for investment (in ₹) |
| `risk_appetite` | enum | Self-reported: conservative / moderate / aggressive |
| `investment_horizon_months` | integer | How long they plan to stay invested |
| `primary_goal` | enum | Wealth creation / retirement / child's education / etc. |
| `sector_exposure` | jsonb | Optional: rough sector presence e.g. `{"IT": true, "Banking": true}` |

**Layer 2 — Derived Persona** (`user_personas` table, computed, not user-entered):

| Field | Type | Description |
|-------|------|-------------|
| `risk_score` | float (0–100) | Numeric risk score derived from Layer 1 inputs |
| `persona_label` | string | e.g. "Conservative Income Seeker", "Balanced Growth Investor", "Aggressive Wealth Builder" |
| `preferred_sectors` | jsonb | Inferred from inputs + behavior over time |
| `sector_concentration_flags` | jsonb | Flags where over-exposure is detected |
| `diversification_score` | float (0–10) | Portfolio health score based on known sector spread |
| `scoring_weight_profile` | jsonb | Adjusts analysis lens weights for this user's risk level (see §3.5) |

> **Design Rule:** Exact stock names, quantities, or rupee values are never stored or required. The system functions entirely on sector-level approximations and persona-level signals.

#### 🧮 Risk Score Calculation

The risk score (0–100) is derived using a weighted formula across inputs:

| Input | Weight | Logic |
|-------|--------|-------|
| Investment horizon | 30% | Longer horizon → higher score (can absorb volatility) |
| Self-reported risk appetite | 35% | Direct multiplier: conservative=0.3, moderate=0.6, aggressive=1.0 |
| Age | 20% | Younger age → higher score (more recovery time) |
| Monthly investable surplus | 15% | Higher surplus → slightly higher score (can weather losses) |

**Persona classification thresholds:**

| Risk Score | Persona Label | Strategy Baseline |
|------------|---------------|-------------------|
| 0–30 | Conservative Income Seeker | Large-cap, dividend stocks, debt funds, index ETFs |
| 31–55 | Balanced Growth Investor | Mix of large-cap + select mid-cap, some sector diversification |
| 56–75 | Growth-Oriented Investor | Mid-cap focus, high-growth sectors, moderate volatility tolerance |
| 76–100 | Aggressive Wealth Builder | Small/mid-cap, high-beta, high-growth with risk awareness |

---

### 🔹 3.2 Privacy-Aware Portfolio Understanding

Understands portfolio composition **without requiring exact holdings or amounts**.

| Stage | Details |
|-------|---------|
| **👤 Input** | Natural language descriptions, e.g., *"I have mostly IT and Banking stocks"* |
| **⚙️ Processing** | Probabilistic portfolio modeling, Sector exposure estimation |
| **📊 Output** | *"High concentration in Banking sector"*, *"Low diversification detected"* |

**Design Principles:**
- No exact stock names, quantities, or values required
- Works on **approximate, partial information**
- Sector-level analysis is sufficient for advisory recommendations
- Preserves user privacy while still enabling meaningful insights

#### 📐 Probabilistic Sector Modeling

When a user says *"I have mostly IT and Banking stocks"*, the system maps this to a sector weight distribution with confidence ranges rather than hard numbers:

```
Input: "mostly IT and Banking stocks"

→ IT sector:      40–55% (high confidence)
→ Banking sector: 30–45% (high confidence)
→ Other sectors:  0–20%  (unknown, treated as unallocated)
```

These weights are stored as ranges in `portfolio_models` and used for:
- **Gap detection** — identifying underweighted sectors
- **Concentration flags** — triggering warnings when a sector exceeds a safe threshold
- **Stock suggestion filtering** — prioritizing suggestions from underrepresented sectors

**Concentration thresholds (Indian market context):**

| Sector Weight | Status | System Action |
|--------------|--------|---------------|
| < 20% | Healthy | No flag |
| 20–35% | Moderate | Informational note |
| > 35% | High concentration | Active warning + diversification suggestion |
| > 50% | Dangerous concentration | Strong advisory to reduce |

---

### 🔹 3.3 Market Data Intelligence (ETL + Pipelines)

Automated data engineering pipelines that keep market data current and analysis-ready.

#### 📊 Data Sources

| Source | Data Type |
|--------|-----------|
| **Yahoo Finance** (`yfinance`) | Stock prices, historical data |
| **Financial APIs** | Fundamental metrics (PE, PEG, ROE, etc.) |
| **Sector Benchmarks** | Industry-level comparisons |
| **NSE/BSE Data** | FII/DII flows, open interest, options chain |
| **News APIs** | Headline sentiment for news scoring |
| **RBI / Macro sources** | Repo rate, inflation (CPI/WPI), 10-year bond yield |

#### ⚙️ Computed Metrics — Full Enumeration

All metrics below are computed per stock and stored daily in the `market_data` table.

**Fundamental Metrics:**

| Metric | Description | Why It Matters |
|--------|-------------|----------------|
| Trailing 12M EPS | Earnings per share, last 12 months | Base for PE, PEG |
| Revenue growth YoY | Year-over-year revenue change | Business momentum |
| Revenue CAGR (3Y) | 3-year compounded revenue growth | Sustained growth check |
| Net profit margin | Net profit / revenue | Operational efficiency |
| ROE | Return on equity | Quality of capital use |
| ROCE | Return on capital employed | Broader efficiency |
| Debt-to-equity ratio | Total debt / shareholder equity | Financial health |
| Interest coverage ratio | EBIT / interest expense | Ability to service debt |
| Free cash flow | Operating CF - capex | Earnings quality check |
| Promoter holding % | % of shares held by promoters | Skin-in-the-game signal |
| FII holding trend | Change in FII % over last quarter | Smart money flow |

**Technical Metrics:**

| Metric | Parameters | Signal |
|--------|-----------|--------|
| SMA | 20-day, 50-day, 200-day | Trend direction |
| EMA | 20-day, 50-day | Faster trend signal |
| RSI | 14-period | Overbought (>70) / Oversold (<30) |
| MACD | 12/26/9 standard | Momentum and crossover signals |
| Bollinger Band position | 20-day, 2 std dev | Relative price position |
| Volume ratio | Current / 20-day average | Confirms breakouts |
| 52-week high/low %ile | Current price position in range | Momentum context |
| Support level | Most recent price floor | Stop-loss anchor |
| Resistance level | Most recent price ceiling | Target anchor |

**Valuation Metrics:**

| Metric | Description |
|--------|-------------|
| Current PE | Price / trailing EPS |
| Sector median PE | Median PE of all stocks in same sector |
| PE vs sector | Current PE as % premium/discount to sector |
| PE vs 3Y own history | Current PE vs stock's own historical range |
| PEG ratio | PE / EPS growth rate |
| Price-to-book | Price / book value per share |
| EV/EBITDA | Enterprise value / EBITDA |
| Graham number | √(22.5 × EPS × Book Value) — rough intrinsic value |

**Risk Metrics:**

| Metric | Description |
|--------|-------------|
| Beta (1-year) | Volatility relative to Nifty 50 |
| 30-day rolling volatility | Annualized standard deviation of returns |
| Max drawdown (last bear) | Peak-to-trough decline in most recent market fall |
| Correlation with Nifty | How closely it tracks the index |

**Sentiment & Derivative Metrics:**

| Metric | Description |
|--------|-------------|
| News sentiment score | Negative / Neutral / Positive classification of recent headlines |
| Analyst consensus | Buy / Hold / Sell count from brokerage reports |
| Futures open interest | OI buildup or reduction in NSE futures |
| Put-call ratio (PCR) | Options market's directional bias |
| Implied volatility (IV) | Options-priced expectation of future move |
| FII net futures position | Institutional directional bet |

**Macro Context Metrics (market-level, not stock-level):**

| Metric | Update Frequency | Use |
|--------|-----------------|-----|
| RBI repo rate + direction | Per policy meeting | Adjusts DCF discount rate, sector bias |
| India 10-year bond yield | Daily | Risk-free rate for valuation |
| Nifty 50 trailing PE | Daily | Is the market cheap or expensive overall? |
| India VIX | Daily | Market fear gauge — high VIX = caution |
| CPI / WPI inflation | Monthly | Macro health, RBI stance prediction |
| FII net equity flows | Daily | Broad sentiment of foreign money |

#### 🔄 Pipeline

- **Daily automated updates** via cron jobs (initial) → Prefect (advanced)
- Data validation and quality checks
- Incremental loading for efficiency
- Storage in Supabase (PostgreSQL)
- **Staleness flags** — any metric older than 1 trading day is tagged as stale and excluded from active recommendations until refreshed

---

### 🔹 3.4 Portfolio Advisory System

Analyzes the user's current allocation and recommends adjustments aligned with their risk profile.

| Stage | Details |
|-------|---------|
| **👤 Input** | *"What should I invest in?"* |
| **⚙️ Processing** | Portfolio gap detection, Risk alignment, Diversification logic |
| **📊 Output** | Actionable recommendations |

#### 🔍 Gap Detection Logic

The advisory system compares the user's estimated sector weights against an **ideal allocation template** for their persona:

| Sector | Conservative | Balanced | Growth | Aggressive |
|--------|-------------|---------|--------|-----------|
| Large-cap / Index | 40% | 25% | 15% | 10% |
| Banking & Finance | 20% | 20% | 20% | 15% |
| IT / Technology | 10% | 15% | 20% | 20% |
| Pharma / Healthcare | 10% | 10% | 10% | 5% |
| FMCG / Consumer | 10% | 10% | 5% | 5% |
| Infrastructure / Capital Goods | 5% | 10% | 15% | 20% |
| Gold / Debt ETF | 5% | 10% | 5% | 5% |
| Small/Mid-cap growth | 0% | 0% | 10% | 20% |

Sectors where the user's estimated weight is more than **15% below the template** are flagged as **gap sectors** — these drive stock suggestions in Mode 1.

#### 📋 Stock Selection for Portfolio Suggestions (3–4 picks)

Once gap sectors are identified, the system:

1. Screens all stocks in gap sectors against minimum quality thresholds (fundamental score ≥ 6/10, no red flags)
2. Ranks survivors by composite score **adjusted for user risk profile** (see §3.5 scoring weights)
3. Applies a **timing filter** — removes stocks that are technically overextended (RSI > 72, price > 10% above 50-day MA)
4. Applies a **correlation filter** — avoids suggesting a stock highly correlated (>0.75) with something the user already holds
5. Returns top 3–4 stocks, each with a "why for you" explanation (see §3.6)

**Example Recommendations:**

```
📋 Portfolio Advisory Report
━━━━━━━━━━━━━━━━━━━━━━━━━━

🔸 Add Gold ETF (5-10% allocation)
   → Hedge against equity volatility

🔸 Reduce Banking sector concentration
   → Currently ~40%, recommended ≤25%

🔸 Add Index Fund exposure (Nifty 50 / Sensex)
   → Core portfolio stability

🔸 Consider International diversification
   → Single-country risk mitigation
```

---

### 🔹 3.5 Stock Analysis Engine

> **⭐ Core Differentiator** — Professional-grade, multi-dimensional stock analysis powered by the existing prompt system.

| Stage | Details |
|-------|---------|
| **👤 Input** | *"Analyze HDFC Bank"* |
| **📊 Output** | Comprehensive scorecard with actionable levels |

#### Analysis Dimensions

| Dimension | Focus Areas |
|-----------|-------------|
| 🌍 **Macro Analysis** | GDP, Inflation, Interest Rates |
| 🏭 **Sector Analysis** | Industry Trends, Peer Comparison |
| 📊 **Fundamental Analysis** | Revenue, Profit, ROE, Debt |
| 💰 **Valuation Analysis** | PE, PEG, DCF, Fair Value |
| 📈 **Technical Analysis** | RSI, MACD, Support/Resistance |
| ⚠️ **Risk Scoring** | Volatility, Beta, Sector Risk |
| 📰 **Sentiment & Derivatives** | News sentiment, FII flows, PCR, OI |

#### 🏆 Scoring Framework — How Each Lens Is Scored

Each of the six analysis dimensions produces a sub-score (0–10). These are combined into a **weighted composite score** that varies by user risk profile.

**Sub-score rules:**

**Fundamental Score (0–10):**

| Signal | Points |
|--------|--------|
| Revenue CAGR (3Y) > 15% | +2 |
| Net profit margin expanding YoY | +1.5 |
| ROE > 15% | +1.5 |
| Debt-to-equity < 0.5 (or sector-appropriate) | +1.5 |
| Free cash flow positive and growing | +1.5 |
| Promoter holding > 40% and stable/increasing | +1 |
| Deductions: D/E > 1.5, declining margins, negative FCF | −1 to −3 |

**Technical Score (0–10):**

| Signal | Points |
|--------|--------|
| Price above 50-day and 200-day MA | +2 |
| RSI between 40–65 (healthy zone, not stretched) | +2 |
| MACD bullish crossover in last 5 days | +1.5 |
| Volume on up-days > 20-day average | +1.5 |
| Price within 5% of identified support level | +2 |
| Deductions: RSI > 75 (overbought), price far from support, death cross | −1 to −3 |

**Valuation Score (0–10):**

| Signal | Points |
|--------|--------|
| PE below sector median | +2.5 |
| PEG < 1 | +2.5 |
| Price below Graham number | +2 |
| EV/EBITDA below sector average | +2 |
| Deductions: PE > 2× sector median, PEG > 2 | −1 to −3 |

**Quantitative/Risk Score (0–10):**

| Signal | Points |
|--------|--------|
| Beta < 1.2 (manageable volatility) | +2 |
| Max drawdown in last bear < 30% | +2 |
| Low correlation with user's existing holdings | +2 |
| Sharpe ratio (1Y) > 1.0 | +2 |
| 30-day volatility below sector average | +2 |
| Deductions: Beta > 2, high drawdown history | −1 to −2 |

**Sentiment & Derivative Score (0–10):**

| Signal | Points |
|--------|--------|
| News sentiment: Positive | +2 |
| Analyst consensus: majority Buy | +2 |
| FII futures: net long or increasing | +2 |
| PCR between 0.7–1.2 (balanced options market) | +2 |
| Promoter buying in last quarter | +2 |
| Deductions: negative news, FII selling, high IV spike | −1 to −3 |

**Macro/Sector Score (0–10):**

| Signal | Points |
|--------|--------|
| Sector in uptrend (majority of sector stocks above 50MA) | +3 |
| Sector PE below its own 3Y historical average | +2 |
| RBI policy favorable for sector (e.g. rate cut = good for NBFCs) | +2 |
| India VIX < 18 (calm market) | +2 |
| Market overall PE not stretched (Nifty PE < 22) | +1 |
| Deductions: sector in downtrend, adverse regulation | −1 to −3 |

#### ⚖️ Composite Score Weighting by User Persona

The six sub-scores are combined with persona-adjusted weights:

| Dimension | Conservative | Balanced | Growth | Aggressive |
|-----------|-------------|---------|--------|-----------|
| Fundamental | 35% | 30% | 25% | 20% |
| Valuation | 25% | 20% | 15% | 10% |
| Technical | 10% | 15% | 20% | 25% |
| Quant/Risk | 15% | 15% | 15% | 10% |
| Sentiment/Derivatives | 5% | 10% | 15% | 20% |
| Macro/Sector | 10% | 10% | 10% | 15% |

> **Rationale:** Conservative investors prioritize business quality and price safety (fundamentals + valuation weighted heavily). Aggressive investors are more willing to ride momentum and sentiment signals (technical + sentiment weighted higher).

#### 🔖 Verdict Thresholds

| Composite Score | Verdict | Meaning |
|----------------|---------|---------|
| ≥ 7.5 | **Strong Buy** | High conviction across most dimensions |
| 6.5–7.4 | **Buy** | Good setup, proceed with suggested sizing |
| 5.5–6.4 | **Wait** | Stock is good but timing or valuation not ideal yet |
| 4.0–5.4 | **Weak/Watchlist** | Monitor — not ready for entry |
| < 4.0 | **Avoid** | Fundamental or risk issues present |

> An additional **portfolio context override** applies: even a "Buy" verdict is downgraded to "Wait" if the user's sector exposure in that stock's sector already exceeds the concentration threshold.

#### Output Format

| Component | Description |
|-----------|-------------|
| **Scorecard** | Numerical ratings across all dimensions |
| **Verdict** | **Buy** / **Wait** / **Avoid** with confidence level |
| **Entry Price** | Recommended entry point |
| **Stop Loss** | Downside protection level |
| **Target Price** | Expected upside target(s) |
| **Justification** | Detailed reasoning for each recommendation |
| **"Why For You" section** | Personalized explanation tied to user's portfolio and goals |

#### 📐 Trade Setup Methodology (when verdict is Buy)

When a Buy verdict is reached, the system computes specific, actionable trade parameters:

**Entry Zone:**
- Identifies the nearest **support level** from technical data (a price where the stock has bounced at least twice in recent history)
- Suggests entering within **2–3% of that support**
- If the stock is already in an uptrend above support, uses the most recent **consolidation zone** (tight trading range) as entry

**Stop-Loss:**
- Set just **below the identified support level**, typically 5–8% below entry
- Logic: if price breaks support, the technical thesis is invalidated — exit to preserve capital
- Expressed as both a rupee price and a percentage from entry

**Target 1 (partial exit):**
- Set at the **next resistance level** above entry (price where selling pressure has historically appeared)
- Typically 15–25% above entry
- Recommendation: book **50% of the position** at Target 1

**Target 2 (full exit / hold):**
- Derived from **fundamental fair value** — PE expansion to sector median, or DCF intrinsic value estimate
- Represents the full thesis upside if held over the investment horizon
- Recommendation: hold remaining **50% of position** until Target 2 or thesis change

**Position Sizing:**
- Expressed as a % of the user's `monthly_investable` amount
- Calibrated by: conviction score, sector concentration already held, stock beta

| Condition | Suggested Allocation |
|-----------|---------------------|
| Strong Buy + low sector concentration + low beta | 30–40% of monthly amount |
| Buy + moderate concentration + moderate beta | 15–25% of monthly amount |
| Buy + near concentration limit + high beta | 5–10% of monthly amount (small diversifier) |

**Example Trade Setup Output:**
```
📈 Trade Setup — Infosys (INFY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verdict: Buy  |  Score: 7.4/10  |  Confidence: Moderate-High

Entry Zone:   ₹1,720 – ₹1,750  (near support at ₹1,710)
Stop Loss:    ₹1,610  (−6.5% from entry midpoint)
Target 1:     ₹2,050  (+19%) → book 50% here
Target 2:     ₹2,380  (+38%) → hold rest for full thesis
Position:     ~20% of monthly investable amount

⚠️ Your IT exposure is already moderate (~30%). Keep position small.
```

---

### 🔹 3.6 AI Education Layer (RAG-Based)

Retrieval-Augmented Generation system that educates users about financial concepts **in context**.

| Stage | Details |
|-------|---------|
| **👤 Input** | *"Why does PEG ratio matter?"* |
| **⚙️ Processing** | Retrieve knowledge from vector DB → LLM explanation |
| **📊 Output** | Simple explanation + contextual relevance |

**Example Output:**

```
📚 PEG Ratio Explained
━━━━━━━━━━━━━━━━━━━━━

📖 What is it?
PEG = PE Ratio ÷ Earnings Growth Rate
It adjusts the PE ratio for growth, giving a more complete picture.

🤔 Why does it matter?
A stock with PE of 30 seems expensive. But if earnings are
growing at 35%, the PEG is only 0.86 — potentially undervalued!

📌 Rule of Thumb:
  • PEG < 1  → Potentially undervalued
  • PEG = 1  → Fairly valued
  • PEG > 1  → Potentially overvalued

🔗 In Context:
The stock you're analyzing has a PEG of 0.72, suggesting it
may be undervalued relative to its growth rate.
```

#### 📚 RAG Knowledge Base — Content Specification

The vector database contains financial knowledge written across **three literacy levels**:

| Level | Target User | Description |
|-------|-------------|-------------|
| Beginner | New investors, no finance background | Analogies and plain language only, no formulas |
| Intermediate | Some market awareness | Light formulas with plain interpretation |
| Confident | Regular investors | Full technical definition + nuance |

**Content categories that must be in the knowledge base:**

| Category | Examples |
|----------|---------|
| Metric definitions (3 levels each) | PE, PEG, ROE, ROCE, D/E, RSI, MACD, Beta, Sharpe, EV/EBITDA, FCF, PCR |
| Indian market benchmarks | What is a normal PE for IT / Banking / Pharma / FMCG in India |
| Sector explainers | How interest rate changes affect banking stocks; why pharma is defensive |
| Concept analogies | PE as "years of profit you're paying for"; Beta as "how jumpy the stock is vs the market" |
| Historical examples | Overvalued stocks in 2021 tech run; 2008 banking crash explained simply |
| Trade mechanics | What stop-loss means in plain terms; why profit booking at targets matters |
| Portfolio concepts | Diversification, correlation, concentration risk — all jargon-free |
| Macro concepts | What RBI rate hikes mean for your stocks; how inflation affects markets |

#### 🔗 "Why For You" Personalization — How It Works

When the system explains why a stock was recommended for a specific user, the LLM receives:

```
System prompt context injected:
  - User persona: {persona_label}
  - Risk score: {risk_score}
  - Estimated sector gaps: {gap_sectors}
  - Investment goal: {primary_goal}
  - Stock scorecard: {scorecard_json}
  - RAG-retrieved context: {relevant_knowledge_chunks}

Instruction to LLM:
  "In 2–3 plain sentences, explain why this stock fills a gap
   in this user's portfolio and what role it would play.
   Use no financial jargon. Use everyday analogies where helpful.
   Reference the user's specific situation, not generic advice."
```

**Example "Why For You" output:**
> *"Your portfolio is heavily in IT and Banking, which tend to move together when markets get nervous about tech or interest rates. Infosys being an IT stock would increase that concentration — but right now, it's technically well-positioned and trading at a reasonable price compared to its growth. Given your moderate risk profile, a small allocation here makes sense if you're comfortable with the existing IT exposure."*

The user can then tap **"What does 'technically well-positioned' mean?"** and the RAG system explains RSI, moving averages, and support levels in beginner-friendly terms — in the context of that exact stock.

**Knowledge Sources:**
- Curated financial education content
- Investopedia-style explanations
- Indian market-specific concepts (SEBI regulations, NSE/BSE specifics)
- Sector cycle guides (rate sensitivity, macro linkages)
- Stored as embeddings in FAISS / ChromaDB vector database

---

### 🔹 3.7 AI Agent (ReAct Framework)

An intelligent orchestrator that **dynamically decides** which tools and analysis to invoke based on user queries.

```
                        ┌──────────────┐
                        │  User Query  │
                        └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │  🤖 ReAct    │
                        │    Agent     │
                        └──┬──┬──┬──┬──┘
                           │  │  │  │
            ┌──────────────┘  │  │  └──────────────┐
            │        ┌───────┘  └───────┐          │
     ┌──────▼──────┐ ┌──────▼──┐ ┌──────▼──┐ ┌────▼───────┐
     │📊 Market    │ │💼 Port- │ │📚 RAG   │ │🔍 Stock    │
     │   Data Tool │ │ folio   │ │ System  │ │  Analysis  │
     └──────┬──────┘ └────┬────┘ └────┬────┘ └────┬───────┘
            └──────────────┴──────────┴────────────┘
                               │
                        ┌──────▼───────┐
                        │ 📝 Final     │
                        │   Response   │
                        └──────────────┘
```

**Agent Capabilities:**

| Decision | Trigger |
|----------|---------|
| Fetch market data | User asks about current prices, trends |
| Analyze portfolio | User asks about allocation, diversification |
| Use RAG | User asks conceptual / educational questions |
| Run stock analysis | User asks to evaluate a specific stock |
| Combine tools | Complex queries requiring multiple data sources |

---

### 🔹 3.8 Continuous Monitoring & Alerts

Background monitoring system that tracks portfolio-relevant events and notifies users proactively.

| Stage | Details |
|-------|---------|
| **⚙️ Processing** | Track price changes, check stop-loss triggers, monitor portfolio risk levels |
| **📊 Output** | Real-time alerts and notifications |

**Alert Types:**

| Alert | Trigger |
|-------|---------|
| 🔴 **Stop Loss Hit** | *"HDFC Bank hit your stop loss at ₹1,450"* |
| 🟡 **Risk Increase** | *"Portfolio risk increased due to Banking sector decline"* |
| 🟢 **Target Reached** | *"TCS reached your target price of ₹4,200"* |
| 🔵 **Opportunity** | *"IT sector showing oversold conditions — potential entry"* |

---

## 🏗️ 4. System Architecture

### 🔄 High-Level Flow

```
User Input
   ↓
User Profile + Approx Portfolio Model
   ↓
Market Data Pipelines (ETL)
   ↓
Agent (ReAct)
   ↓           ↓           ↓
Portfolio    Market       RAG
Analyzer    Data Svc    Knowledge
   ↓           ↓           ↓
   └─────────────┼─────────────┘
                 ↓
   LLM Reasoning Engine
                 ↓
   Recommendations + Education
                 ↓
   (Optional) Stock Analysis Engine
                 ↓
   Final Output to User
```

### 📐 Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React.js)                           │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐              │
│  │ Dashboard │  │  Chat UI │  │ Portfolio  │  │ Analysis │              │
│  │   View   │  │          │  │   View    │  │  Reports │              │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  └────┬─────┘              │
│       └──────────────┼──────────────┼──────────────┘                    │
│                      │         REST API / WebSocket                     │
└──────────────────────┼──────────────────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────────────────┐
│                  BACKEND (FastAPI + Uvicorn)                            │
│                      │                                                  │
│  ┌───────────────────▼───────────────────┐                              │
│  │          🤖 ReAct Agent               │                              │
│  │     (LangChain / Custom Agent)        │                              │
│  └──┬────────┬────────┬────────┬─────────┘                              │
│     │        │        │        │                                        │
│  ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──────┐                                 │
│  │User │ │Mkt  │ │RAG  │ │Analysis │                                  │
│  │Prof.│ │Data │ │Sys. │ │Engine  │                                   │
│  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──────┘                                  │
│     │       │       │       │                                          │
└─────┼───────┼───────┼───────┼──────────────────────────────────────────┘
      │       │       │       │
┌─────▼───────▼───────▼───────▼──────────────────────────────────────────┐
│                      DATA LAYER                                        │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌────────────┐           │
│  │ Supabase │  │  yfinance │  │ FAISS /  │  │  OpenAI /  │           │
│  │  (PgSQL) │  │  (Market) │  │ ChromaDB │  │  HF / LLM  │           │
│  └──────────┘  └───────────┘  └──────────┘  └────────────┘           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ 5. Technical Implementation

### 🖥️ Frontend

| Technology | Purpose |
|------------|---------|
| **React.js** | Component-based UI framework |
| **Tailwind CSS** | Utility-first styling |
| **Chart.js / Recharts** | Data visualization (stock charts, portfolio pie charts) |

### ⚙️ Backend

| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async API framework |
| **Uvicorn** | ASGI server |
| **Pydantic** | Data validation and serialization |

### 🗄️ Database — Supabase (PostgreSQL)

| Table | Stores |
|-------|--------|
| `user_profiles` | Age, income, risk appetite, investment horizon |
| `user_personas` | Computed risk score, persona label, scoring weight profile |
| `user_preferences` | Notification settings, display preferences |
| `chat_history` | Conversation logs with AI |
| `portfolio_models` | Approximate portfolio sector allocations (as weight ranges) |
| `market_data` | Cached stock data and all computed metrics (updated daily) |
| `sector_benchmarks` | Sector-level PE medians, concentration thresholds, macro linkages |
| `macro_context` | RBI rate, bond yield, India VIX, Nifty PE — updated per event |
| `alerts` | Active monitoring rules and triggered alerts |

### 📊 Data Engineering

| Technology | Purpose |
|------------|---------|
| **Python** (`pandas`, `numpy`, `ta`) | Data processing, transformation, technical indicator computation |
| **yfinance** | Market data ingestion |
| **Cron Jobs** | Initial scheduled pipeline execution |
| **Prefect** | Advanced workflow orchestration (future) |

### 🤖 LLM Layer

| Technology | Purpose |
|------------|---------|
| **OpenAI API** | Primary LLM for reasoning and generation (initial) |
| **Hugging Face / Ollama** | Open-source alternatives (optional, cost optimization) |

### 📚 RAG System

| Technology | Purpose |
|------------|---------|
| **sentence-transformers** | Text embedding generation |
| **FAISS** | Vector similarity search (lightweight, local) |
| **ChromaDB** | Alternative vector DB (persistent, metadata-rich) |

### 🧠 Agent Framework

| Technology | Purpose |
|------------|---------|
| **LangChain (ReAct)** | Primary agent framework with tool-use capabilities |
| **Custom Tool-Based Agent** | Alternative lightweight implementation |

### 🔐 Authentication

| Technology | Purpose |
|------------|---------|
| **Supabase Auth** | User registration, login, session management |

### 🚀 Deployment

| Component | Platform |
|-----------|----------|
| **Frontend** | Vercel |
| **Backend** | Render / Railway |
| **Database** | Supabase (managed PostgreSQL) |

---

## 📊 6. Data Flow (Example)

### Example Query: *"Should I invest in this stock?"*

### Step-by-Step Breakdown

#### Step 1 — Load User Context

```
👤 User asks: "Should I invest in HDFC Bank?"
         │
         ▼
┌─────────────────┐     ┌────────────────────────────────────────────┐
│   Supabase DB   │ ──▶ │ Profile: Moderate risk (score: 52), 5yr    │
│                 │     │ Persona: Balanced Growth Investor           │
│                 │     │ Portfolio: Banking ~40%, IT ~30%            │
│                 │     │ Scoring weights: Fundamental 30%, Tech 15%  │
└─────────────────┘     └────────────────────────────────────────────┘
```

#### Step 2 — Fetch Market Data

```
┌──────────────┐     ┌──────────────────────────────────────────────────┐
│   yfinance   │ ──▶ │ Price, PE (22x), Sector PE median (18x),         │
│   + APIs     │     │ PEG (1.1), RSI (64), 50-day MA (₹1,610),         │
│              │     │ Beta (0.9), News sentiment (Neutral),             │
│              │     │ FII trend (slight selling), PCR (1.3)            │
└──────────────┘     └──────────────────────────────────────────────────┘
```

#### Step 3 — Run Analysis Engine

```
┌──────────────────┐     ┌──────────────────────────────────────────────┐
│ Analysis Engine  │ ──▶ │ Fundamental: 7.2 | Technical: 6.1            │
│ (Scoring System) │     │ Valuation: 5.8   | Quant/Risk: 7.0           │
│                  │     │ Sentiment: 5.0   | Macro: 6.5                │
│                  │     │ ─────────────────────────────────────        │
│                  │     │ Composite (Balanced weights): 6.4/10         │
│                  │     │ Verdict: Wait                                │
│                  │     │ Reason: Valuation + FII selling              │
└──────────────────┘     └──────────────────────────────────────────────┘
```

#### Step 3a — Portfolio Context Override Check

```
┌──────────────────────┐     ┌───────────────────────────────────────────┐
│ Concentration Check  │ ──▶ │ Banking exposure: ~40% (above 35% flag)   │
│                      │     │ Override: even if Buy, → downgrade to Wait │
└──────────────────────┘     └───────────────────────────────────────────┘
```

#### Step 4 — Retrieve Knowledge (RAG)

```
┌──────────────┐     ┌────────────────────────────────────────────────────┐
│  Vector DB   │ ──▶ │ PE context: "Banking sector PE usually 14–20x.     │
│  (FAISS)     │     │  HDFC at 22x is slightly premium. Not overvalued,  │
│              │     │  but not cheap either."                            │
│              │     │ Concentration: "40% in one sector increases risk   │
│              │     │  when that sector faces headwinds."                │
└──────────────┘     └────────────────────────────────────────────────────┘
```

#### Step 5 — Generate Response

```
┌──────────────┐     ┌──────────────────────────────────────────────────────────┐
│  LLM Engine  │ ──▶ │ "HDFC Bank scores 6.4/10 — a fundamentally sound         │
│  (OpenAI)    │     │  business, but two things give us pause right now.        │
│              │     │  First, your portfolio already has ~40% in Banking,       │
│              │     │  which is above the safe zone. Adding more concentrates   │
│              │     │  your risk in one sector. Second, foreign investors        │
│              │     │  have been lightly selling banking stocks lately.          │
│              │     │  The stock itself is fairly priced — not expensive,        │
│              │     │  but not a bargain either. Our suggestion: add this        │
│              │     │  to your watchlist. If Banking exposure reduces or         │
│              │     │  price dips to ₹1,580–1,600, it becomes a stronger buy." │
└──────────────┘     └──────────────────────────────────────────────────────────┘
```

### Summary Table

| Step | Action | Data Used | Output |
|------|--------|-----------|--------|
| **1. Load User Context** | Fetch profile + portfolio + persona | Supabase DB | Risk score, persona weights, sector exposure flags |
| **2. Fetch Market Data** | Pull latest fundamentals & technicals | yfinance + computed metrics | All 30+ metrics per stock + macro context |
| **3. Run Analysis Engine** | Multi-dimensional stock scoring | All financial data | Per-lens scores, composite score, raw verdict |
| **3a. Context Override** | Check portfolio concentration | Portfolio model | Upgrade/downgrade verdict if concentration exceeded |
| **4. Retrieve Knowledge (RAG)** | Contextual explanations | Vector DB embeddings | Plain-English metric explanations, relevant educational content |
| **5. Generate Response** | Synthesize personalized recommendation | All above + user profile | Recommendation + justification + "why for you" + learning content |

---

## 🖥️ 7. UX & Interaction Design

### 🎯 Design Principle: The User Reacts, Not Types

The system is designed so that the user **spends most of their time reading, learning, and deciding** — not typing or configuring. The AI surfaces relevant information proactively; the user's role is to engage with it.

### 📱 Four-Stage Session Flow

```
┌─────────────────┐    ┌─────────────────────────┐    ┌──────────────────────────┐    ┌────────────────────┐
│   Stage 1       │    │   Stage 2               │    │   Stage 3                │    │   Stage 4          │
│   Onboarding    │ →  │   Dashboard             │ →  │   Explore                │ →  │   Act              │
│   (once, ~3min) │    │   (default session view)│    │   (any stock, deep dive) │    │   (trade setup)    │
└─────────────────┘    └─────────────────────────┘    └──────────────────────────┘    └────────────────────┘
```

#### Stage 1 — Onboarding (one-time)
A guided 5–7 question flow (not a form dump) that collects the user's profile conversationally. Questions are presented one at a time with tap-to-select options where possible. Takes ~3 minutes. At the end, the system shows the user their generated persona and explains what it means for how the system will work for them.

#### Stage 2 — Dashboard (default landing view)
Every time the user opens the app, they see:
- **Portfolio health card** — diversification score, any active concentration warnings
- **3–4 personalized pick cards** — each showing: stock name, sector, verdict badge (Buy/Wait/Avoid), one-line "why for you" summary, and a score indicator
- **Search bar** — to look up any specific stock instantly
- **Market pulse strip** — India VIX, Nifty PE, RBI stance in one line

The picks are refreshed daily after market close. The user does not need to ask for them.

#### Stage 3 — Explore (stock deep-dive)
When the user taps a pick card or searches a stock:
- Full scorecard displayed (per-lens scores, visual indicators)
- Verdict with confidence level
- "Why for you" section — personalized paragraph
- Expandable "What does this mean?" for each metric — powered by RAG, beginner-friendly
- If verdict is Buy: Trade Setup section appears (see Stage 4)
- Chat input available at bottom: *"Ask anything about this stock"*

#### Stage 4 — Act (trade setup)
If the user decides to proceed:
- Entry zone, stop-loss, and targets displayed clearly
- Position sizing suggestion (in ₹ terms, based on their monthly investable amount)
- One-tap "Add to Watchlist" to track the stock
- Reminder: *"This is educational — please verify before placing orders on your broker app"*

### 💬 Chat — On Demand Only
The chat interface is not the primary mode of interaction. It is accessible from any screen and serves two purposes:
- **Concept questions:** *"What is RSI?"*, *"Why does beta matter?"* → RAG-powered jargon-free answer
- **Follow-up analysis:** *"Compare this with ICICI Bank"*, *"What if I only have ₹5,000 to invest?"* → Agent-powered response

This keeps the experience fast and non-intimidating for users who don't want to type.

---

## 🧠 8. Key Innovations

### ✅ Privacy-Aware AI

| Feature | Benefit |
|---------|---------|
| Works without full portfolio disclosure | Users maintain financial privacy |
| Probabilistic sector modeling from natural language | No exact holdings required |
| Approximate risk assessment | Meaningful insights from partial data |

### ✅ Hybrid Intelligence

| Component | Role |
|-----------|------|
| **Rule-Based Logic** | Deterministic financial calculations (PE, RSI, scoring) |
| **LLM Reasoning** | Natural language understanding, synthesis, explanation |
| **RAG Retrieval** | Grounded, factual knowledge augmentation |

### ✅ Professional-Grade Decision Framework

| What professionals do | How this system replicates it |
|----------------------|-------------------------------|
| Multi-lens analysis (fundamental + technical + valuation + quant + derivatives + sentiment) | Six scored dimensions, each with explicit rules |
| Weight signals by conviction and context | Persona-adjusted scoring weights |
| Never buy a good stock at a bad time | Technical timing score + RSI/MA filters |
| Consider existing portfolio before adding | Concentration override + correlation filter |
| Give precise, actionable trade levels | Support/resistance-based entry, SL, and targets |
| Size positions by conviction and risk | Position sizing formula tied to monthly investable |

### ✅ Education-First Design

| Principle | Implementation |
|-----------|----------------|
| Every recommendation includes explanation | Users learn *why*, not just *what* |
| Contextual learning | Concepts explained in the context of user's actual query |
| Progressive complexity | Beginner-friendly defaults with deep-dive options |
| No jargon in outputs | RAG retrieves appropriate literacy-level explanation per user |
| Analogies over formulas | PE explained as "years of profit you're pre-paying for", not a formula |

### ✅ Modular System

| Mode | Description |
|------|-------------|
| **🟢 Light Mode** | Quick suggestions, portfolio tips, market overview |
| **🔵 Deep Mode** | Full stock analysis, comprehensive scorecard, detailed justification |

---

## ⚠️ 9. Constraints & Considerations

### 🚨 Regulatory Compliance

> **CRITICAL**: This system is **NOT a SEBI-registered investment advisor**. All outputs must be treated as **educational and informational only**.

| Constraint | Mitigation |
|------------|------------|
| **Not SEBI-registered** | Clear disclaimers on every recommendation |
| **No direct "Buy" without justification** | Every suggestion includes detailed reasoning |
| **Data accuracy** | Multiple source verification, data freshness indicators |
| **Market volatility** | Timestamped analysis, staleness warnings |
| **User misinterpretation** | Educational framing, risk warnings, confidence levels |

### Required Disclaimers

```
⚠️ DISCLAIMER: This tool is for educational and informational purposes only.
It does not constitute financial advice. Always consult a SEBI-registered
investment advisor before making investment decisions. Past performance
does not guarantee future results.
```

---

## 🚀 10. Future Enhancements

| Phase | Enhancement | Description |
|-------|-------------|-------------|
| **Phase 2** | 📊 Portfolio Simulation | "What-if" scenarios for portfolio changes |
| **Phase 2** | 🔙 Backtesting Engine | Test strategies against historical data |
| **Phase 3** | 🤖 Reinforcement Learning | Adaptive personalization based on user feedback |
| **Phase 3** | 🔔 Real-Time Alerts System | Push notifications for price triggers and market events |
| **Phase 4** | 📱 Mobile App | Native iOS/Android app for on-the-go access |
| **Phase 4** | 🌐 Multi-Market Support | Extend beyond Indian markets (US, EU, Crypto) |
| **Phase 5** | 🤝 Social Features | Anonymous portfolio comparisons, community insights |
| **Phase 5** | 📄 Tax Optimization | Capital gains planning and tax-loss harvesting suggestions |

---

## 🏁 11. Conclusion

This project demonstrates a comprehensive, production-grade system combining:

| Competency | Demonstrated By |
|------------|-----------------|
| **End-to-End Data Engineering** | ETL pipelines, automated data ingestion, 30+ computed metrics per stock |
| **AI System Design** | LLM integration, RAG architecture, agentic workflows |
| **Real-World Finance Application** | Six-lens stock analysis, portfolio advisory, trade setup methodology |
| **Explainability & Education** | Every decision justified, concepts taught in context at the right literacy level |
| **Privacy-Conscious Design** | Works with partial data, probabilistic sector modeling, no full portfolio disclosure needed |
| **Modular Architecture** | Independently deployable components, scalable design |
| **Professional-Grade Intelligence** | Scoring framework, persona-adjusted weights, concentration overrides, position sizing |

> *The goal is not to replace financial advisors, but to **democratize investment intelligence** — making professional-grade analysis and education accessible to every retail investor.*

---

> **Document Version**: 2.0
> **Last Updated**: April 2026
> **Status**: Specification Complete — Ready for Development