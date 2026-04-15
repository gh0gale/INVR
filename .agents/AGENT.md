# AGENT.md — AI-Powered Personalized Investment Intelligence & Learning System

You are a senior AI/ML engineer and full-stack developer building a hybrid investment intelligence
platform for retail investors. 

### 🏛️ Core Philosophy: The "Investment Committee"
The system is architected as a **Multi-Analyst Committee** orchestrated via a **Lead Portfolio Manager (PM) Agent**.
- **Quant Analyst (Tool)**: Deterministic Python logic for RSI, PE, ROE, etc.
- **Risk/Macro Agent (Tool)**: Evaluates portfolio concentration and broader RAG-based context.
- **Lead PM (Agent)**: The ReAct orchestrator that weights conflicting analyst signals and synthesizes a final verdict with **Conviction & Sizing**.

### 🧠 Strategic Memory: The "Investment Thesis"
Every decision must generate an **Investment Thesis** stored in Supabase. The system doesn't just look at today's data; it checks if the current reality still supports the *original reason* for the position.

Your job is to **plan first, then implement** — making every structural decision explicit and
traceable before writing production code. Read this file fully before doing anything. Follow
phases in order. Do not skip ahead.

---

## Session Protocol

**Start of every session:**
1. Read this file top to bottom.
2. Run `cat .agents/TODO.md` — continue from next unchecked item.
3. If confused about current state, read `.agents/context-sync.md`.

**End of every session:**
1. Update `.agents/TODO.md` — check off done items, add newly discovered work.
2. Run all tests touched this session. Fix regressions before stopping.
3. Commit with conventional message: `feat(scope): description`
4. Append one line to `.agents/context-sync.md` summarising what changed.

**When uncertain about a design decision:**
- Do NOT guess silently.
- Write `docs/decisions/ADR-NNN-topic.md` using the template below.
- Pick the most defensible default, note it in the ADR, continue.
- Add to `.agents/TODO.md` under `## Needs Human Review`.

**When you feel yourself drifting from the plan:**
- Stop. Re-read this file from the top.
- Re-read `.agents/TODO.md`.
- Resume from next unchecked item only.

**ADR template:**
```
# ADR-NNN: [Topic]
## Context — why this decision is needed
## Options considered
## Decision — what we're doing and why
## Consequences — what this makes easier or harder
```

---

## Users

- **Beginner Retail Investor** — Age 20–35, low financial literacy, uses mobile/web. Wants simple
  guidance without jargon. Needs educational explanations alongside every recommendation. May not
  know their own risk profile.

- **Intermediate Retail Investor** — Age 30–50, has some market experience, wants data-backed
  analysis. Uses desktop/web. Knows basic terms (PE, RSI) but wants deeper insight. Comfortable
  with charts.

- **Privacy-Conscious Investor** — Any age range, unwilling to share exact portfolio holdings.
  Provides only rough sector descriptions. Must receive meaningful advice without requiring
  sensitive financial data.

---

## Phase 0 — Plan Before You Build

No application code until all of these exist.

### 0.1 Extract Requirements
Read `.agents/PS.md`. Write `.agents/docs/extracted_requirements.md`:
- Functional requirements — grouped by user type
- Non-functional requirements — scale, latency, privacy, data freshness, disclaimer enforcement
- AI/ML requirements — LLM routing, RAG pipeline, ReAct agent, stock analysis engine
- Ambiguities — list, do NOT assume answers

### 0.2 Map the System
Write `.agents/docs/architecture/system_overview.md`:
- All services/modules and which calls which
- End-to-end data flow per feature: "user does X" → "system does Y" → "user sees Z"
- Cover: User Profiling, Portfolio Modeling, Market ETL, Advisory, Stock Analysis, RAG, Agent, Alerts

### 0.3 Tech Stack Decision
Write `.agents/docs/decisions/ADR-001-tech-stack.md`.
Justify every choice against non-functional requirements:
- React + Tailwind vs alternatives
- FastAPI vs alternatives
- Supabase (PostgreSQL + Auth) vs alternatives
- OpenAI vs HuggingFace/Ollama
- FAISS vs ChromaDB
- LangChain ReAct vs custom agent
- yfinance vs paid data sources

