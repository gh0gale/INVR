# Extracted Requirements v2.0
> **Source:** `.agents/PS.md` (Updated)

## 📌 Functional Requirements
### Data Storage & Profiling
- **Layer 1 Profile:** Age, Income Bracket, Monthly Investable Surplus, Self-reported Risk Appetite, Investment Horizon, Primary Goal.
- **Layer 2 Persona:** Risk Score (0-100), Persona Label (Conservative/Balanced/Growth/Aggressive), Diversification Score, Concentration Flags, Scoring Weight Profile.
- **Probabilistic Portfolio Modeling:** Store sector exposure as confidence ranges instead of exact quantities/values.

### Analysis & Market Data
- Calculate **30+ metrics** per stock daily via ETL:
  - **Fundamental:** Trailing 12M EPS, Rev CAGR, Net Profit Margin, ROCE, D/E, FCF.
  - **Technical:** SMA, EMA, RSI, MACD, Bollinger Bands, Volume Ratios.
  - **Valuation:** Sector Median PE comparisons, PEG, Graham number.
  - **Risk:** 1-1y Beta, Volatility, Max Drawdown.
  - **Sentiment:** News Sentiment, Put-Call Ratio, IV, FII flows.
- Track **Staleness Flags** if data >24 hours old.

### Advisory Workflow
- **Gap Detection:** Compare user sector weights against *Ideal Persona Templates*.
- **Scorecard System:** 6 Lenses (Funda, Tech, Val, Quant, Sent, Macro).
- **Dynamic Weighting:** Multiply 6 scores by the `user_personas.scoring_weight_profile` to calculate composite out of 10.
- **Context Override:** Automatically downgrade verdicts (e.g. Buy -> Wait) if `concentration_flag` is tripped for that sector.
- **Trade Setup Calculation:** Compute Entry Zone (support level), Target 1 (resistance), Target 2 (fair value), Stop Loss (below support), and Position Size (based on monthly investable).

## 📌 Non-Functional Requirements
- **Privacy:** Entire matching/scoring process must function perfectly without knowing exact net worth or stock holdings.
- **UX Paradigm - "The User Reacts, Not Types":** 4 Stage Flow (Onboarding > Dashboard > Explore > Act). Primary interface is card-based. Chat is secondary for follow-up only.
- **Education Layer:** Content matched to 3 Literacy Levels (Beginner, Intermediate, Confident). Zero jargon outputs. Use analogies over formulas.

## 📌 Ambiguities / Open Questions
- Is `prefect` necessary right now for workflow execution, or is APScheduler sufficient for Phase 3? (Default: APScheduler).
- How do we specifically calculate the sector weight bounds? E.g., user says "Heavy in IT", how is 40-55% specifically distributed across remaining?
