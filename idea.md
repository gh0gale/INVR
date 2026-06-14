# Stock Analysis Pipeline Blueprint

> Complete specification of Bronze Layer data fetched and Silver Layer metrics calculated for each trading timeframe.

---

## 1. Intraday Analysis

**Config:** `period='5d'`, `interval='5m'`, ~375 candles, horizon: same-day exit

---

### A. Data Fetched (Bronze Layer)

| Source | What is fetched | Cost |
|---|---|---|
| `yfinance` | 5-day 5-minute OHLCV ticks for the ticker | Free, no auth needed |
| `nsepython` | Live circuit breaker limits (upper/lower %) | Free NSE data wrapper |

---

### B. Bronze Payload Generated

| Field | Value |
|---|---|
| `ticker` | e.g. `"ASHOKLEY"` |
| `timeframe` | `"intraday"` |
| `circuit_status` | `"none"` \| `"upper"` \| `"lower"` |
| `price_history` | DataFrame ~375 rows — columns: `Open, High, Low, Close, Volume` (each row = 5 mins) |
| `sector_history` | `None` |
| `fundamentals` | `None` |
| `institutional_activity` | `None` — irrelevant on 5-min scale |

---

### C. Silver Metrics Calculated

| Metric | Inputs from Bronze | Significance |
|---|---|---|
| `sma_20` | `price_history['Close']` | 100-minute moving average. Micro-trend direction; price above = bullish bias for the next 1–2 candles. |
| `sma_50` | `price_history['Close']` | 250-minute average. Intraday structural baseline; acts as a magnet for price on slow days. |
| `sma_200` | — | **Null.** Not enough rows in 5-day 5-min data to compute reliably. |
| `rsi_14` | `price_history['Close']` | 70-minute momentum tracker. RSI >70 = overbought fade zone; <30 = oversold bounce zone for scalps. |
| `atr_14` | `High, Low, Close` | Average ₹ move per 5-min candle. Sets tight dynamic stop-loss (e.g. entry − 1.5×ATR) so the risk per trade is quantified. |
| `volume_avg_20` | `price_history['Volume']` | Baseline 100-min volume. A candle with volume >1.5× this avg confirms a real breakout vs a fake one. |
| `stock_vs_sector_rs` | — | **Null.** Sector correlation doesn't matter on a 5-min scale. |
| `sma_gap_pct` | — | **Null.** Death-cross noise filter is irrelevant intraday. |

> **Primary edge:** Price action + volume confirmation + tight ATR stop. The circuit status is a pre-trade gate — if a stock is in upper circuit, you can't buy; if lower, you can't short. All other fundamentals are noise at this horizon.

---
---

## 2. Swing Analysis

**Config:** `period='6mo'`, `interval='1d'`, ~126 candles, horizon: 5–20 trading days

---

### A. Data Fetched (Bronze Layer)

| Source | What is fetched | Cost |
|---|---|---|
| `yfinance` | 6-month daily OHLCV for the ticker | Free |
| `yfinance` | 6-month daily OHLCV for the sector index (e.g. Nifty Auto for ASHOKLEY). Used to compute relative strength. | Free |
| `nsepython` | Live circuit status. A stock in circuit can't be traded. | Free |
| `yfinance .info` | Lightweight fundamentals: P/E, P/B, Debt-to-Equity, Revenue Growth (TTM) | Free via `ticker.info` dict |
| NSE bulk/block deals | Recent FII/DII activity + bulk/block deal data from NSE website. Signals smart-money positioning. | Free, scrapeable from NSE portal |

---

### B. Bronze Payload Generated

| Field | Value |
|---|---|
| `ticker` | e.g. `"ASHOKLEY"` |
| `timeframe` | `"swing"` |
| `circuit_status` | `"none"` \| `"upper"` \| `"lower"` |
| `price_history` | DataFrame ~126 rows — columns: `Open, High, Low, Close, Volume` |
| `sector_history` | DataFrame ~126 rows — sector index daily close |
| `fundamentals` | Dict: `pe_ratio, pb_ratio, debt_to_equity, revenue_growth_ttm` |
| `institutional_activity` | Dict: `fii_net_activity` (buy/sell ₹Cr last 5 days), `dii_net_activity`, `recent_bulk_deals [ {date, qty, price} ]` |

---