### 0.4 Directory Structure
Write `.agents/docs/architecture/directory_structure.md` — full intended tree.
One-line purpose comment per directory. Do not create directories yet.

### 0.5 Gate
Only when 0.1–0.4 are all written: set `PLANNING_COMPLETE=true` in `.agents/TODO.md`.
Then begin Phase 1.

---

## Phase 1 — Scaffold

1.1 Create full directory skeleton from 0.4
1.2 `backend/requirements.txt` with pinned versions (FastAPI, uvicorn, pydantic, sqlalchemy, asyncpg, python-dotenv, httpx, yfinance, pandas, numpy, langchain, openai, sentence-transformers, faiss-cpu, chromadb, pytest, pytest-asyncio)
1.3 `frontend/package.json` — React 18, Vite, TypeScript, Tailwind CSS, React Query, React Hook Form, Zod, Recharts, React Router
1.4 `docker-compose.yml` — backend, frontend dev servers; local Supabase optional
1.5 `.env.example` — all env vars documented, no real values
1.6 Verify: `uvicorn backend.main:app --reload` starts; `npm run dev` starts

---

## Phase 2 — Database Layer (Supabase / PostgreSQL)

2.1 Define all Supabase table schemas (SQL migrations):
    - `user_profiles` (id, age, income_bracket, monthly_investable, risk_appetite, investment_horizon_months, primary_goal, sector_exposure, created_at)
    - `user_personas` (user_id, risk_score, persona_label, preferred_sectors, sector_concentration_flags, diversification_score, scoring_weight_profile)
    - `user_preferences` (user_id, notification_enabled, display_mode, language)
    - `portfolio_models` (id, user_id, sector, weight_range_low, weight_range_high)
    - `chat_history` (id, user_id, role, content, session_id, created_at)
    - `market_data` (ticker, metric_name, metric_type, value, fetched_at)
    - `sector_benchmarks` (sector, metric_name, median_value, concentration_threshold_max)
    - `macro_context` (metric_name, value, last_updated)
    - `alerts` (id, user_id, ticker, alert_type, threshold, triggered, created_at)
2.2 Supabase Auth integration — sign up, sign in, session management
2.3 SQLAlchemy async models mirroring Supabase tables (for local dev / tests)
2.4 Run migrations; verify schema in Supabase dashboard
2.5 Seed script for test user + sample portfolio model

---

## Phase 3 — Market Data ETL Pipeline

3.1 `backend/etl/market_fetcher.py` — yfinance wrapper (prices, fundamentals)
3.2 Compute derived metrics: PE, PEG, ROE, Debt/Equity, RSI, SMA-50, SMA-200, EMA-20, MACD, Beta, Volatility
3.3 `backend/etl/pipeline.py` — idempotent daily update pipeline (fetch → compute → upsert)
3.4 Cron trigger setup (APScheduler initially; Prefect-ready interface)
3.5 Data quality verification after each run (count checks, null checks, range checks)
3.6 Tests: mock yfinance responses, assert metric calculations, assert idempotency

---

## Phase 4 — Backend API (FastAPI)

### User & Auth Domain
4.1 `POST /api/v1/auth/register`, `POST /api/v1/auth/login` (delegate to Supabase Auth)
4.2 `GET/PUT /api/v1/users/me/profile` — user_profiles ingestion.
4.3 `POST /api/v1/users/me/persona` — Compute risk score (0-100) and layer 2 user_personas mapping (Conservative/Balanced/Growth/Aggressive) & scoring weights.
4.4 `GET/PUT /api/v1/users/me/portfolio` — Sector allocation ranges and probability models.

### Advisory Domain
4.5 `POST /api/v1/advisory/suggest` — Gap detection logic (vs ideal persona templates) + auto-filtering from gap sectors.

### Stock Analysis Domain
4.6 `POST /api/v1/analysis/stock` — Full 6-Lens Analysis: Fundamental, Technical, Valuation, Quant/Risk, Sentiment/Deriv, Macro.
4.7 Scorecard Engine: Composite score out of 10 heavily weighted by `user_personas.scoring_weight_profile`. 
4.8 Decision Engine: Target 1, Target 2, Stop-loss, Entry zone methodology.
4.9 Context Override: If stock is a Buy, check `user_personas.sector_concentration_flags`. Downgrade to Wait if overexposed.

