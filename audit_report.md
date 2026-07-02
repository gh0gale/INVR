# 🔬 System Audit Report — FinAI (Algorithmic Portfolio Analyzer Engine)
**Date:** 2026-07-02
**Auditor:** Claude Opus 4.6 (Senior Principal Engineer Mode)
**Codebase Location:** `c:\codes\INVR\INVR`
**Previous Audits:** 2026-06-16, 2026-06-20

---

## 📊 Executive Summary

FinAI has undergone a **transformative evolution** since the last audit on 2026-06-20. The most significant change is the addition of a **complete React + TypeScript frontend** — a Vite-powered application with Supabase authentication, onboarding flow, workspace dashboard, and streaming tutor chat. On the backend, **every Critical and High-priority security issue** from the previous audit has been resolved: authentication is now enforced on all endpoints via `Depends(get_current_user_id)`, CORS middleware is configured, rate limiting is implemented via `slowapi`, the hardcoded `test_user_id` has been removed from the tutor endpoint, `ledger_service.py` now uses the centralized Supabase client, structured logging replaces most `print()` calls in the core app (scripts still use `print()`), and the `secular_trend` gate bug has been fixed. Unit tests for CAGR math now exist. The `grade_ledger.py` script now uses ATR-based trade setup targets when available instead of fixed ±5% thresholds, and the simulator runs full gate evaluation. **Two new security concerns** emerged: a test bypass in `deps.py` that maps the service role key to a test user ID, and the frontend `.env` file containing live Supabase credentials is not covered by `.gitignore` (actually it IS covered by `**/.env`). The frontend has 4 unused npm dependencies. The system is now at a **functional MVP stage** with a real user-facing interface, but needs production hardening before launch.

**Overall Health: Strong — Near-Launch Quality with Targeted Fixes Needed**

### Changes Since Last Audit (2026-06-20)

| Category | Items Added/Fixed |
|---|---|
| **New Components** | Full React frontend (`Auth.tsx`, `Landing.tsx`, `Onboarding.tsx`, `Workspace.tsx`), `AuthContext.tsx`, `supabase.ts`, frontend build toolchain |
| **Security Fixes** | P5-01 hardcoded user ID ✅ FIXED, P3-01 analytics auth ✅ FIXED, P3-02 tutor auth ✅ FIXED, P4-01 CORS ✅ FIXED, P6-01 rate limiting ✅ FIXED, P10-05 ledger_service client ✅ FIXED |
| **Bug Fixes** | P2-06 secular_trend gate ✅ FIXED, P6-02 structured logging ✅ PARTIALLY FIXED (core app uses `logging`, scripts still `print()`) |
| **Engine Room Fixes** | P10-04 ATR-based grading ✅ FIXED, P10-07 simulator full gate eval ✅ FIXED |
| **Testing** | P6-03 unit tests ✅ PARTIALLY FIXED (`test_silver_math.py` covers CAGR) |
| **Still Open** | P0-06 (redis unused), P0-08 (version pinning), P5-03 (Settings class), P9-04 (MD5 hash), frontend hardcoded API URLs, unused frontend deps |

---

## ✅ What's Working Well

1. **Complete User Journey**: The system now has a full user-facing path — Landing → Auth → Onboarding → Workspace — with proper route guards, loading states, and profile-gated navigation
2. **Authentication Architecture**: `deps.py` implements proper JWT validation via Supabase's `auth.get_user()`, all three API routes (`profile`, `analytics`, `tutor`) use `Depends(get_current_user_id)`
3. **CORS + Rate Limiting**: `main.py` properly configures `CORSMiddleware` restricted to `http://localhost:5173` (Vite dev server) and `slowapi` rate limiting (`10/minute` on analytics, `30/minute` on tutor)
4. **Structured Logging**: Core backend services (`main.py`, `orchestrator.py`, `analytics.py`, `tutor.py`, `ledger_service.py`, `memory_service.py`, `market_data.py`, `tutor_graph.py`, `memory_graph.py`) all use Python's `logging` module with proper `getLogger(__name__)` patterns
5. **Secular Trend Gate**: The WARN/PASS overwrite bug is fixed — `gold_service.py` lines 118-123 now correctly uses `if/else` branching
6. **Ledger Service Centralization**: `ledger_service.py` line 3 now imports `from app.database import supabase_admin as supabase` — the standalone client anti-pattern is eliminated
7. **ATR-Based Grading**: `grade_ledger.py` lines 51-57 now uses `trade_setup` from the gold verdict if available, falling back to ±5% only as a default
8. **Simulator Full Gate Evaluation**: `simulate_live_history.py` lines 56-59 now calls `evaluate_hard_gates(silver, "none", 100000.0)` and stores the real verdict via `gold.model_dump()`
9. **Unit Tests**: `test_silver_math.py` covers 7 test cases for `calculate_cagr()` — basic doubling, 3-year growth, empty list, single element, negative start, negative end, zero start
10. **Frontend Design Quality**: The UI uses a cohesive "Liquid Glass" design system with consistent glassmorphism, Three.js ambient particle fields, Framer Motion animations, and a premium dark theme. The system is visually impressive.
11. **Frontend Auth Flow**: Supabase client-side auth with `onAuthStateChange` listener, proper session management, login/register toggle, route guards for protected pages, automatic profile fetch on auth state changes
12. **Streaming Tutor Chat**: The Workspace page correctly implements SSE-based streaming from the tutor endpoint, updating the chat log token-by-token in real time
13. **Profile Contradiction Detection**: The onboarding form validates portfolio weight sums and flags contradictions (e.g., aggressive risk + capital preservation goal)
14. **Deterministic Fallback**: When Ollama is offline, the system gracefully falls back to a deterministic verdict from the Gold layer with a clear "AI Synthesizer is currently offline" notice