### C. Silver Metrics Calculated — Technical

| Metric | Inputs from Bronze | Significance |
|---|---|---|
| `sma_20` | `price_history['Close']` | 1-month trend baseline. A close above SMA-20 is the minimum trend condition for a swing entry. |
| `sma_50` | `price_history['Close']` | 2.5-month structural support. Pullbacks to SMA-50 while RSI is not oversold = high-probability swing entry. |
| `sma_200` | — | **Null or unreliable.** 126 daily candles technically computable but only ~6 months of history — noisy. |
| `rsi_14` | `price_history['Close']` | 14-day momentum. RSI 40–60 on entry is ideal — not overextended. Used to time entries during pullbacks. |
| `atr_14` | `High, Low, Close` | Daily ATR in ₹. Sets the stop-loss distance (2×ATR below entry) and position size for proper risk management. |
| `volume_avg_20` | `price_history['Volume']` | 20-day average volume. Breakout on 1.5× this volume is a genuine move; less = likely to fail. |
| `stock_vs_sector_rs` | `price_history`, `sector_history` | % return of stock minus % return of sector index over 20 days (1 month). A positive delta means the stock is outperforming its sector. |
| `market_regime` | `sector_history` | Evaluates broader market structure (index close vs 50/200 SMA). "bullish", "bearish", or "neutral". Bearish suppresses bullish swing setups. |
| `sma_gap_pct` | — | **Null.** Death-cross filter is a positional concept. |

---

### D. Additional Silver — Fundamentals Gate (Lightweight)

| Metric | Significance |
|---|---|
| `pe_vs_sector_avg` | Compare stock P/E against sector median. A stock trading at 40% discount to its peers with positive RS = undervalued momentum candidate. |
| `debt_flag` | Boolean: Debt/Equity > 1.5? If yes, avoid swing trades on bad-news catalysts — high-debt stocks can gap down violently. |
| `institutional_bias` | FII + DII net activity over last 5 days: "buyer" (>50), "seller" (< -50), or "neutral". Smart money accumulation during a technical consolidation = strong swing setup. |

> **Primary edge:** Technical momentum + relative strength + smart money confirmation. Fundamentals here are a filter (avoid debt traps, confirm sector context) — not the thesis driver.

---
---

## 3. Positional Analysis

**Config:** `period='1y'`, `interval='1d'`, ~252 candles, horizon: 1–6 months

---

### A. Data Fetched (Bronze Layer)

| Source | What is fetched | Cost |
|---|---|---|
| `yfinance` | 1-year daily OHLCV for the ticker | Free |
| `yfinance` | 1-year daily OHLCV for the sector index. RS over a full year is a meaningful signal. | Free |
| `nsepython` | Circuit status — still useful as a pre-trade gate | Free |
| `yfinance .info` + `.financials` | Full fundamentals: P/E, P/B, EV/EBITDA, Revenue (3 years), Net Profit (3 years), Debt/Equity, Promoter Holding %, ROE, ROCE | Free via yfinance |
| NSE shareholding pattern | Quarterly promoter + FII + DII holding % (last 4 quarters). Trend in promoter holding is a key conviction signal. | Free from NSE / Screener.in scrape |
| Screener.in (scrape) | Historical quarterly financials: Sales growth, Operating profit margin trend, Cash flow from operations | Free public data |

---

### B. Bronze Payload Generated

| Field | Value |
|---|---|
| `ticker` | e.g. `"ASHOKLEY"` |
| `timeframe` | `"positional"` |
| `circuit_status` | `"none"` \| `"upper"` \| `"lower"` |
| `price_history` | DataFrame ~252 rows — 1-year daily OHLCV |
| `sector_history` | DataFrame ~252 rows — sector index daily close |
| `fundamentals` | Dict: `pe, pb, ev_ebitda, roe, roce, debt_to_equity, revenue_3y [ ], net_profit_3y [ ], opm_trend [ ], cfo_3y [ ], promoter_holding_trend [ ]` |
| `institutional_activity` | `None` — quarterly holding % is in fundamentals; no live FII flow needed for multi-month holds |

---

### C. Silver Metrics Calculated — Technical (Supporting Role)

