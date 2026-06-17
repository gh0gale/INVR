# 🔬 System Audit Report — FinAI (Algorithmic Portfolio Analyzer Engine)
**Date:** 2026-06-16
**Auditor:** Claude Opus 4.6 (Senior Principal Engineer Mode)
**Codebase Location:** `c:\codes\INVR\INVR`

---

## 📊 Executive Summary

FinAI is a well-architected financial analysis pipeline with a sound philosophical foundation — deterministic math before probabilistic language. The medallion architecture (Bronze → Silver → Gold → Platinum) is correctly layered, and the core technical indicator calculations (RSI, ATR, SMA) are mathematically correct. However, the system has **critical security vulnerabilities** (hardcoded credentials committed to source control, a hardcoded user ID bypassing authentication in production tutor endpoint), **financial logic gaps** (institutional data is fully hardcoded/discarded, several CAGR edge cases produce wrong outputs, and key metrics like FCF conversion are never computed), and **structural issues** that would produce incorrect advice under real-world conditions. The system is functional as a prototype but requires targeted fixes across security, data integrity, and financial correctness before any production exposure.

**Overall Health: Needs Work** — Strong foundation, but Critical and High-priority issues must be resolved.

---

## 🚨 Critical Issues (Fix Immediately)
3. **[P5-01]** Hardcoded `test_user_id` in production tutor endpoint bypasses all authentication — any user's chat is saved under a fixed UUID ([tutor.py:38](file:///c:/codes/INVR/INVR/backend/app/api/routes/tutor.py#L38))