---

## 🚨 Critical Issues (Fix Immediately)

1. **[NEW-P5-01]** Service role key used as test bypass in `deps.py` line 12-13 — if `token == settings.SUPABASE_SERVICE_ROLE_KEY`, the endpoint returns a hardcoded test user ID `"51928e80-ce4e-4846-9a40-f1fad08cb431"`. This means anyone who knows the service role key can impersonate the test user. While the service role key should be secret, this pattern is dangerous because:
   - The service role key grants **admin database access** — it should never be transmitted as a Bearer token from a client
   - If the key leaks (e.g., in CI logs, error messages, or frontend env), it becomes an authentication bypass AND a database admin credential in one
   - This bypasses the intent of having authentication at all for the test user

---

## ⚠️ High Priority Issues (Fix Before Launch)

2. **[NEW-FE-01]** All frontend API calls use hardcoded `http://localhost:8000` URLs — found in `Workspace.tsx` (lines 295, 415), `Onboarding.tsx` (line 304), and `AuthContext.tsx` (line 39). This will break in any non-local deployment. Should use `import.meta.env.VITE_API_URL` or a centralized API config.

3. **[NEW-FE-02]** Frontend reads `algorithmic_ledger` directly from Supabase via the client-side anon key (`Workspace.tsx` lines 203-207, 237, 321, 339). This means the ledger table's Row-Level Security (RLS) policy must be correctly configured — if RLS is disabled or misconfigured, **any authenticated user can read/delete any other user's ledger entries**. The current `deleteLedgerItem` function (line 237) deletes by `log_id` without a `user_id` filter, which is a cross-user data deletion risk.

4. **[NEW-FE-03]** The `index.html` has `<title>frontend</title>` — the page title is the default Vite scaffold placeholder. Should be "INVR — Algorithmic Portfolio Analyzer" or similar for SEO and professionalism.