| Metric | Inputs from Bronze | Significance |
|---|---|---|
| `sma_50` | `price_history['Close']` | Medium-term trend filter. Entry only when price is above SMA-50, confirming the trend is intact. |
| `sma_200` | `price_history['Close']` | Macro trend baseline. Price above SMA-200 = bull market structure. Death Cross (50 crossing below 200) = hard rejection signal for new positional entries. |
| `sma_gap_pct` | `sma_50`, `sma_200` | (SMA50 − SMA200) / SMA200 × 100. If gap < −5%, the death cross is real and deep — avoid. If gap is a small −1%, it may be a false signal in a sideways market. |
| `rsi_14` | `price_history['Close']` | Entry timing only — don't buy RSI >75 even if fundamentals are great. Used to wait for a pullback to a better price. |
| `stock_vs_sector_rs` | `price_history`, `sector_history` | 50-day relative strength. A positive delta means the stock is outperforming its sector. |
| `market_regime` | `sector_history` | Evaluates broader market structure (index close vs 50/200 SMA). "bullish", "bearish", or "neutral". Bearish suppresses bullish setups. |
| `sma_20` | — | Computed but **low weight.** Micro-trend noise for a multi-month hold. |
| `atr_14` | — | Computed but **low weight.** Stop-loss on positional trades is based on % drawdown tolerance, not ATR ticks. |

---

### D. Silver Metrics Calculated — Fundamentals (Primary Driver)

| Metric | Inputs from Bronze | Significance |
|---|---|---|
| `revenue_cagr_3y` | `fundamentals['revenue_3y']` | 3-year revenue CAGR. Business growing >15% CAGR consistently = compounding candidate. Flat or declining = red flag regardless of cheap valuation. |
| `profit_cagr_3y` | `fundamentals['net_profit_3y']` | Net profit CAGR must match or exceed revenue CAGR. If revenue grows 20% but profit grows only 5%, margins are compressing — the business is scaling poorly. |
| `opm_trend` | `fundamentals['opm_trend']` | Operating profit margin over 4 quarters. Expanding margins = business gaining pricing power. Contracting = input cost pressure or competition — investigate before buying. |
| `roe_vs_cost_of_capital` | `fundamentals['roe']` | ROE should be >15%. If ROE < 12%, the company earns less than what equity capital costs — value destruction, not creation. |
| `valuation_comfort` | `fundamentals['pe']`, `ev_ebitda` | P/E vs 3-year historical P/E band + EV/EBITDA vs sector. Buying a great business at fair value beats buying a mediocre one cheap. A P/E at 5-year highs with slowing growth = mean reversion risk. |

> **Primary edge:** Fundamental business quality sets the universe; technicals (SMA-200 structure, RS, RSI) purely set the entry timing. Don't enter a fundamentally weak stock just because it "looks good on the chart."

---
---

## 4. Long-Term Analysis

**Config:** `period='5y'`, `interval='1wk'`, ~260 weekly candles, horizon: 2–5+ years

---

### A. Data Fetched (Bronze Layer)

| Source | What is fetched | Cost |
|---|---|---|
| `yfinance` | 5-year weekly OHLCV for the ticker | Free |
| `yfinance` | 5-year weekly OHLCV for the sector index AND Nifty 500 (broad market). Both needed: sector RS + market RS. | Free |
| `yfinance .financials` / `.balance_sheet` / `.cashflow` | 5-year income statement, balance sheet, cash flow statement (annual). Full business quality audit. | Free |
| Screener.in (scrape) | 10-year financial history: Sales, Net Profit, EPS, Dividend, Book Value per share. Context for long-term compounders. | Free public data |
| NSE shareholding pattern | 8-quarter promoter + FII + DII holding trend. Long-term institutional accumulation is a multi-year signal. | Free from NSE portal |
| `yfinance .info` | Market cap, float, dividend yield, 52-week high/low context | Free |

---

### B. Bronze Payload Generated

| Field | Value |
|---|---|
| `ticker` | e.g. `"ASHOKLEY"` |
| `timeframe` | `"long_term"` |
| `circuit_status` | `None` — irrelevant for 2–5 year holds |
| `price_history` | DataFrame ~260 rows — 5-year weekly OHLCV |
| `sector_history` | DataFrame ~260 rows — sector index + Nifty 500 weekly close |
| `fundamentals` | Dict: `income_statement_5y { revenue[], ebit[], net_profit[], eps[] }`, `balance_sheet_5y { total_debt[], equity[], book_value_per_share[] }`, `cashflow_5y { cfo[], capex[], fcf[] }`, `ratios { pe, pb, ev_ebitda, roe_5y[], roce_5y[], dividend_yield, debt_to_equity_trend[] }`, `holding_pattern_8q { promoter[], fii[], dii[] }` |
| `institutional_activity` | `None` — 8-quarter holding trend is in fundamentals; no short-term flow data needed |

