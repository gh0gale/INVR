# 🔬 System Audit Report — FinAI (Algorithmic Portfolio Analyzer Engine)
**Date:** 2026-06-20
**Auditor:** Claude Opus 4.6 (Senior Principal Engineer Mode)
**Codebase Location:** `c:\codes\INVR\INVR`
**Previous Audit:** 2026-06-16

---

## 📊 Executive Summary

FinAI has evolved significantly since the initial audit on 2026-06-16. The system has gained a **complete self-improving feedback loop** through three new Engine Room scripts — a nightly prediction grader, a weekly statistical drift analyzer, and a historical simulation backfiller — orchestrated via GitHub Actions CI/CD. The core financial logic has received targeted fixes: the death cross gate now uses `abs()` for gap comparison, the debt flag implements dual-format detection, FCF conversion is now computed in the Silver Layer, and the `ratios` sub-dictionary is populated in the fundamentals fetcher. The `memory_service.py` now correctly uses the centralized `supabase_admin` client. However, **critical security issues remain unresolved** — the hardcoded `test_user_id` in the tutor endpoint, missing authentication on analytics and tutor routes, and absent CORS middleware are all still present. The Engine Room scripts, while architecturally sound, have their own set of issues: fixed ±5% grading thresholds instead of ATR-based targets, partial gate evaluation in the simulator, and only 2 of 10+ possible drift checks implemented. The `secular_trend` gate bug (WARN immediately overwritten to PASS) also persists.

**Overall Health: Improved — Solid Foundation with Critical Security Debt**

### Changes Since Last Audit (2026-06-16)

| Category | Items Added/Fixed |
|---|---|
| **New Components** | `scripts/grade_ledger.py`, `scripts/analyze_drift.py`, `scripts/simulate_live_history.py`, `.github/workflows/engine_room.yml` |
| **New Database Objects** | `threshold_insights` table, `actual_outcome`/`max_favorable_excursion`/`max_adverse_excursion` columns on `algorithmic_ledger` |
| **Bug Fixes Applied** | Death cross `abs()` fix, debt flag dual-check, FCF conversion computation, `ratios` sub-dict population, memory service client consolidation |
| **Still Open** | P5-01 (hardcoded user ID), P3-01/P3-02 (no auth), P4-01 (no CORS), secular_trend PASS overwrite, `ledger_service.py` standalone client |

---

## 🚨 Critical Issues (Fix Immediately)

1. **[P5-01]** Hardcoded `test_user_id` in production tutor endpoint bypasses all authentication — any user's chat is saved under a fixed UUID ([tutor.py:37](file:///c:/codes/INVR/INVR/backend/app/api/routes/tutor.py#L37))

## ⚠️ High Priority Issues (Fix Before Launch)