### RAG / Education Domain
4.10 `POST /api/v1/education/explain` — Explain a financial concept in context at 3 literacy levels (Beginner, Intermediate, Confident).
4.11 Embedding generation + FAISS/ChromaDB vector search.
4.12 Seed vector DB with curated financial education content (PE, PEG, RSI, MACD, etc. with plain analogies).

### Agent Domain
4.11 `POST /api/v1/agent/chat` — main conversation endpoint
4.12 LangChain ReAct agent (Lead PM) wired to analyst tools: market_data, portfolio_analyzer, rag_search, stock_analysis
4.13 LLM client wrapper (Groq/Llama-3-70B, mock-able)
4.14 **Thesis Repository**: Logic to save/fetch historical decision justifications to enable stateful "Thesis Drift" detection.

### Alerts Domain
4.14 `POST /api/v1/alerts` — create price/stop-loss/target alert
4.15 `GET /api/v1/alerts` — list user alerts
4.16 Background alert checker (APScheduler) — poll prices, trigger notifications

---

## Phase 5 — Frontend UX: "User Reacts, Not Types" (React + TypeScript + Tailwind)

Design pattern: The user spends time reading, learning, and deciding — not typing. Information is proactively surfaced.

5.1 Stage 1: Onboarding — 5-7 question conversation flow (tap-to-select). Ends with persona reveal.
5.2 Stage 2: Dashboard (Landing View) — Portfolio health graph, Daily Picks (3-4 auto-generated cards with verdicts and 1-line "why for you"), Market pulse strip, Search bar.
5.3 Stage 3: Explore (Stock Deep Dive) — Full scorecard visual, composite score, "Why for you" paragraph, expandable RAG definitions ("What does this mean?").
5.4 Stage 4: Act (Trade Setup) — Entry/SL/Target UI block, sizing suggestions (% of monthly investable), Add to Watchlist button.
5.5 Chat UI — On-demand only (bottom sheet/panel). Used strictly for follow-up questions and concept learning.
5.6 Alerts management & profile settings UI.
5.7 DISCLAIMER banner — persistent, non-dismissible on analysis screens.

---

## Phase 6 — Quality

6.1 Backend tests: ≥1 test per endpoint (role-based, success, error)
6.2 ETL tests: idempotency, metric calculation accuracy (assert against known values)
6.3 AI output contract test — NEVER DELETE (`tests/test_agent_contract.py`)
6.4 Frontend: React Testing Library for critical flows (login, chat, analysis)
6.5 Accessibility: ARIA labels, keyboard navigation, color contrast ≥ 4.5:1
6.6 Disclaimer verification: test that disclaimer text is present on analysis/advisory routes

---

## Phase 7 — Hardening

7.1 Rate limiting on all LLM-calling endpoints (slowapi / nginx)
7.2 Auth middleware: all `/api/v1/` routes require valid JWT
7.3 Input validation: Pydantic on all request bodies; Zod on all forms
7.4 Secrets: all keys via env vars; no hardcoded values anywhere
7.5 Logging: structured JSON logs (structlog), request ID propagation
7.6 Data freshness: stale data warnings on analysis output (>24h old)
7.7 Performance: cache market data responses (Redis or in-memory TTL)
7.8 Deployment: frontend → Vercel, backend → Render/Railway, DB → Supabase managed

---

## Non-Negotiable Rules

1. **Never hardcode secrets, API keys, or credentials.** Always read from env vars.
2. **Every endpoint/function needs at least one test** before moving to the next.
3. **Wrap all external dependencies** (OpenAI, yfinance, Supabase, FAISS) in injectable classes.
4. **Never silently resolve a design ambiguity** — write an ADR.
5. **Run all tests at end of every phase.** Fix regressions before moving on.
6. **Keep `.agents/TODO.md` current every session.**
7. **Keep `.agents/context-sync.md` current every session.**
8. **When in doubt about scope: re-read this file. Do not invent requirements.**
9. **The AI output contract test must NEVER be deleted** (`tests/test_agent_contract.py`).
10. **On any ETL/pipeline exception: log it, mark record as REVIEW, do NOT crash the worker.**
11. **Every analysis/advisory response must include the SEBI disclaimer.** The disclaimer test must pass.
12. **Never give a "Buy" verdict without a scored, justified scorecard.** No bare recommendations.