---

### C. Silver Metrics Calculated — Technical (Entry Discipline Only)

| Metric | Inputs from Bronze | Significance |
|---|---|---|
| `sma_50` (weekly) | `price_history['Close']` | ~1-year trend on weekly chart. Basic sanity check: don't initiate in a confirmed downtrend. |
| `sma_200` (weekly) | `price_history['Close']` | ~4-year macro trend line. Price above weekly SMA-200 = secular bull market structure. The single most important technical gate for long-term buys. |
| `stock_vs_sector_rs` | `price_history`, `sector_history` | 12-week relative strength. Used to compare final candidates against recent sector performance. |
| `market_regime` | `sector_history` | Evaluates broader market structure (index close vs 50/200 SMA). "bullish", "bearish", or "neutral". Bearish suppresses bullish setups. |
| `sma_20` | — | **Null.** Irrelevant noise for a multi-year hold. |
| `rsi_14` | — | Computed but **nearly irrelevant.** Trying to time entry by RSI on a 5-year hold costs you more than it saves. |
| `atr_14` | — | **Null.** Long-term position sizing is based on portfolio % allocation, not ATR. |
| `sma_gap_pct` | — | **Null** on weekly chart. Weekly death crosses are major structural events, assessed qualitatively. |

---

### D. Silver Metrics Calculated — Fundamentals (The Entire Thesis)

| Metric | Inputs from Bronze | Significance |
|---|---|---|
| `revenue_cagr_5y` | `fundamentals['income_statement_5y']['revenue']` | 5-year revenue CAGR. A true compounder grows revenue >15% CAGR for 5 years through cycles — not just one good year. |
| `eps_cagr_5y` | `fundamentals['income_statement_5y']['eps']` | EPS growth must outpace revenue growth. If revenue grows 20% but EPS grows 8%, dilution or margin collapse is happening. Long-term wealth comes from EPS compounding. |
| `fcf_conversion` | `fundamentals['cashflow_5y']['cfo']`, `capex[]` | Free Cash Flow = CFO − Capex, averaged over 5 years. FCF >60% of net profit is healthy. (Pending implementation in silver layer) |
| `roe_consistency_5y` | `fundamentals['ratios']['roe_5y']` | ROE > 18%. Returns "consistent_moat" if min 5yr ROE (or current) > 18%, else "volatile" or "average". |
| `debt_trajectory` | `fundamentals['balance_sheet_5y']['total_debt']` | Debt/Equity ratio trend over 5 years. Returns "deleveraging" (improving) or "leveraging". |
| `pe_band_vs_growth` | `fundamentals['ratios']['pe']`, `eps_cagr_5y` | Current P/E vs 5-year historical P/E band. Evaluates valuation comfort and growth premium. |

> **Primary edge:** Business quality audit over a full cycle. Technicals only answer: "is now a reasonable time to start buying?" The real question is "will this business be worth 3–5× more in 5 years?" — and that answer lives entirely in the fundamentals.

---

## Summary — What Matters by Timeframe

| | Intraday | Swing | Positional | Long-Term |
|---|---|---|---|---|
| **Technical weight** | 100% | 70% | 30% | 10% |
| **Fundamental weight** | 0% | 30% | 70% | 90% |
| **Key technical signal** | ATR stop + volume spike | SMA-20/50 + RSI entry | SMA-200 structure + death cross | Weekly SMA-200 + 5yr RS |
| **Key fundamental signal** | Circuit status (gate only) | Debt flag + institutional bias | ROE, CFO quality, promoter trend | EPS CAGR, FCF conversion, ROE consistency |
| **Stop-loss basis** | ATR (₹ per candle) | 2×ATR below entry | % drawdown tolerance | Portfolio % allocation |
| **Free data sources** | yfinance, nsepython | yfinance, nsepython, NSE portal | yfinance, nsepython, Screener.in, NSE | yfinance, Screener.in, NSE portal |