3. **[P3-01]** Analytics endpoint has **no authentication** — `process_pipeline` doesn't use `Depends(get_current_user_id)`, allowing any unauthenticated caller to run the full pipeline ([analytics.py:12-13](file:///c:/codes/INVR/INVR/backend/app/api/routes/analytics.py#L12-L13))
4. **[P3-02]** Tutor endpoint has **no authentication** — same issue as analytics ([tutor.py:13](file:///c:/codes/INVR/INVR/backend/app/api/routes/tutor.py#L13))
5. **[P4-01]** No CORS middleware configured on FastAPI — the API accepts requests from any origin ([main.py](file:///c:/codes/INVR/INVR/backend/main.py))

## 🔶 Medium Priority Issues (Fix Soon)

6. **[P0-06]** `redis` dependency declared in `pyproject.toml` (line 17) but never imported or used anywhere in the codebase


## 💡 Optimization Opportunities (Improve Over Time)

10. **[P0-08]** `pyproject.toml` uses `>=` version pinning on all dependencies — in production, pin exact versions or use lock file for reproducibility
11. **[P2-10]** No inflation adjustment in any projection — future value calculations should account for inflation but none exists
12. **[P2-11]** No Monte Carlo simulation or probabilistic modeling — all projections are deterministic single-path
13. **[P4-05]** No prompt versioning — prompt changes are invisible with no rollback capability
14. **[P4-06]** No LLM response caching — identical ticker/timeframe/profile combinations re-invoke the full LLM pipeline
17. **[P9-02]** No accessibility considerations — no frontend exists yet but the API responses contain no semantic structure for screen readers
18. **[P9-04]** MD5 used for profile version hashing — cryptographically broken, should use SHA-256 ([profile.py:44](file:///c:/codes/INVR/INVR/backend/app/schemas/profile.py#L44))
19. **[P5-03]** `Settings` class uses `os.getenv()` defaults alongside `pydantic_settings.BaseSettings` — the pydantic settings pattern should handle env loading itself, the manual `load_dotenv()` + `os.getenv()` is redundant and can cause precedence conflicts ([config.py:1-13](file:///c:/codes/INVR/INVR/backend/app/config.py#L1-L13))
20. **[P3-06]** Frontend directory is empty — no UI exists

---

## 📋 Detailed Findings by Phase

### Phase 0: System Discovery

**Tech Stack Detected:**
| Component | Technology |
|---|---|
| Language | Python 3.14+ |
| Backend | FastAPI 0.136.3+ |
| Orchestration | LangGraph 1.2.4+, LangChain Core 1.4.6+ |
| LLM | Ollama (llama3.1, local) via langchain-ollama |
| Data Processing | Pandas 3.0.3+, NumPy (transitive) |
| Validation | Pydantic 2.13.4+, pydantic-settings 2.14.1+ |
| Database | Supabase (PostgreSQL + Auth) |
| Market Data | yfinance 1.4.1+, nsepython 2.97+ |
| Cache | Local filesystem JSON (Redis declared but unused) |
| Server | uvicorn 0.49.0+ |
| CI/CD | GitHub Actions (engine_room.yml) |

**Folder Structure Assessment:**
- `backend/app/` — Properly separated into `api/`, `schemas/`, `services/`, `pipeline/`, `integrations/`, `tools/`
- `backend/config/` — Gate thresholds correctly externalized
- `backend/scripts/` — **NEW:** Three Engine Room scripts for grading, drift analysis, and historical simulation
- `.github/workflows/` — **NEW:** CI/CD workflow for automated maintenance
- `frontend/` — **Empty directory**, no UI code exists
- Separation of concerns is **generally clean**: routes → services → integrations is respected
- **Improvement since last audit**: `memory_service.py` now uses centralized `supabase_admin` from `database.py` instead of creating its own client
- **Remaining violation**: `ledger_service.py` still creates its own Supabase client instead of using `database.py`

**Orphaned/Unused:**
- `redis` package in `pyproject.toml` — never imported
- `debt_equity_max`, `roe_min`, `max_pe` in `gate_thresholds.py` — `debt_equity_max` is now used in `silver_service.py` (dual-check), `roe_min` used in positional path, `max_pe` used in long-term valuation gate (**FIXED since last audit**)
- Several SilverMetrics schema fields are declared but never populated: `cfo_vs_net_profit`, `promoter_holding_trend`, `book_value_growth`, `promoter_conviction_trend`, `dividend_consistency`

---

### Phase 1: Data Layer

**Data Sources Identified:**
1. yfinance — OHLCV history, fundamentals, financial statements, news
2. nsepython — Circuit breaker status
3. Supabase — User profiles, chat sessions, semantic profiles, algorithmic ledger, threshold insights
4. Ollama — LLM inference (local)
5. Local filesystem — Cache layer

**Key Issues:**
- Institutional activity data is **entirely fabricated** then used in swing bias calculation
- Circuit status logic has `lower = upper * 0.9` fallback which is a rough approximation, not a precise circuit limit lookup
- Book value per share is **hardcoded mock data** `[100, 110, 125, 140, 160]`
- Sector P/E median is a **static 25.0**
- Cache keys now use normalized ticker format (appends `.NS` in `bronze_service.py` before building cache key) — **IMPROVED since last audit**
- The `ratios` sub-dictionary is now populated with basic fields — **FIXED since last audit**, but `roe_5y` and `debt_to_equity_trend` arrays are empty placeholders

---

### Phase 2: Financial Logic & Mathematics

**CAGR Calculation** ([silver_service.py:8-20](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L8-L20)):
- Formula: `(end_val / start_val) ** (1 / periods) - 1` — **Correct** for positive values
- Guards: empty list, <2 elements, start ≤ 0, end ≤ 0 → returns None
- **Still vulnerable**: When `start_val > 0` and `end_val > 0` but the ratio produces an edge case in fractional exponentiation (very unlikely but theoretically possible)

**RSI Calculation** ([silver_service.py:55-60](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L55-L60)):
- Uses Wilder's smoothing (EWMA with alpha=1/14) — **Correct**
- Adds `1e-9` epsilon to prevent division by zero — **Correct**

**ATR Calculation** ([silver_service.py:63-68](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L63-L68)):
- True Range = max(H-L, |H-Cprev|, |L-Cprev|) — **Correct**
- Uses EWMA smoothing — **Correct**

**FCF Conversion** ([silver_service.py:161-170](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L161-L170)):
- **NEW since last audit** — now implemented
- Formula: `Σ(CFO - Capex) / Σ(Net Profit)` over the minimum available years — **Correct**
- Guards: checks for non-empty lists and `total_np > 0` — **Correct**

**Debt Flag Dual-Check** ([silver_service.py:109-110](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L109-L110)):
- **IMPROVED since last audit**: Now handles both percentage format (`de > TH["debt_equity_max"] * 100`) and ratio format (`0 < de < 10 AND de > TH["debt_equity_max"]`)
- This is a pragmatic solution to yfinance's inconsistent D/E format

**Death Cross Gap Check** ([gold_service.py:96-105](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L96-L105)):
- **FIXED since last audit**: Now uses `abs(silver.sma_gap_pct) > TH["death_cross_gap_pct"]` to correctly compare the magnitude regardless of sign
- When `sma_50 < sma_200`, the gap is negative, but `abs()` correctly extracts the severity

**Trade Setup Math** ([gold_service.py:250-283](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L250-L283)):
- Entry zone: `price ± 0.5*ATR` — Reasonable
- Stop loss: `price - multiplier*ATR` — **Correct**
- Position sizing: `(capital * 2%) / risk_distance` — **Correct** Kelly-adjacent formula
- Risk-reward: `(target - price) / risk_distance` — **Correct**
- **Remaining issue**: `risk_distance = max(p - stop_loss, 0.01)` — the 0.01 floor is an absolute value in INR, not proportional. For a ₹2,000 stock, 0.01 INR floor would create an absurdly large position size if ATR somehow collapsed to zero

**Confidence Score** ([gold_service.py:231-244](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L231-L244)):
- **FIXED since last audit**: Now uses weighted scoring with `GATE_WEIGHTS` dictionary
- Formula: `50 + (passed_weight / total_weight * 45)` — Range 50-95%
- Weights correctly differentiate gate severity: circuit/death_cross (3.0) > secular_trend/eps_growth/fcf_quality/valuation (2.0) > volume/trend/sector (1.5) > rsi/revenue_growth (1.0)

**Secular Trend Gate Bug** ([gold_service.py:118-122](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L118-L122)):
- **Still broken**: When `price < sma_200`, the gate is set to WARN on line 120, then immediately overwritten to PASS on line 122
- This makes the long-term secular trend gate completely non-functional — it always passes regardless of price position relative to 200-week SMA

**ROE Consistency Fallback** ([silver_service.py:174-182](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L174-L182)):
- **Improved logic**: First checks `roe_5y` array if available, then falls back to single-year ROE
- **Potential issue**: The fallback condition `roe_val > 0.18 or roe_val > 18.0` handles both decimal (0.18) and percentage (18.0) formats, which is correct given yfinance's inconsistency, but the `or` means `roe_val > 0.18` always triggers first, making the `> 18.0` branch redundant

---

### Phase 3: System Cohesion

**End-to-End Flow Trace (Analytics):**
1. `POST /api/v1/analytics/process` → `analytics.py` (no auth) → builds initial state dict
2. `pipeline_graph.ainvoke()` → `fetch_data_node` → `bronze_service.build_bronze_payload()`
3. → `quant_engine_node` → `silver_service.compute_silver_metrics()` + `gold_service.evaluate_hard_gates()`
4. → `llm_synthesizer_node` → Ollama inference → `AnalysisOutput`
5. Background: `log_prediction_to_ledger()` → writes to `algorithmic_ledger`
6. Return `PipelineResponse`

**End-to-End Flow Trace (Engine Room — NEW):**
1. [Nightly CI] `grade_ledger.py` → queries PENDING rows → fetches future reality → grades WIN/LOSS/DRAW
2. [Weekly CI] `analyze_drift.py` → queries graded rows → compares win/loss distributions → fires threshold insights
3. [Manual] `simulate_live_history.py` → walk-forward simulation → backfills graded ledger rows

**Data Contract Issues:**
- `AnalysisState` uses `TypedDict` (structural typing) not Pydantic — no runtime validation at graph boundaries
- `user_profile` is passed as a plain dict, not the `UserProfile` TypedDict — no key validation
- Gold layer accesses `state['user_profile']['available_capital']` which defaults to `100000.0` from `APIUserProfile` but could be missing if passed as raw dict
- **Engine Room scripts** bypass the full pipeline — `simulate_live_history.py` constructs `BronzePayload` manually and only runs partial gates

**Missing Components:**
- No progress tracking for financial goals
- No data sanity checks on user profile values (e.g., negative capital accepted)
- No session expiry mechanism
- RAG-based tutor (Stage 9 vector search) not implemented — current tutor uses pure LLM inference

---

### Phase 4: LangChain / LangGraph Pipeline

**Main Analysis Graph** ([orchestrator.py](file:///c:/codes/INVR/INVR/backend/app/orchestrator.py)):
```
[fetch_data] → [quant_engine] → [llm_synthesizer] → END
```
- **Linear, no conditional edges** — errors propagate via state dict `errors` key. Nodes check `state.get("errors")` and return early, but the graph doesn't short-circuit via conditional edges.

**Tutor Graph** ([tutor_graph.py](file:///c:/codes/INVR/INVR/backend/app/pipeline/tutor_graph.py)):
```
START → [router] → (conditional) → [news_tool] → [generate] → END
                                  → [generate] → END
```
- **Issue**: Only the "news" mode triggers tool execution. Definitions, portfolio, and scenario all go directly to `generate` with no data enrichment
- **Issue**: Chat history is limited to last 10 messages (`state["messages"][-10:]`) but there's no token counting — 10 very long messages could overflow the context window

**Prompt Quality:**
- System prompt is well-structured with clear sections and format requirements
- **Mitigation present**: Sanitizes `silver_metrics` and `what_to_watch` by escaping `<` and `>` characters — **acknowledged from last audit**
- `tutor_triggers` instruction says "2-4 single financial jargon words ONLY" — good constraint but not enforced programmatically
- **FIXED since last audit**: `AnalysisOutput` no longer asks the LLM to echo `verdict` and `confidence_score` — these are injected post-inference from the Gold layer

**LLM Configuration:**
- Temperature 0.0 for analysis, 0.3 for tutor — **Appropriate** choices
- No `max_tokens` set — could produce unexpectedly long outputs
- No fallback model — Ollama unavailability triggers the deterministic fallback path (which is correct behavior)
- No streaming for the main analysis pipeline (only the tutor streams)

---

### Phase 5: Security

| Finding | Severity | Status |
|---|---|---|
| Hardcoded user ID in tutor production endpoint | 🔴 Critical | **Still open** |
| No auth on analytics endpoint | 🟠 High | **Still open** |
| No auth on tutor endpoint | 🟠 High | **Still open** |
| No CORS middleware | 🟠 High | **Still open** |
| No rate limiting | 🟡 Medium | **Still open** |
| MD5 for hashing (weak) | 🟡 Medium | **Still open** |
| No input sanitization against prompt injection | 🟡 Medium | Partially addressed (`<`/`>` escaping) |
| No output filtering on LLM responses | 🟡 Medium | **Still open** |
| `ledger_service.py` creates standalone Supabase client | 🟡 Medium | **Still open** |

**New Security Consideration:**
- Engine Room scripts (`grade_ledger.py`, `analyze_drift.py`) use `os.getenv()` + `create_client()` directly instead of the centralized `database.py` — acceptable for standalone scripts but secrets are passed via GitHub Actions environment variables (secure).

---

### Phase 6: Production Standards

- **Logging**: All `print()` — no structured logging, no log levels, no correlation IDs
- **Testing**: One comprehensive integration script (`test_pipeline.py`) with 14 steps. It uses color-coded output and `assert` statements but is not pytest-based. No unit tests for financial math.
- **Error handling**: Broad `except Exception` blocks throughout — errors are caught but not typed or actionable
- **Health check**: Returns `{"status": "healthy"}` with cache_writable and database_connected checks — **IMPROVED since last audit**: now checks `os.path.isdir(".local_cache")` and `supabase_admin is not None`

---

### Phase 7: Performance

**Critical Path (Analytics):**
1. yfinance OHLCV fetch (~1-5s per API call)
2. Optional: fundamentals fetch (~1-3s), circuit status (~1-2s), sector data (~1-5s)
3. Silver computation (< 50ms, Pandas vectorized) — offloaded via `asyncio.to_thread()`
4. Gold evaluation (< 5ms, pure Python) — offloaded via `asyncio.to_thread()`
5. LLM inference via Ollama (~5-30s depending on model and hardware)

**Bottleneck**: LLM inference is the dominant latency contributor. No streaming on the main pipeline.

**Cache Issues**: File-based cache is adequate for local dev but introduces filesystem I/O on every request. No cache invalidation beyond TTL.

**Engine Room Performance:**
- `simulate_live_history.py` processes ~60 data points per ticker × 5 tickers ≈ 300 Silver Layer computations — runs in ~2-5 minutes
- `grade_ledger.py` has a 0.5s sleep between yfinance calls to avoid rate limiting — appropriate

---

### Phase 8: Fault & Trap Detection

- **Dead-end state**: If all gates WARN (no PASS, no FAIL, no BLOCK), the verdict logic falls through to "BUY ON DIP" — this is the default catch-all which could give a buy signal on a completely data-deficient stock
- **Assumption violation**: The `market_regime` check requires 200 data points in sector history. For swing (6mo daily ≈ 126 points), market regime is never computed, defaulting to "neutral" — bearish markets won't trigger the macro override for swing trades
- **Secular trend gate is dead code** ([gold_service.py:118-122](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L118-L122)): WARN is immediately overwritten to PASS on the next line — **still broken since last audit**
- **Death cross now functional**: The `abs()` fix correctly handles the negative gap percentage — **FIXED since last audit**
- **Engine Room trap**: `simulate_live_history.py` hardcodes verdict to `"BUY ON DIP"` for all simulated trades. When `grade_ledger.py` grades these, it evaluates bullish intent (`STRONG BUY` / `BUY ON DIP` → check if price went up 5%). But the simulator doesn't actually run the full gate logic, so the stored verdict may not match what the real pipeline would have produced. This creates a systematic bias in the drift analyzer's data.

---

### Phase 9: Additional Engineering

- **No `.env.example`** — **RESOLVED**: `.env.example` now exists with template for 3 required vars
- **No migration strategy** — DB schema changes are untracked
- **No feature flags** — no gradual rollout capability
- **Hard-coded India assumptions** — `.NS` suffix, INR currency, NSE-specific APIs, Indian tax concepts in documentation
- **Regulatory disclaimers** — **RESOLVED**: Now injected post-LLM in every response
- **CI/CD** — **NEW**: GitHub Actions workflow with nightly grading and weekly drift analysis

---

### Phase 10: Quantitative Engine Room (NEW)

**Architecture Assessment:**
The Engine Room represents a significant architectural advancement — a self-improving feedback loop where the system can learn from its own predictions. The concept is sound: predict → wait → grade → analyze drift → adjust thresholds. However, the implementation has several gaps.

**Grading Logic** ([grade_ledger.py](file:///c:/codes/INVR/INVR/backend/scripts/grade_ledger.py)):
- **Intent-based grading is correct in principle**: Bullish verdicts are graded as WIN when price goes up, bearish verdicts when price goes down
- **Fixed ±5% thresholds are problematic**: The system generates ATR-based trade setups with specific entry, stop-loss, and target levels, but grading ignores these entirely. A `STRONG BUY` with a 2% ATR-based target would be graded differently than a stock with a 10% ATR-based target, but both use the same 5% threshold.
- **Only swing (15-day) evaluation window exists**: No grading for positional or long-term predictions
- **`MONITOR` verdict grading is undefined**: The code only handles bullish (`STRONG BUY`, `BUY ON DIP`) and bearish (`CAUTION`, `AVOID`) — `MONITOR` predictions are always graded as DRAW

**Drift Analysis** ([analyze_drift.py](file:///c:/codes/INVR/INVR/backend/scripts/analyze_drift.py)):
- **Minimum sample size (30) is appropriate** for basic statistical checks
- **Only 2 drift checks implemented out of 10+ possible**: RSI overbought ceiling and volume minimum ratio
- **Missing drift checks**: death cross gap threshold, sector RS minimum, max PE ceiling, EPS CAGR floor, revenue CAGR floor, debt/equity maximum, ROE minimum
- **Fixed confidence score of 90.0**: Should be calculated from sample size and statistical significance (e.g., using p-values or confidence intervals)
- **No A/B testing**: Insights are logged but there's no mechanism to automatically apply or test suggested thresholds

**Historical Simulator** ([simulate_live_history.py](file:///c:/codes/INVR/INVR/backend/scripts/simulate_live_history.py)):
- **Walk-forward methodology is correct**: Starts at day 200 to allow SMA warm-up, processes each day sequentially
- **Uses real `compute_silver_metrics()`**: The Silver Layer math is exactly the production code — good for consistency
- **Partial gate evaluation**: Only checks RSI and volume ratio, not the full `evaluate_hard_gates()` function. This means the simulator accepts trades that the production system would reject.
- **Hardcoded verdict `"BUY ON DIP"`**: All simulated trades are stored with this verdict regardless of actual gate outcomes. This corrupts the intent-based grading since the grader uses the stored verdict to determine win/loss direction.
- **No sector data, no fundamentals, no circuit status**: `BronzePayload` is constructed with `sector_history=None, fundamentals=None, institutional_activity=None`. This means the simulator only tests the technical indicator path, not the fundamental analysis path.

---

## 🛠️ Solutions Register

---

**Issue ID:** P5-01
**Phase:** 5
**Severity:** Critical
**Description:** Hardcoded `test_user_id` in production tutor route
**Impact:** All tutor chat messages are stored under one UUID, mixing all users' data, destroying data isolation
**Root Cause:** Testing shortcut left in production code
**Solution:** Add authentication dependency and use the actual user ID:
```python
# In app/api/routes/tutor.py
from app.api.deps import get_current_user_id

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest, 
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)  # ADD THIS
):
    # ... existing code ...
    
    # REPLACE line 37:
    # test_user_id = "51928e80-ce4e-4846-9a40-f1fad08cb431" 
    # WITH:
    background_tasks.add_task(
        manage_session_memory, 
        request.session_id, 
        user_id,  # USE ACTUAL USER ID
        request.message, 
        full_ai_response,
        topic_changed=False 
    )
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 30 minutes
**Dependencies:** None

---

**Issue ID:** P3-01
**Phase:** 3 / 5
**Severity:** High
**Description:** Analytics endpoint has no authentication
**Impact:** Anyone can invoke the full pipeline without credentials
**Root Cause:** `Depends(get_current_user_id)` not added to the analytics route
**Solution:**
```python
# In app/api/routes/analytics.py, add:
from app.api.deps import get_current_user_id
from fastapi import Depends

@router.post("/process", response_model=PipelineResponse)
async def process_pipeline(
    payload: PipelineRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id)  # ADD THIS
):
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 15 minutes
**Dependencies:** None

---

**Issue ID:** P3-02
**Phase:** 3 / 5
**Severity:** High
**Description:** Tutor endpoint has no authentication (separate from the hardcoded ID issue)
**Impact:** Anyone can trigger LLM inference and chat storage without authentication
**Solution:** Same pattern as P3-01 — add `Depends(get_current_user_id)` to the tutor route
**Free-Stack Compatible:** Yes
**Estimated Effort:** 15 minutes
**Dependencies:** P5-01 (hardcoded ID fix)

---

**Issue ID:** P4-01
**Phase:** 5
**Severity:** High
**Description:** No CORS middleware on FastAPI
**Impact:** API accepts requests from any domain — XSS and CSRF attacks possible when frontend is deployed
**Root Cause:** FastAPI CORS middleware not configured
**Solution:**
```python
# In main.py, add:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Restrict to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 15 minutes
**Dependencies:** None

---

**Issue ID:** P2-06
**Phase:** 2
**Severity:** Medium
**Description:** `secular_trend` gate in long-term evaluation is immediately overwritten to PASS
**Impact:** The long-term secular trend gate is non-functional — price position relative to 200-week SMA is never enforced
**Root Cause:** Line 122 of `gold_service.py` sets `gates["secular_trend"] = "PASS"` immediately after line 120 sets it to `"WARN"`, without any conditional
**Solution:**
```python
# In gold_service.py, lines 118-122, change:
if silver.sma_200:
    if silver.current_price < silver.sma_200:
        gates["secular_trend"] = "WARN"
        watch_list.append(f"Wait for structural recovery above the 200-week SMA (₹{silver.sma_200:.2f}).")
        gates["secular_trend"] = "PASS"  # DELETE THIS LINE

# To:
if silver.sma_200:
    if silver.current_price < silver.sma_200:
        gates["secular_trend"] = "WARN"
        watch_list.append(f"Wait for structural recovery above the 200-week SMA (₹{silver.sma_200:.2f}).")
    else:
        gates["secular_trend"] = "PASS"
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 5 minutes
**Dependencies:** None

---

**Issue ID:** P10-05
**Phase:** 10
**Severity:** Medium
**Description:** `ledger_service.py` creates its own Supabase client instead of using `database.py`
**Impact:** Inconsistent client management — if Supabase credentials change, two separate initialization paths must be updated
**Root Cause:** Service was written before the centralized client pattern was established
**Solution:**
```python
# In ledger_service.py, replace lines 1-13:
# REMOVE:
import os
from dotenv import load_dotenv
from supabase import create_client, Client
load_dotenv(override=True)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
else:
    supabase = None

# WITH:
from app.database import supabase_admin as supabase
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 15 minutes
**Dependencies:** None

---

**Issue ID:** P0-06
**Phase:** 0
**Severity:** Medium
**Description:** `redis` dependency declared but never used
**Impact:** Unnecessary dependency weight, potential security surface
**Solution:** Remove `"redis>=8.0.0"` from `pyproject.toml` line 17 until Redis is actually implemented
**Free-Stack Compatible:** Yes
**Estimated Effort:** 5 minutes
**Dependencies:** None

---

**Issue ID:** P6-01
**Phase:** 6
**Severity:** Medium
**Description:** No rate limiting on any endpoint
**Impact:** Single client can exhaust Ollama inference capacity or API rate limits
**Solution:** Use `slowapi` (free, open-source):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# On each endpoint:
@router.post("/process")
@limiter.limit("10/minute")
async def process_pipeline(request: Request, ...):
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 1 hour
**Dependencies:** None

---

**Issue ID:** P10-04
**Phase:** 10
**Severity:** Low
**Description:** Grading uses fixed ±5% thresholds instead of ATR-based trade setup targets
**Impact:** Grading accuracy is reduced — trades with different risk profiles are all graded against the same threshold
**Solution:**
```python
# In grade_ledger.py, replace lines 50-52:
# Instead of:
target_up = entry_price * 1.05
stop_down = entry_price * 0.95

# Use the stored trade_setup if available:
trade_setup = row["gold_verdict"].get("trade_setup")
if trade_setup:
    target_up = trade_setup["target_1"]
    stop_down = trade_setup["stop_loss"]
else:
    target_up = entry_price * 1.05
    stop_down = entry_price * 0.95
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 30 minutes
**Dependencies:** None

---

**Issue ID:** P10-07
**Phase:** 10
**Severity:** Low
**Description:** `simulate_live_history.py` hardcodes verdict to `"BUY ON DIP"` for all simulated trades
**Impact:** Corrupts intent-based grading data — all simulated trades are graded as bullish regardless of actual signal
**Solution:** Run full `evaluate_hard_gates()` on the simulated Silver metrics and store the actual computed verdict:
```python
# In simulate_live_history.py, replace line 85:
# Instead of:
"gold_verdict": {"verdict": "BUY ON DIP"},

# Run the actual gold evaluation:
from app.services.gold_service import evaluate_hard_gates
gold = evaluate_hard_gates(silver, "none", 100000.0)
# Then use:
"gold_verdict": gold.model_dump(),
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 1 hour
**Dependencies:** None

---

**Issue ID:** P9-04
**Phase:** 9
**Severity:** Low
**Description:** MD5 used for profile version hashing
**Impact:** MD5 is cryptographically broken — not a security risk here (used for change detection, not authentication) but is a bad practice signal
**Solution:**
```python
# In profile.py line 44, change:
version_hash = hashlib.md5(serialized_profile.encode("utf-8")).hexdigest()
# To:
version_hash = hashlib.sha256(serialized_profile.encode("utf-8")).hexdigest()[:16]
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 5 minutes
**Dependencies:** None

---

**Issue ID:** P6-02
**Phase:** 6
**Severity:** Low
**Description:** All logging via `print()` — no structured logging
**Solution:** Replace with Python `logging` module:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Fetching data for %s", ticker)
```
Configure in `main.py`:
```python
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 2-3 hours
**Dependencies:** None

---

**Issue ID:** P6-03
**Phase:** 6
**Severity:** Low
**Description:** No assertion-based unit tests for financial calculations
**Solution:** Create `tests/test_silver_math.py` with parametrized tests for CAGR, RSI, ATR, confidence score. Example:
```python
def test_cagr_basic():
    assert abs(calculate_cagr([100, 121]) - 0.21) < 0.001

def test_cagr_negative_start_returns_none():
    assert calculate_cagr([-100, 200]) is None

def test_cagr_three_year():
    # 100 → 200 over 3 periods = ~26% CAGR
    result = calculate_cagr([100, 130, 165, 200])
    assert abs(result - 0.2599) < 0.01
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 4-6 hours
**Dependencies:** None

---

**Issue ID:** P5-03
**Phase:** 5
**Severity:** Low
**Description:** `Settings` class mixes `os.getenv()` with `pydantic_settings.BaseSettings`
**Solution:** Use pydantic-settings' built-in `.env` loading:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

settings = Settings()
```
Remove the `load_dotenv()` call and `os.getenv()` defaults.
**Free-Stack Compatible:** Yes
**Estimated Effort:** 15 minutes
**Dependencies:** None

---

**Issue ID:** P10-06
**Phase:** 10
**Severity:** Low
**Description:** CI/CD uses Python 3.12, project requires Python 3.14+
**Solution:** Update `.github/workflows/engine_room.yml` line 19:
```yaml
python-version: '3.14'
```
Note: Ensure GitHub Actions runners support Python 3.14. If not, verify that the scripts are forward-compatible with 3.12.
**Free-Stack Compatible:** Yes
**Estimated Effort:** 5 minutes
**Dependencies:** None

---

## 🗺️ Recommended Fix Sequence

**Wave 1 — Emergency (Day 1):**
1. P5-01 — Remove hardcoded user ID in tutor endpoint
2. P2-06 — Fix secular_trend gate PASS overwrite (5-minute fix)

**Wave 2 — Security Hardening (Day 2):**
3. P3-01 — Add auth to analytics endpoint
4. P3-02 — Add auth to tutor endpoint
5. P4-01 — Add CORS middleware
6. P10-05 — Consolidate `ledger_service.py` to use centralized Supabase client

**Wave 3 — Engine Room Correctness (Days 3-4):**
7. P10-07 — Fix simulator to run full gate evaluation and store real verdicts
8. P10-04 — Use ATR-based trade setup targets for grading instead of fixed ±5%
9. P10-01 — Add positional (90-day) and long-term (365-day) grading horizons
10. P10-06 — Align CI/CD Python version

**Wave 4 — Data Integrity (Days 5-6):**
11. P1-03 — Remove or document sector PE mock
12. P1-08 — Remove or document BVPS mock
13. P1-01 — Document institutional mock data with clear TODO
14. P0-06 — Remove unused redis dependency

**Wave 5 — Code Quality (Days 7-8):**
15. P5-03 — Fix Settings class to use pydantic-settings properly
16. P9-04 — Replace MD5 with SHA-256
17. P6-02 — Replace print() with structured logging
18. P6-01 — Add rate limiting

**Wave 6 — Quality Assurance (Days 9-10):**
19. P6-03 — Write unit tests for all financial math
20. P10-03 — Expand drift analyzer with more threshold checks
21. P10-08 — Implement proper confidence scoring in drift analyzer

---

## 📈 Post-Fix Expected Improvements

| Area | Before | After |
|---|---|---|
| **Security** | Hardcoded user ID, no auth on 2/3 endpoints, no CORS | Per-user data isolation, all endpoints authenticated, CORS restricted |
| **Financial Accuracy** | Secular trend gate dead, fixed grading thresholds | All gates functional, ATR-based grading aligned with trade setup targets |
| **Engine Room** | Partial gate evaluation, hardcoded verdicts, 2 drift checks | Full pipeline simulation, accurate verdicts, comprehensive drift detection |
| **Data Integrity** | Mock data silently used, standalone DB clients | Documented mocks, centralized Supabase client pattern |
| **Reliability** | print() logging, no tests, Python version mismatch | Structured logging, assertion-based test suite, aligned CI environment |

---

## 📊 Audit Comparison: 2026-06-16 → 2026-06-20

| Metric | 2026-06-16 | 2026-06-20 | Δ |
|---|---|---|---|
| **Total Issues Found** | 56 | 29 active | 27 resolved or superseded |
| **Critical Issues** | 3 | 1 | 2 resolved (credentials in git, debug printing) |
| **High Priority Issues** | 5 | 4 | 1 resolved (confidence scoring was unweighted) |
| **Components** | 19 files | 22 files + 1 CI workflow | +3 scripts, +1 CI, +1 DB table |
| **Stages Implemented** | 9 (Stage 0–9) | 10 (Stage 0–10) | +1 (Engine Room) |
| **Database Tables** | 4 | 5 | +1 (`threshold_insights`) |
| **Ledger Columns** | 7 | 10 | +3 (`actual_outcome`, `max_favorable_excursion`, `max_adverse_excursion`) |
| **Gate Threshold Usage** | 5 of 10 constants used | 8 of 10 constants used | +3 (`debt_equity_max`, `roe_min`, `max_pe` now active) |
| **Overall Health** | Needs Work | Improved | ↑ |