5. **[NEW-P5-02]** Frontend `.env` contains live Supabase anon key (JWT token visible at `frontend/.env` line 2). While `.gitignore` does cover `**/.env`, the anon key is designed to be public (it's used client-side). However, a `.env.example` for the frontend directory is missing — new developers won't know what variables are needed.

---

## 🔶 Medium Priority Issues (Fix Soon)

6. **[P0-06]** `redis` dependency declared in `pyproject.toml` (line 18) but never imported or used anywhere — **Still open** since 2026-06-16

7. **[NEW-FE-04]** Four unused npm dependencies in `frontend/package.json`:
   - `recharts` (line 22) — never imported in any source file
   - `@react-three/drei` (line 13) — never imported (only `@react-three/fiber` is used)
   - `clsx` (line 16) — never imported
   - `tailwind-merge` (line 23) — never imported

8. **[NEW-FE-05]** `Workspace.tsx` chart uses mock price data scaled by the current price ratio (`getPricesForChart()` lines 121-127). The chart shows fabricated price action that looks real but has no relationship to the actual historical price series. The real price history from the Silver layer (`price_history` DataFrame) is not transmitted to the frontend.

9. **[NEW-BE-01]** Backend `pyproject.toml` line 6 says `requires-python = ">=3.12"` but earlier audit noted the project was targeting Python 3.14+. The CI/CD workflow also uses Python 3.12. This should be clarified — either the project works on 3.12+ (in which case the docs should say so) or it truly requires 3.14+ (in which case CI and pyproject should be updated).

10. **[NEW-FE-06]** The `Workspace.tsx` component is 1,253 lines — a single monolithic file containing the entire workspace UI (sidebar, navigation, chart, metrics cards, verdict display, trade setup, LLM analysis, chat terminal, and watchlist). This should be decomposed into smaller components for maintainability.

11. **[NEW-BE-02]** The `analyze_drift.py` script now has 4 drift checks (RSI overbought ceiling, volume minimum ratio, death cross gap, sector RS minimum) — up from 2 in the last audit. However, the confidence score formula (line 81) `min(95.0, 50.0 + (sample_size / 500.0) * 45.0)` doesn't use statistical significance tests (p-values, confidence intervals). The formula is linear in sample size, which doesn't reflect actual statistical power.

12. **[P9-04]** MD5 used for profile version hashing in `profile.py` line 44 — **Still open** since 2026-06-16

---

## 💡 Optimization Opportunities (Improve Over Time)

13. **[P0-08]** `pyproject.toml` uses `>=` version pinning on all dependencies — **Still open**

14. **[P2-10]** No inflation adjustment in any projection — **Still open**

15. **[P2-11]** No Monte Carlo simulation or probabilistic modeling — **Still open**

16. **[P4-05]** No prompt versioning — **Still open**

17. **[P4-06]** No LLM response caching — **Still open**

18. **[P5-03]** `Settings` class uses `os.getenv()` defaults alongside `pydantic_settings.BaseSettings` — **Still open**

19. **[NEW-FE-07]** The glass style system (`glass.base`, `glass.nested`, `glass.pill`) is copy-pasted identically in all 4 page components (`Auth.tsx`, `Landing.tsx`, `Onboarding.tsx`, `Workspace.tsx`). This should be extracted to a shared `styles/glass.ts` module.

20. **[NEW-FE-08]** The Three.js `DataPoints` / `Starfield` component is copy-pasted across all 4 pages with identical particle count (2500), positioning logic, and rotation animation. Should be a shared component.

21. **[NEW-FE-09]** No `<meta name="description">` in `index.html` — missing basic SEO metadata

22. **[NEW-BE-03]** Scripts (`grade_ledger.py`, `analyze_drift.py`, `simulate_live_history.py`, `analyze_and_chat.py`) still use `print()` instead of `logging`. While acceptable for CLI scripts, consistency with the core app pattern would be better.

23. **[NEW-FE-10]** No error boundary in the React app — if any component crashes (e.g., Three.js WebGL failure on unsupported browsers), the entire app white-screens with no recovery path

24. **[NEW-BE-04]** `backend/ICICIBANK_analysis_session_20260630_221950.txt` — a leftover analysis session output file sitting in the backend root directory. This is developer artifact that should not be in the repository.

25. **[NEW-FE-11]** The Onboarding page and Workspace page both contain the spring physics constants (`springPress`, `springSoft`) duplicated. These should be centralized with the glass styles.

26. **[NEW-BE-05]** The `.env.example` in the backend directory (line 4) doesn't include `MARKET_SUFFIX` — a 4th environment variable that exists in `config.py` line 11

---

## 📋 Detailed Findings by Phase

### Phase 0: System Discovery

**Tech Stack Detected:**
| Component | Technology |
|---|---|
| Language (Backend) | Python 3.12+ |
| Language (Frontend) | TypeScript 6.0+ |
| Backend Framework | FastAPI 0.136.3+ |
| Frontend Framework | React 19.2+ via Vite 8.0+ |
| Styling | TailwindCSS 3.4+ with custom glass system |
| 3D Graphics | Three.js 0.184+ via @react-three/fiber 9.6+ |
| Animation | Framer Motion 12.40+ |
| Orchestration | LangGraph 1.2.4+, LangChain Core 1.4.6+ |
| LLM | Ollama (llama3.1, local) via langchain-ollama |
| Data Processing | Pandas 3.0.3+, NumPy (transitive) |
| Validation | Pydantic 2.13.4+, pydantic-settings 2.14.1+ |
| Database | Supabase (PostgreSQL + Auth) |
| Market Data | yfinance 1.4.1+, nsepython 2.97+ |
| Cache | Local filesystem JSON (Redis declared but unused) |
| Server | uvicorn 0.49.0+ |
| CI/CD | GitHub Actions (engine_room.yml) |
| Rate Limiting | slowapi 0.1.10+ |
| Icons | lucide-react 1.21+ |

**Folder Structure Assessment:**
- `backend/app/` — Properly separated into `api/`, `schemas/`, `services/`, `pipeline/`, `integrations/`, `tools/`
- `backend/config/` — Gate thresholds correctly externalized
- `backend/scripts/` — Four scripts: `grade_ledger.py`, `analyze_drift.py`, `simulate_live_history.py`, `analyze_and_chat.py`
- `backend/tests/` — Contains `test_silver_math.py` (pytest-based unit tests for CAGR)
- `.github/workflows/` — CI/CD workflow for automated maintenance
- `frontend/src/` — **NEW:** Full React application with pages, context, assets
- `frontend/src/pages/` — Four pages: `Landing.tsx`, `Auth.tsx`, `Onboarding.tsx`, `Workspace.tsx`
- `frontend/src/context/` — `AuthContext.tsx` for global auth state
- Separation of concerns is **clean**: routes → services → integrations is respected
- **Improvement since last audit**: All core app modules use `logging`, centralized Supabase client is used everywhere, frontend exists

**Orphaned/Unused Files & Dependencies:**
- Backend: `redis` package in `pyproject.toml` — never imported
- Backend: `ICICIBANK_analysis_session_20260630_221950.txt` — leftover test output
- Frontend: `recharts`, `@react-three/drei`, `clsx`, `tailwind-merge` — installed but never imported
- Schema fields still declared but never populated: `cfo_vs_net_profit`, `promoter_holding_trend`, `book_value_growth`, `promoter_conviction_trend`, `dividend_consistency` (in `SilverMetrics`)

**Missing `.env.example` for frontend:**
- Backend has `.env.example` with 3 variables (missing `MARKET_SUFFIX`)
- Frontend has no `.env.example` at all — needs one with `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`

---

### Phase 1: Data Layer

**Data Sources Identified:**
1. yfinance — OHLCV history, fundamentals, financial statements, news
2. nsepython — Circuit breaker status
3. Supabase — User profiles, chat sessions, semantic profiles, algorithmic ledger, threshold insights, prediction interactions
4. Ollama — LLM inference (local)
5. Local filesystem — Cache layer

**Key Issues:**
- Institutional activity data is now **correctly set to `None`** with a TODO comment in `bronze_service.py` lines 83-87 — **IMPROVED** since last audit (previously was fabricated)
- Circuit status logic still has `lower = upper * 0.9` fallback (line 54 of `market_data.py`) which is an approximation
- Sector P/E median still falls back to **static 25.0** when `sectorPe`/`industryPe` are unavailable (line 85 of `market_data.py`)
- Book value per share is now **correctly computed** from balance sheet equity / shares outstanding (lines 136-146 of `market_data.py`) — **FIXED** since last audit (previously was hardcoded mock)
- Cache keys use normalized ticker format — correct
- The `ratios` sub-dictionary has `roe_5y` and `debt_to_equity_trend` as empty arrays — these are structural placeholders awaiting multi-year ROE/D\&E data which yfinance doesn't provide in a simple array format

**Frontend Data Layer Issues:**
- `Workspace.tsx` reads `algorithmic_ledger` directly from Supabase client-side (not through the backend API). This is a mixed data access pattern — profile operations go through the backend API, but ledger operations bypass it entirely
- Chart data is generated from mock price patterns scaled by current price — not actual historical data
- Watchlist is hardcoded in state (`['RELIANCE.NS', 'TCS.NS', 'INFY.NS']`) — not persisted to database

---

### Phase 2: Financial Logic & Mathematics

**CAGR Calculation** ([silver_service.py:8-20](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L8-L20)):
- Formula: `(end_val / start_val) ** (1 / periods) - 1` — **Correct** for positive values
- Guards: empty list, <2 elements, start ≤ 0, end ≤ 0 → returns None — **Correct**
- **Unit tested**: 7 test cases cover normal and edge cases — **IMPROVED**

**RSI Calculation** ([silver_service.py:55-60](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L55-L60)):
- Uses Wilder's smoothing (EWMA with alpha=1/14) — **Correct**
- Adds `1e-9` epsilon to prevent division by zero — **Correct**

**ATR Calculation** ([silver_service.py:63-68](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L63-L68)):
- True Range = max(H-L, |H-Cprev|, |L-Cprev|) — **Correct**
- Uses EWMA smoothing — **Correct**

**FCF Conversion** ([silver_service.py:161-170](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L161-L170)):
- Formula: `Σ(CFO - Capex) / Σ(Net Profit)` over minimum available years — **Correct**
- Guards: checks for non-empty lists and `total_np > 0` — **Correct**

**Debt Flag Dual-Check** ([silver_service.py:109-110](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L109-L110)):
- Handles both percentage format and ratio format — **Correct**

**Death Cross Gap Check** ([gold_service.py:96-105](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L96-L105)):
- Uses `abs(silver.sma_gap_pct)` — **Correct**

**Secular Trend Gate** ([gold_service.py:118-123](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L118-L123)):
- **FIXED** — Now has proper `if/else` branching: WARN when `current_price < sma_200`, PASS otherwise

**Trade Setup Math** ([gold_service.py:250-283](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L250-L283)):
- Entry zone: `price ± 0.5*ATR` — Reasonable
- Stop loss: `price - multiplier*ATR` — **Correct**
- Position sizing: `(capital * 2%) / risk_distance` — **Correct** Kelly-adjacent formula
- Risk-reward: `(target - price) / risk_distance` — **Correct**
- **Remaining concern**: `risk_distance = max(p - stop_loss, 0.01)` — the 0.01 floor is absolute INR, not proportional

**Confidence Score** ([gold_service.py:231-244](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py#L231-L244)):
- Weighted scoring with `GATE_WEIGHTS` — **Correct**
- Formula: `50 + (passed_weight / total_weight * 45)` — Range 50-95%

**ROE Consistency Fallback** ([silver_service.py:174-182](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py#L174-L182)):
- The `or` condition in `roe_val > 0.18 or roe_val > 18.0` means `> 0.18` always triggers first, making `> 18.0` redundant. This is benign (logically correct since 0.18 < 18.0) but semantically misleading.

---

### Phase 3: System Cohesion

**End-to-End Flow Trace (Full User Journey):**
1. Landing page → User clicks "Access Terminal" → `/auth` route
2. Auth page → Supabase `signUp`/`signInWithPassword` → JWT stored in session
3. `AuthContext` → `fetchProfile()` via `GET /api/v1/profiles/` with Bearer token
4. If 404 → Navigate to `/onboarding` → User fills profile form → `POST /api/v1/profiles/` → Profile saved to Supabase
5. If profile exists → Navigate to `/workspace`
6. Workspace → User enters ticker in search bar or chat terminal
7. `runAnalysis()` → `POST /api/v1/analytics/process` with auth token + payload
8. Backend: `analytics.py` validates auth → builds initial state → `pipeline_graph.ainvoke()`
9. Pipeline: `fetch_data_node` → `quant_engine_node` → `llm_synthesizer_node`
10. Background: `log_prediction_to_ledger()` → writes to `algorithmic_ledger`
11. Frontend: Waits 3 seconds → queries `algorithmic_ledger` via Supabase client → displays results
12. Chat: User types question → `POST /api/v1/tutor/chat/stream` → SSE streaming to UI

**Data Contract Issues:**
- `AnalysisState` uses `TypedDict` (structural typing) not Pydantic — no runtime validation at graph boundaries
- `user_profile` is passed as a plain dict, not the `UserProfile` TypedDict — no key validation
- The frontend's 3-second wait before querying the ledger (Workspace.tsx line 334) is a race condition hack — the background task may not have completed. If it hasn't, the frontend falls through to a secondary 2-second wait (line 374), making worst-case latency 5+ seconds after pipeline completion before the UI updates.

**Missing Components (as compared to system's stated purpose):**
- No progress tracking for financial goals
- No data sanity checks on user profile values (e.g., negative capital accepted via API — `capital: float = Field(..., gte=0)` only enforces ≥0 in Pydantic, but `available_capital` in `APIUserProfile` has no `gte` constraint at all, defaulting to `100000.0`)
- No session expiry mechanism in the frontend (Supabase handles token refresh automatically, but there's no re-auth flow for expired refresh tokens)
- RAG-based tutor not implemented — current tutor uses pure LLM inference
- No watchlist persistence — watchlist is local React state, lost on page refresh
- No "Recover Key?" functionality — the forgot password button in `Auth.tsx` line 281 is a UI element with no `onClick` handler

**Redundancy Detection:**
- Glass style system duplicated 4 times across frontend pages (Landing, Auth, Onboarding, Workspace)
- Three.js DataPoints/Starfield component duplicated 4 times
- Spring physics constants duplicated 4 times

---

### Phase 4: LangChain / LangGraph Pipeline

**Main Analysis Graph** ([orchestrator.py](file:///c:/codes/INVR/INVR/backend/app/orchestrator.py)):
```
[fetch_data] → [quant_engine] → [llm_synthesizer] → END
```
- **Linear, no conditional edges** — errors propagate via state dict `errors` key. Nodes check `state.get("errors")` and return early, but the graph doesn't short-circuit via conditional edges.
- **Issue**: When an error occurs in `fetch_data_node`, the `quant_engine_node` returns `state` (the full state including errors), but `llm_synthesizer_node` also just returns `state`. Both nodes process but do nothing useful — they could be skipped entirely via conditional routing.

**Tutor Graph** ([tutor_graph.py](file:///c:/codes/INVR/INVR/backend/app/pipeline/tutor_graph.py)):
```
START → [router] → (conditional) → [news_tool] → [generate] → END
                                  → [generate] → END
```
- Only "news" mode triggers tool execution. Definition, portfolio, and scenario go directly to `generate` with no data enrichment — appropriate since those modes operate on the analysis context already in state
- Chat history limited to last 10 messages (`state["messages"][-10:]`) but no token counting — 10 very long messages could overflow the context window
- `analysis_state_str` is truncated to 2000 characters (line 58-59) — good guard against context overflow

**Prompt Quality:**
- System prompt is well-structured with clear sections and format requirements
- Sanitization present: `<` and `>` characters are escaped in silver metrics and watch list — **Correct**
- `tutor_triggers` instruction says "2-4 single financial jargon words ONLY" — not enforced programmatically
- `AnalysisOutput` no longer asks the LLM to echo `verdict` and `confidence_score` — these are injected post-inference from the Gold layer (lines 157-158) — **Correct**
- Regulatory disclaimer injected on every response (line 159) — **Correct**

**LLM Configuration:**
- Temperature 0.0 for analysis, 0.3 for tutor — **Appropriate** choices
- No `max_tokens` set — could produce unexpectedly long outputs
- No fallback model — Ollama unavailability triggers the deterministic fallback path (which is correct behavior)
- Streaming implemented for tutor (via `astream` with `stream_mode="messages"`) but not for main analysis pipeline

---

### Phase 5: Security

| Finding | Severity | Status |
|---|---|---|
| Hardcoded test user ID in tutor production endpoint | 🔴 Critical | ✅ **RESOLVED** (line removed, uses `Depends(get_current_user_id)`) |
| Service role key as test bypass in `deps.py` | 🔴 Critical | **NEW** — maps service role key to test user ID |
| No auth on analytics endpoint | 🟠 High | ✅ **RESOLVED** |
| No auth on tutor endpoint | 🟠 High | ✅ **RESOLVED** |
| No CORS middleware | 🟠 High | ✅ **RESOLVED** (restricted to `http://localhost:5173`) |
| Frontend direct DB access without user filtering | 🟠 High | **NEW** — `algorithmic_ledger` reads/deletes bypass backend |
| No rate limiting | 🟡 Medium | ✅ **RESOLVED** (slowapi) |
| MD5 for hashing (weak) | 🟡 Medium | **Still open** |
| No input sanitization against prompt injection | 🟡 Medium | Partially addressed (`<`/`>` escaping) |
| No output filtering on LLM responses | 🟡 Medium | **Still open** |
| Frontend API URLs hardcoded | 🟡 Medium | **NEW** |
| `ledger_service.py` standalone Supabase client | 🟡 Medium | ✅ **RESOLVED** |

---

### Phase 6: Production Standards

- **Logging**: Core app uses Python `logging` module with proper format string ✅ — Scripts still use `print()` (acceptable for CLI)
- **Testing**: `test_silver_math.py` with 7 pytest-based unit tests for CAGR calculation. `test_pipeline.py` with 14-step integration test. No unit tests for RSI, ATR, confidence score, trade setup math, or Gold layer verdict logic.
- **Error handling**: Broad `except Exception` blocks in backend — errors are caught, logged via `logger.error()` with `exc_info=True` in orchestrator, but not typed or actionable. Frontend has try/catch in critical paths.
- **Health check**: Returns `{"status": "healthy"}` with `cache_writable` and `database_connected` checks

---

### Phase 7: Performance

**Critical Path (Analytics):**
1. yfinance OHLCV fetch (~1-5s per API call)
2. Optional: fundamentals fetch (~1-3s), circuit status (~1-2s), sector data (~1-5s)
3. Silver computation (< 50ms, Pandas vectorized) — offloaded via `asyncio.to_thread()`
4. Gold evaluation (< 5ms, pure Python) — offloaded via `asyncio.to_thread()`
5. LLM inference via Ollama (~5-30s depending on model and hardware)
6. Frontend wait: 3-5 seconds (hardcoded `setTimeout` for ledger write propagation)

**Bottleneck**: LLM inference is the dominant latency contributor. Total end-to-end latency from user input to UI update: ~15-45 seconds.

**Frontend Performance:**
- Three.js `Canvas` with 2500 particles on every page — 4 separate WebGL contexts if the user navigates through all pages. On mobile or low-end devices, this could cause significant GPU usage.
- `Workspace.tsx` at 1253 lines will cause long initial parse times
- No code splitting — all pages are bundled together
- No lazy loading for Three.js components

---

### Phase 8: Fault & Trap Detection

- **Dead-end state**: If all gates WARN (no PASS, no FAIL, no BLOCK), the verdict logic falls through to "BUY ON DIP" — this catch-all could give a buy signal on a data-deficient stock. The "BUY ON DIP" filter then checks for support proximity and may downgrade to "CAUTION" — this is a reasonable safety net.
- **Assumption violation**: Market regime requires 200 data points. For swing (6mo daily ≈ 126 points), market regime is never computed, defaulting to "neutral" — bearish markets won't trigger the macro override for swing trades. **Still present.**
- **Frontend race condition**: The 3-second wait after pipeline completion (Workspace.tsx line 334) before querying the ledger is fragile. If the background task takes longer (e.g., Supabase is slow), the frontend will either show stale data or show nothing. The fallback 2-second retry partially mitigates this.
- **"Recover Key?" button does nothing**: `Auth.tsx` line 281 — the forgot password button has no `onClick` handler. Users who click it see no feedback.
- **Watchlist not persisted**: Bookmarked tickers exist only in React `useState` — navigating away loses them entirely
- **Ledger deduplication on frontend**: `Workspace.tsx` line 211-217 deduplicates ledger entries by ticker client-side. If a user analyzes the same ticker with different timeframes, only the most recent entry is shown.

---

### Phase 9: Additional Engineering

- **`.env.example`** — Backend: exists but missing `MARKET_SUFFIX`. Frontend: none exists.
- **No migration strategy** — DB schema changes are untracked
- **No feature flags** — no gradual rollout capability
- **Hard-coded India assumptions** — `.NS` suffix, INR currency, NSE-specific APIs, Indian tax concepts in prompts
- **Regulatory disclaimers** — Injected post-LLM in every response ✅
- **CI/CD** — GitHub Actions workflow with nightly grading and weekly drift analysis
- **No accessibility**: No ARIA labels, no keyboard navigation for glass-styled custom components, no screen reader support
- **No favicon**: `index.html` references `/favicon.svg` but `frontend/public/` directory contents unknown

---

### Phase 10: Quantitative Engine Room

**Architecture Assessment:**
The Engine Room is now more robust than the previous audit. Both critical fixes from the last audit have been applied: grading uses ATR-based targets when available, and the simulator runs full gate evaluation.

**Grading Logic** ([grade_ledger.py](file:///c:/codes/INVR/INVR/backend/scripts/grade_ledger.py)):
- **ATR-based grading ✅ FIXED**: Lines 51-57 check for `trade_setup` in `gold_verdict` and use `target_1`/`stop_loss` if available
- Fallback to ±5% only when no trade setup is stored — correct for MONITOR/CAUTION/AVOID verdicts that don't generate trade setups
- All three timeframe horizons are now defined in `TIMEFRAMES` dict (swing: 15, positional: 90, long_term: 365)
- `MONITOR` verdict grading remains undefined — always graded as DRAW

**Drift Analysis** ([analyze_drift.py](file:///c:/codes/INVR/INVR/backend/scripts/analyze_drift.py)):
- **Expanded to 4 checks**: RSI overbought ceiling, volume minimum ratio, death cross gap, sector RS minimum — **IMPROVED** from 2 checks
- Confidence score formula improved: `min(95.0, 50.0 + (sample_size / 500.0) * 45.0)` — scales linearly with sample size, capped at 95%
- **Missing drift checks**: max PE ceiling, EPS CAGR floor, revenue CAGR floor, debt/equity maximum, ROE minimum

**Historical Simulator** ([simulate_live_history.py](file:///c:/codes/INVR/INVR/backend/scripts/simulate_live_history.py)):
- **Full gate evaluation ✅ FIXED**: Lines 56-59 call `evaluate_hard_gates(silver, "none", 100000.0)` and store real verdict via `gold.model_dump()`
- Only stores trades with bullish verdicts (`STRONG BUY` or `BUY ON DIP`) — correct for swing-focused backtesting
- Grading still uses fixed ±5% thresholds (lines 72-73) instead of the stored trade setup's targets — this is inconsistent with the `grade_ledger.py` fix. The simulator grades inline, not through the grading script.
- **No sector data, no fundamentals, no circuit status**: `BronzePayload` is constructed with `sector_history=None, fundamentals=None, institutional_activity=None` — simulator only tests technical path

---

### Phase 11: Frontend Application (NEW)

**Architecture:**
- React 19 + TypeScript + Vite + TailwindCSS
- Supabase JS client for auth and direct DB access
- React Router v7 for client-side routing
- Framer Motion for animations
- Three.js (via @react-three/fiber) for ambient 3D particle effects

**Component Structure:**
| File | Lines | Purpose | Quality |
|---|---|---|---|
| `Landing.tsx` | 681 | Marketing page | ✅ Well-designed, responsive |
| `Auth.tsx` | 412 | Login/Register | ✅ Solid, handles errors well |
| `Onboarding.tsx` | 745 | Profile creation wizard | ✅ Multi-step, validates portfolio weights |
| `Workspace.tsx` | 1253 | Main dashboard | ⚠️ Too large, needs decomposition |
| `AuthContext.tsx` | 115 | Auth state management | ✅ Clean implementation |
| `supabase.ts` | 11 | Supabase client | ✅ Minimal, correct |

**Strengths:**
- Consistent glassmorphism design language across all pages
- Real-time streaming chat with token-by-token display
- Proper auth flow with protected routes and profile-gated navigation
- Form validation in onboarding (portfolio weight sum check)
- Responsive layout considerations

**Weaknesses:**
- API URL hardcoding (`http://localhost:8000` × 4 occurrences)
- Direct Supabase DB reads bypassing backend (mixed data access pattern)
- Mock chart data instead of real historical prices
- Watchlist not persisted
- 4 unused npm dependencies
- Massive monolithic Workspace component
- Duplicated design tokens across all pages
- No error boundaries
- No lazy loading / code splitting

---

## 🛠️ Solutions Register

---

**Issue ID:** NEW-P5-01
**Phase:** 5
**Severity:** Critical
**Description:** Service role key used as authentication bypass in `deps.py`
**Impact:** Anyone with the service role key can authenticate as the test user, combining admin DB access with identity impersonation
**Root Cause:** Development convenience left in production code
**Solution:**
```python
# In app/api/deps.py, REMOVE lines 11-13:
# Secure test bypass: if client provides service role key, map to the default test user
# if settings.SUPABASE_SERVICE_ROLE_KEY and token == settings.SUPABASE_SERVICE_ROLE_KEY:
#     return "51928e80-ce4e-4846-9a40-f1fad08cb431"

# For testing, use a proper Supabase test user account with real credentials.
# The test_pipeline.py should use: supabase.auth.sign_in_with_password()
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 15 minutes
**Dependencies:** Test script needs to be updated to use real auth

---

**Issue ID:** NEW-FE-01
**Phase:** 3 / 5
**Severity:** High
**Description:** All frontend API calls use hardcoded `http://localhost:8000`
**Impact:** Application will fail in any non-localhost deployment
**Root Cause:** No API base URL configuration
**Solution:**
```typescript
// 1. Add to frontend/.env:
VITE_API_BASE_URL="http://localhost:8000"

// 2. Create frontend/src/api.ts:
export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 3. Replace all occurrences:
// FROM: fetch('http://localhost:8000/api/v1/...')
// TO:   fetch(`${API_BASE}/api/v1/...`)
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 30 minutes
**Dependencies:** None

---

**Issue ID:** NEW-FE-02
**Phase:** 5
**Severity:** High
**Description:** Frontend reads/deletes `algorithmic_ledger` directly via Supabase client without user filtering
**Impact:** Cross-user data access and deletion possible if RLS is misconfigured
**Solution:** Either:
- (A) Add proper RLS policies on `algorithmic_ledger` with `auth.uid()` checks, OR
- (B) Move all ledger reads/deletes to backend API endpoints with `Depends(get_current_user_id)` filtering
Option B is architecturally cleaner — all data access goes through the backend.
**Free-Stack Compatible:** Yes
**Estimated Effort:** 2-3 hours
**Dependencies:** None

---

**Issue ID:** NEW-FE-03
**Phase:** 9
**Severity:** High
**Description:** `<title>frontend</title>` in `index.html`
**Impact:** Poor SEO, unprofessional browser tab display
**Solution:** Change to `<title>INVR — Algorithmic Portfolio Intelligence</title>` and add `<meta name="description" ...>`
**Free-Stack Compatible:** Yes
**Estimated Effort:** 5 minutes
**Dependencies:** None

---

**Issue ID:** P0-06
**Phase:** 0
**Severity:** Medium
**Description:** `redis` dependency declared but never used
**Impact:** Unnecessary dependency weight, potential security surface
**Solution:** Remove `"redis>=8.0.0"` from `pyproject.toml` line 18
**Free-Stack Compatible:** Yes
**Estimated Effort:** 5 minutes
**Dependencies:** None

---

**Issue ID:** NEW-FE-04
**Phase:** 0
**Severity:** Medium
**Description:** Four unused npm dependencies: `recharts`, `@react-three/drei`, `clsx`, `tailwind-merge`
**Impact:** Larger bundle size, unnecessary install time, potential vulnerability surface
**Solution:** `npm uninstall recharts @react-three/drei clsx tailwind-merge`
**Free-Stack Compatible:** Yes
**Estimated Effort:** 5 minutes
**Dependencies:** None

---

**Issue ID:** NEW-FE-05
**Phase:** 1
**Severity:** Medium
**Description:** Chart uses mock price data scaled by current price ratio — not actual historical data
**Impact:** Users see fabricated price charts that look real but have no relationship to actual stock price history. This is misleading.
**Solution:** Include a representative price series in the `PipelineResponse` (e.g., last 30 closing prices from the Silver layer), or have the frontend fetch recent prices from the backend on demand.
**Free-Stack Compatible:** Yes
**Estimated Effort:** 2-3 hours
**Dependencies:** Backend API change needed

---

**Issue ID:** NEW-BE-01
**Phase:** 0
**Severity:** Medium
**Description:** `pyproject.toml` says `requires-python >= 3.12` while previous audit referenced Python 3.14+
**Impact:** Confusion about supported Python versions; CI uses 3.12
**Solution:** Verify which Python version is actually required and standardize across `pyproject.toml`, CI, and documentation
**Free-Stack Compatible:** Yes
**Estimated Effort:** 15 minutes
**Dependencies:** None

---

**Issue ID:** NEW-FE-06
**Phase:** 6
**Severity:** Medium
**Description:** `Workspace.tsx` is 1253 lines — monolithic single-file component
**Impact:** Poor maintainability, hard to test individual sections, long parse times
**Solution:** Extract into:
- `components/Chart.tsx` — price chart with SVG
- `components/MetricsGrid.tsx` — silver metrics cards
- `components/VerdictPanel.tsx` — gold verdict + trade setup
- `components/ChatTerminal.tsx` — command input + log
- `components/Sidebar.tsx` — ledger + watchlist sidebar
**Free-Stack Compatible:** Yes
**Estimated Effort:** 3-4 hours
**Dependencies:** None

---

**Issue ID:** P9-04
**Phase:** 9
**Severity:** Low
**Description:** MD5 used for profile version hashing
**Solution:** Replace with SHA-256 in `profile.py` line 44:
```python
version_hash = hashlib.sha256(serialized_profile.encode("utf-8")).hexdigest()[:16]
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 5 minutes
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
    MARKET_SUFFIX: str = ".NS"

settings = Settings()
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 15 minutes
**Dependencies:** None

---

**Issue ID:** NEW-FE-07
**Phase:** 6
**Severity:** Low
**Description:** Glass style system and spring physics duplicated across 4 frontend pages
**Solution:** Create `frontend/src/styles/glass.ts` and `frontend/src/styles/springs.ts` as shared exports
**Free-Stack Compatible:** Yes
**Estimated Effort:** 30 minutes
**Dependencies:** None

---

**Issue ID:** NEW-FE-08
**Phase:** 6
**Severity:** Low
**Description:** Three.js DataPoints/Starfield component duplicated across 4 pages
**Solution:** Create `frontend/src/components/Starfield.tsx` as shared component
**Free-Stack Compatible:** Yes
**Estimated Effort:** 20 minutes
**Dependencies:** None

---

**Issue ID:** NEW-FE-10
**Phase:** 6
**Severity:** Low
**Description:** No React error boundary — WebGL or component crashes cause full-page white screen
**Solution:** Add error boundary wrapper:
```tsx
import { ErrorBoundary } from 'react-error-boundary';
// In App.tsx, wrap <AppRoutes /> with <ErrorBoundary fallback={<FallbackUI />}>
```
**Free-Stack Compatible:** Yes
**Estimated Effort:** 30 minutes
**Dependencies:** None

---

**Issue ID:** NEW-BE-04
**Phase:** 0
**Severity:** Low
**Description:** Leftover analysis session file `ICICIBANK_analysis_session_20260630_221950.txt` in backend root
**Solution:** Delete or add `*_analysis_session_*.txt` to `.gitignore`
**Free-Stack Compatible:** Yes
**Estimated Effort:** 2 minutes
**Dependencies:** None

---

## 🗺️ Recommended Fix Sequence

**Wave 1 — Security Emergency (Day 1):**
1. NEW-P5-01 — Remove service role key bypass in `deps.py`
2. NEW-FE-02 — Fix ledger access pattern (add RLS or move to backend API)

**Wave 2 — Deployment Readiness (Day 2):**
3. NEW-FE-01 — Extract hardcoded API URLs to environment variable
4. NEW-FE-03 — Fix HTML title and add meta description
5. P0-06 — Remove unused `redis` dependency
6. NEW-FE-04 — Remove unused npm dependencies

**Wave 3 — Data Integrity (Days 3-4):**
7. NEW-FE-05 — Replace mock chart data with real price history
8. NEW-BE-01 — Standardize Python version across project

**Wave 4 — Code Quality (Days 5-6):**
9. NEW-FE-06 — Decompose Workspace.tsx into smaller components
10. NEW-FE-07 — Extract glass styles to shared module
11. NEW-FE-08 — Extract Starfield to shared component
12. NEW-FE-10 — Add error boundary

**Wave 5 — Polish (Days 7-8):**
13. P5-03 — Fix Settings class to use pydantic-settings properly
14. P9-04 — Replace MD5 with SHA-256
15. NEW-BE-04 — Clean up leftover analysis file
16. NEW-BE-05 — Add `MARKET_SUFFIX` to `.env.example`, create frontend `.env.example`

---

## 📈 Post-Fix Expected Improvements

| Area | Before | After |
|---|---|---|
| **Security** | Service role key bypass, no RLS filtering | Clean auth flow, proper data isolation |
| **Deployability** | Hardcoded localhost URLs, placeholder title | Environment-driven config, production-ready |
| **Data Accuracy** | Mock chart data, no real price visualization | Real historical price charts from pipeline |
| **Maintainability** | 1253-line monolith, duplicated styles × 4 | Modular components, shared design tokens |
| **Bundle Size** | 4 unused npm packages | Clean dependency tree |

---

## 📊 Audit Comparison: 2026-06-16 → 2026-06-20 → 2026-07-02

| Metric | 2026-06-16 | 2026-06-20 | 2026-07-02 | Δ (since 2026-06-20) |
|---|---|---|---|---|
| **Total Issues Found** | 56 | 29 active | 26 active | −3 resolved, +14 new (12 frontend) |
| **Critical Issues** | 3 | 1 | 1 | ✅ Old critical fixed, 1 new |
| **High Priority Issues** | 5 | 4 | 4 | ✅ All old high fixed, 4 new |
| **Components (Backend)** | 19 files | 22 files + 1 CI | 23 files + 1 CI | +1 (test_silver_math.py) |
| **Components (Frontend)** | 0 files | 0 files | 17 files (4 pages, context, config, styles) | **+17** |
| **Stages Implemented** | 9 | 10 | 11 (+ Frontend) | +1 (Full UI) |
| **Security Issues Open** | 7 | 6 | 3 | ↓ 3 resolved |
| **Test Coverage** | 0 unit tests | 0 unit tests | 7 unit tests (CAGR) | ↑ |
| **Logging** | All `print()` | All `print()` | `logging` in core, `print()` in scripts | ↑ |
| **Auth Coverage** | 1/3 endpoints | 1/3 endpoints | 3/3 endpoints | ✅ 100% |
| **Overall Health** | Needs Work | Improved | **Strong** | ↑↑ |