## ⚠️ High Priority Issues (Fix Before Launch)
8. **[P1-03]** `sector_pe_median` is hardcoded to `25.0` in fundamentals — the P/E vs sector comparison in silver_service always compares against this static fiction ([market_data.py:75](file:///c:/codes/INVR/INVR/backend/app/integrations/market_data.py#L75))
12. **[P3-01]** Analytics endpoint has **no authentication** — `process_pipeline` doesn't use `Depends(get_current_user_id)`, allowing any unauthenticated caller to run the full pipeline ([analytics.py:10-11](file:///c:/codes/INVR/INVR/backend/app/api/routes/analytics.py#L10-L11))
13. **[P3-02]** Tutor endpoint has **no authentication** — same issue as analytics ([tutor.py:14](file:///c:/codes/INVR/INVR/backend/app/api/routes/tutor.py#L14))
14. **[P4-01]** No CORS middleware configured on FastAPI — the API accepts requests from any origin ([main.py](file:///c:/codes/INVR/INVR/backend/main.py))

## 🔶 Medium Priority Issues (Fix Soon)
19. **[P0-06]** `redis` dependency declared in `pyproject.toml` (line 17) but never imported or used anywhere in the codebase
31. **[P6-01]** No rate limiting on any endpoint — a single client can flood the pipeline with expensive LLM + data fetching calls


## 💡 Optimization Opportunities (Improve Over Time)
37. **[P0-08]** `pyproject.toml` uses `>=` version pinning on all dependencies — in production, pin exact versions or use lock file for reproducibility
38. **[P0-09]** No `.env.example` file exists — new developers have no template for required environment variables
39. **[P2-10]** No inflation adjustment in any projection — future value calculations should account for inflation but none exists
40. **[P2-11]** No Monte Carlo simulation or probabilistic modeling — all projections are deterministic single-path
41. **[P4-05]** No prompt versioning — prompt changes are invisible with no rollback capability
42. **[P4-06]** No LLM response caching — identical ticker/timeframe/profile combinations re-invoke the full LLM pipeline
43. **[P6-02]** All logging is `print()` statements — no structured logging framework
44. **[P6-03]** No unit tests for financial calculations — `test_gold.py` and `test_tutor.py` are integration scripts, not assertion-based unit tests
45. **[P7-02]** `compute_silver_metrics` is synchronous — blocks the event loop during Pandas operations. Should use `asyncio.to_thread()`
46. **[P7-03]** `evaluate_hard_gates` is synchronous — same issue
47. **[P9-01]** Hard-coded Indian market assumptions throughout (`.NS` suffix, INR currency, NSE circuit limits, SEBI-relevant thresholds) with no localization layer
48. **[P9-02]** No accessibility considerations — no frontend exists yet but the API responses contain no semantic structure for screen readers
49. **[P9-03]** No mandatory regulatory disclaimers in LLM output — the system generates investment verdicts without SEBI disclosure requirements
50. **[P9-04]** MD5 used for profile version hashing — cryptographically broken, should use SHA-256 ([profile.py:44](file:///c:/codes/INVR/INVR/backend/app/schemas/profile.py#L44))
51. **[P8-02]** No maximum iteration guard on LangGraph graph — if a node returns state that re-triggers routing, there's no circuit breaker
52. **[P5-03]** `Settings` class uses `os.getenv()` defaults alongside `pydantic_settings.BaseSettings` — the pydantic settings pattern should handle env loading itself, the manual `load_dotenv()` + `os.getenv()` is redundant and can cause precedence conflicts ([config.py:1-12](file:///c:/codes/INVR/INVR/backend/app/config.py#L1-L12))
53. **[P3-05]** No Supabase logging (Stage 8) implemented — analysis results are ephemeral, no backtesting is possible
54. **[P3-06]** Frontend directory is empty — no UI exists
55. **[P1-08]** `sector_history` `.replace('.NS', '')` call on line 77 of `bronze_service.py` is applied to `index_ticker` which is a caret-prefixed symbol like `^CNXAUTO` that never contains `.NS` — the call is harmless but indicates copy-paste from stock ticker handling
56. **[P4-07]** The LLM `AnalysisOutput` schema asks the LLM to echo back `verdict` and `confidence_score` — the LLM could hallucinate different values than the deterministic Gold layer computed. The echoed values should be injected post-LLM, not requested from the LLM.
57. **[P2-12]** `debt_equity_max`, `roe_min`, `max_pe` thresholds defined in `gate_thresholds.py` are never referenced — unused configuration constants
58. **[P6-04]** Health check endpoint returns no system info — doesn't verify DB connectivity, LLM availability, or cache state

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

**Folder Structure Assessment:**
- `backend/app/` — Properly separated into `api/`, `schemas/`, `services/`, `pipeline/`, `integrations/`, `tools/`
- `backend/config/` — Gate thresholds correctly externalized
- `frontend/` — **Empty directory**, no UI code exists
- Separation of concerns is **generally clean**: routes → services → integrations is respected
- **Violation**: `memory_service.py` creates its own Supabase client instead of using `database.py`
- **Misplaced**: `test_gold.py` and `test_tutor.py` are in the backend root, not in a `tests/` directory

**Orphaned/Unused:**
- `redis` package in `pyproject.toml` — never imported
- `debt_equity_max`, `roe_min`, `max_pe` in `gate_thresholds.py` — never referenced
- Duplicate `json` import in `app/api/routes/tutor.py`

---

### Phase 1: Data Layer

**Data Sources Identified:**
1. yfinance — OHLCV history, fundamentals, financial statements, news
2. nsepython — Circuit breaker status
3. Supabase — User profiles, chat sessions, semantic profiles
4. Ollama — LLM inference (local)
5. Local filesystem — Cache layer

**Key Issues:**
- Institutional activity data is **entirely fabricated** then discarded
- Circuit status logic has `lower = upper` bug making lower-circuit detection impossible
- Book value per share is **hardcoded mock data**
- Sector P/E median is a **static 25.0**
- Cache keys can collide between `TICKER` and `TICKER.NS` variants
- The `ratios` sub-dictionary expected by the long-term silver path is never constructed by the data fetcher
- No freshness validation timestamp is stored with cached data (relies only on filesystem mtime)

---

### Phase 2: Financial Logic & Mathematics

**CAGR Calculation** ([silver_service.py:7-16](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L7-L16)):
- Formula: `(end_val / start_val) ** (1 / periods) - 1` — **Correct** for positive values
- **Bug**: When `start_val > 0` and `end_val > 0` but the intermediate path includes negative values, this still computes correctly. However, when `start_val` is positive and `end_val` is negative (company went from profit to loss), the ratio is negative and fractional exponentiation raises `ValueError` in Python

**RSI Calculation** ([silver_service.py:52-56](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L52-L56)):
- Uses Wilder's smoothing (EWMA with alpha=1/14) — **Correct**
- Adds `1e-9` epsilon to prevent division by zero — **Correct**

**ATR Calculation** ([silver_service.py:59-64](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L59-L64)):
- True Range = max(H-L, |H-Cprev|, |L-Cprev|) — **Correct**
- Uses EWMA smoothing — **Correct**

**Trade Setup Math** ([gold_service.py:232-263](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L232-L263)):
- Entry zone: `price ± 0.5*ATR` — Reasonable
- Stop loss: `price - multiplier*ATR` — **Correct**
- Position sizing: `(capital * 2%) / risk_distance` — **Correct** Kelly-adjacent formula
- Risk-reward: `(target - price) / risk_distance` — **Correct**
- **Issue**: `risk_distance = max(p - stop_loss, 0.01)` — the 0.01 floor is an absolute value in INR, not proportional. For a ₹2,000 stock, 0.01 INR floor would create an absurdly large position size if ATR somehow collapsed to zero

**Confidence Score** ([gold_service.py:224](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L224)):
- `50 + (pass_ratio * 45)` — Range 50-95%. Every gate has equal weight regardless of financial severity. A circuit BLOCK counts the same as a volume WARN.

**Debt/Equity Unit Mismatch:**
- `market_data.py` divides yfinance's `debtToEquity` by 100 (converting from percentage to ratio)
- `silver_service.py` then checks `de > 150.0` — this would require D/E of 15,000% to trigger, making the debt flag effectively dead code for the swing timeframe

**Death Cross Gap Check:**
- When `sma_50 < sma_200` (a death cross), `sma_gap_pct = (sma_50 - sma_200) / sma_200 * 100` is **negative**
- The check `if sma_gap_pct > TH["death_cross_gap_pct"]` (where threshold is 0.5) will never be true for a negative value
- Result: Death crosses are always classified as WARN, never FAIL, regardless of severity

---

### Phase 3: System Cohesion

**End-to-End Flow Trace (Analytics):**
1. `POST /api/v1/analytics/process` → `analytics.py` (no auth) → builds initial state dict
2. `pipeline_graph.ainvoke()` → `fetch_data_node` → `bronze_service.build_bronze_payload()`
3. → `quant_engine_node` → `silver_service.compute_silver_metrics()` + `gold_service.evaluate_hard_gates()`
4. → `llm_synthesizer_node` → Ollama inference → `AnalysisOutput`
5. Return `PipelineResponse`

**Data Contract Issues:**
- `AnalysisState` uses `TypedDict` (structural typing) not Pydantic — no runtime validation at graph boundaries
- `user_profile` is passed as a plain dict, not the `UserProfile` TypedDict — no key validation
- Gold layer accesses `state['user_profile']['available_capital']` which defaults to `100000.0` from `APIUserProfile` but could be missing if passed as raw dict

**Missing Components:**
- No progress tracking for financial goals
- No explanation/reasoning display outside the LLM output
- No data sanity checks on user profile values (e.g., negative capital accepted)
- No session expiry mechanism
- Supabase logging (Stage 8) not implemented
- RAG-based tutor (Stage 9 vector search) not implemented — current tutor uses pure LLM inference

---

### Phase 4: LangChain / LangGraph Pipeline

**Main Analysis Graph** ([orchestrator.py](file:///c:/codes/INVR/INVR/backend/app/orchestrator.py)):
```
[fetch_data] → [quant_engine] → [llm_synthesizer] → END
```
- **Linear, no conditional edges** — errors propagate via state dict `errors` key, but the graph doesn't short-circuit. If `fetch_data` errors, `quant_engine` checks `state.get("errors")` and returns early, but the edge still routes to the next node.
- No parallel branches despite documentation claiming them

**Tutor Graph** ([tutor_graph.py](file:///c:/codes/INVR/INVR/backend/app/pipeline/tutor_graph.py)):
```
START → [router] → (conditional) → [news_tool] → [generate] → END
                                  → [generate] → END
```
- **Issue**: Only the "news" mode triggers tool execution. Definitions, portfolio, and scenario all go directly to `generate` with no data enrichment
- **Issue**: Chat history is limited to last 10 messages (`state["messages"][-10:]`) but there's no token counting — 10 very long messages could overflow the context window

**Prompt Quality:**
- System prompt is well-structured with clear sections and format requirements
- **Vulnerability**: No prompt injection protection — user-controlled data (`silver_metrics`, `what_to_watch`) is injected directly into the prompt template
- `tutor_triggers` instruction says "2-4 single financial jargon words ONLY" — good constraint but not enforced programmatically
- The LLM is asked to echo `verdict` and `confidence_score` — these should be injected post-inference to prevent hallucinated overrides

**LLM Configuration:**
- Temperature 0.0 for analysis, 0.3 for tutor — **Appropriate** choices
- No `max_tokens` set — could produce unexpectedly long outputs
- No fallback model — Ollama unavailability crashes the system
- No streaming for the main analysis pipeline (only the tutor streams)

---

### Phase 5: Security

| Finding | Severity |
|---|---|
| Supabase credentials in tracked `.env` file | 🔴 Critical |
| Service role key printed to stdout | 🔴 Critical |
| Hardcoded user ID in tutor production endpoint | 🔴 Critical |
| No auth on analytics endpoint | 🟠 High |
| No auth on tutor endpoint | 🟠 High |
| No CORS middleware | 🟠 High |
| No rate limiting | 🟡 Medium |
| MD5 for hashing (weak) | 🟡 Medium |
| No input sanitization against prompt injection | 🟡 Medium |
| No output filtering on LLM responses | 🟡 Medium |

---

### Phase 6: Production Standards

- **Logging**: All `print()` — no structured logging, no log levels, no correlation IDs
- **Testing**: Two integration scripts exist but contain zero assertions — they print output but never verify correctness
- **Error handling**: Broad `except Exception` blocks throughout — errors are caught but not typed or actionable
- **Health check**: Returns `{"status": "healthy"}` unconditionally — doesn't check DB, LLM, or cache

---

### Phase 7: Performance

**Critical Path (Analytics):**
1. yfinance OHLCV fetch (~1-5s per API call)
2. Optional: fundamentals fetch (~1-3s), circuit status (~1-2s), sector data (~1-5s)
3. Silver computation (< 50ms, Pandas vectorized)
4. Gold evaluation (< 5ms, pure Python)
5. LLM inference via Ollama (~5-30s depending on model and hardware)

**Bottleneck**: LLM inference is the dominant latency contributor. No streaming on the main pipeline.

**Cache Issues**: File-based cache is adequate for local dev but introduces filesystem I/O on every request. No cache invalidation beyond TTL.

---

### Phase 8: Fault & Trap Detection

- **Dead-end state**: If all gates WARN (no PASS, no FAIL, no BLOCK), the verdict logic falls through to "BUY ON DIP" — this is the default catch-all which could give a buy signal on a completely data-deficient stock
- **Assumption violation**: The `market_regime` check requires 200 data points in sector history. For swing (6mo daily ≈ 126 points), market regime is never computed, defaulting to "neutral" — bearish markets won't trigger the macro override for swing trades
- **Order issue**: Gold verdict overrides (Steps 1, 2, 3 in comments) execute in the order 1→2→3 in comments but the actual code runs them as Steps 2→3→1 (Volume Override → Buy Zone → Macro Override). The macro override runs last, which is correct strategically, but the comments are misleading
- **Death cross never FAIL**: As analyzed in Phase 2, the gap check math is inverted

---

### Phase 9: Additional Engineering

- **No .env.example** — onboarding friction
- **No migration strategy** — DB schema changes are untracked
- **No feature flags** — no gradual rollout capability
- **Hard-coded India assumptions** — `.NS` suffix, INR currency, NSE-specific APIs, Indian tax concepts in documentation
- **No regulatory disclaimers** — system generates investment verdicts without legally required disclosures

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
    
    # REPLACE line 38:
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




**Issue ID:** P1-05 / P1-06
**Phase:** 1
**Severity:** Medium
**Description:** Cache key collision from inconsistent ticker normalization
**Impact:** Same stock fetched and cached twice under different keys — wastes API calls, could serve stale data from one key while the other is fresh
**Root Cause:** Cache key is built from raw ticker input, but yfinance fetch normalizes by appending `.NS`
**Solution:** Normalize ticker before building cache keys:
```python
# In bronze_service.py, after line 25:
clean_ticker = ticker if ticker.endswith(".NS") else f"{ticker}.NS"

# Then use clean_ticker for all cache keys:
cache_key_price = f"price:{clean_ticker}:{manifest['period']}:{manifest['interval']}"
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 30 minutes
**Dependencies:** None

---



**Issue ID:** P4-07
**Phase:** 4
**Severity:** Medium
**Description:** LLM asked to echo verdict and confidence_score — risks hallucinated overrides
**Impact:** The LLM could return a different verdict than the deterministic Gold layer computed, undermining the "deterministic math before probabilistic language" principle
**Root Cause:** `AnalysisOutput` schema includes `verdict` and `confidence_score` fields that the LLM must fill
**Solution:** Remove `verdict` and `confidence_score` from `AnalysisOutput`, inject them post-inference:
```python
# In orchestrator.py, after line 123:
response_dict = response.model_dump()
response_dict["verdict"] = gold.verdict  # Inject deterministic values
response_dict["confidence_score"] = gold.confidence_score
return {"llm_output": response_dict}
```
And remove those fields from `AnalysisOutput` in `schemas/llm.py`.
**Free-Stack Compatible:** Yes
**Estimated Effort:** 30 minutes
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
**Dependencies:** P2-01 (CAGR fix)

---

**Issue ID:** P0-08
**Phase:** 0
**Severity:** Low
**Description:** No pinned dependency versions
**Solution:** The `uv.lock` file exists and handles this. For additional safety, generate a `requirements-lock.txt`:
```bash
uv pip compile pyproject.toml -o requirements-lock.txt
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 15 minutes
**Dependencies:** None

---

**Issue ID:** P0-09
**Phase:** 0
**Severity:** Low
**Description:** No `.env.example`
**Solution:** Create `backend/.env.example`:
```
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 5 minutes
**Dependencies:** P0-01

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

**Issue ID:** P6-04
**Phase:** 6
**Severity:** Low
**Description:** Health check is unconditional
**Solution:**
```python
@app.get("/health")
async def health_check():
    checks = {"api": "healthy"}
    try:
        from app.database import supabase
        supabase.table("user_profiles").select("id").limit(1).execute()
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"
    
    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 30 minutes
**Dependencies:** None

---

**Issue ID:** P9-03
**Phase:** 9
**Severity:** Low
**Description:** No regulatory disclaimers in LLM output
**Solution:** Add a mandatory `disclaimer` field to `AnalysisOutput`:
```python
disclaimer: str = Field(
    default="This analysis is for informational purposes only and does not constitute investment advice. Consult a SEBI-registered advisor before making investment decisions.",
    description="Mandatory regulatory disclaimer"
)
```
Also inject into the LLM system prompt: `"MANDATORY: Include a risk disclaimer noting this is not licensed financial advice."`
**Free-Stack Compatible:** Yes
**Estimated Effort:** 30 minutes
**Dependencies:** None

---

## 🗺️ Recommended Fix Sequence

**Wave 1 — Emergency (Day 1):**
1. P0-01 — Remove `.env` from git, rotate all Supabase keys
2. P0-02 — Delete debug key printing
3. P5-01 — Remove hardcoded user ID in tutor endpoint
4. P0-05 — Uncomment `.gitignore` entries

**Wave 2 — Security Hardening (Day 2):**
5. P3-01 — Add auth to analytics endpoint
6. P3-02 — Add auth to tutor endpoint
7. P4-01 — Add CORS middleware
8. P5-02 — Consolidate Supabase clients

**Wave 3 — Financial Correctness (Days 3-4):**
9. P2-01 — Fix CAGR edge cases
10. P2-02 — Fix debt/equity unit mismatch
11. P2-03 — Fix ROE dead code branch
12. P8-01 — Fix death cross gap check inversion
13. P1-01 — Pass institutional data through (or document mock)
14. P2-04 — Implement FCF conversion calculation
15. P2-05 — Fix verdict override comment ordering
16. P4-07 — Remove LLM verdict/confidence echo

**Wave 4 — Data Integrity (Days 5-6):**
17. P0-03 — Remove duplicate sma_20 field
18. P1-02 — Remove or document BVPS mock
19. P1-03 — Remove or document sector PE mock
20. P1-04 — Fix circuit status lower/upper bug
21. P1-05 — Fix cache key normalization
22. P3-04 — Populate ratios sub-dictionary

**Wave 5 — Code Quality (Days 7-8):**
23. P0-04 — Add `__init__.py` files
24. P0-06 — Remove unused redis dependency
25. P0-09 — Create `.env.example`
26. P5-03 — Fix Settings class to use pydantic-settings properly
27. P3-03 — Fix mutable default in profile schema
28. P1-07 — Remove duplicate json import
29. P6-02 — Replace print() with structured logging

**Wave 6 — Quality Assurance (Days 9-10):**
30. P6-03 — Write unit tests for all financial math
31. P6-04 — Implement proper health check
32. P9-03 — Add regulatory disclaimers
33. P9-04 — Replace MD5 with SHA-256
34. P2-09 — Implement weighted confidence scoring

**Wave 7 — Optimization (Ongoing):**
35. P4-03 — Truncate analysis state in tutor prompt
36. P6-01 — Add rate limiting
37. P7-01 — Move Silver/Gold computation to thread pool
38. Remaining optimization-tier issues

---

## 📈 Post-Fix Expected Improvements

| Area | Before | After |
|---|---|---|
| **Security** | Credentials in git, no auth on 2/3 endpoints, hardcoded user ID | Zero committed secrets, all endpoints authenticated, per-user data isolation |
| **Financial Accuracy** | Debt flag never triggers, death cross never FAILs, FCF never computed, institutional data fabricated | All gates functioning with correct unit conventions, FCF quality gate operational |
| **Data Integrity** | Cache collisions, mock data silently used, unit mismatches | Normalized cache keys, documented mocks, consistent unit conventions |
| **Reliability** | CAGR crashes on negative earnings, no input validation | Graceful handling of edge cases, defensive math |
| **Maintainability** | print() logging, no tests, misleading comments | Structured logging, assertion-based test suite, accurate documentation |
| **Regulatory** | No disclaimers, no data isolation | SEBI-compliant disclaimers, per-user data boundaries |
