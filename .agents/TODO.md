# TODO — AI Investment Intelligence System

PLANNING_COMPLETE=false

---

## Phase 0 — Planning
- [ ] 0.1 Read PS.md and write `.agents/docs/extracted_requirements.md`
- [ ] 0.2 Write `.agents/docs/architecture/system_overview.md`
- [ ] 0.3 Write `.agents/docs/decisions/ADR-001-tech-stack.md`
- [ ] 0.4 Write `.agents/docs/architecture/directory_structure.md`
- [ ] 0.5 Set PLANNING_COMPLETE=true

## Phase 1 — Scaffold
- [ ] 1.1 Create full directory skeleton from 0.4
- [ ] 1.2 `backend/requirements.txt` with pinned versions
- [ ] 1.3 `frontend/package.json` — React 18, Vite, TypeScript, Tailwind, React Query, etc.
- [ ] 1.4 `docker-compose.yml` — backend + frontend dev servers
- [ ] 1.5 `.env.example` — all env vars, no real values
- [ ] 1.6 Verify: backend starts (`uvicorn`), frontend starts (`npm run dev`)

## Phase 2 — Database Layer
- [ ] 2.1 Define all Supabase table schemas (`user_profiles`, `user_personas`, `portfolio_models`, `market_data`, `sector_benchmarks`, `macro_context`, etc.)
- [ ] 2.2 Supabase Auth integration
- [ ] 2.3 SQLAlchemy async models (for local dev / tests)
- [ ] 2.4 Run migrations; verify schema
- [ ] 2.5 Seed script: test user + sample portfolio model + RAG seed data + sample sector benchmarks

## Phase 3 — Market Data ETL Pipeline
- [ ] 3.1 `backend/etl/market_fetcher.py` — yfinance wrapper
- [ ] 3.2 Compute derived metrics (PE, PEG, ROE, RSI, SMA, MACD, Beta, Volatility)
- [ ] 3.3 `backend/etl/pipeline.py` — idempotent daily update pipeline
- [ ] 3.4 Cron trigger setup (APScheduler / Prefect-ready)
- [ ] 3.5 Data quality verification after each run
- [ ] 3.6 ETL tests (mock responses, metric accuracy, idempotency)

## Phase 4 — Backend API
- [ ] 4.1 Auth endpoints (register, login via Supabase Auth)
- [ ] 4.2 User profile ingestion (`GET/PUT /api/v1/users/me/profile`)
- [ ] 4.3 Persona Endpoint: Risk score mapping + scoring_weight_profile generation
- [ ] 4.4 Portfolio & Sector alignment logic endpoint
- [ ] 4.5 Advisory endpoint (gap detection vs ideal persona templates)
- [ ] 4.6 Stock analysis endpoint (Full 6-Lens Analysis: Funda, Tech, Val, Quant, Sent, Macro)
- [ ] 4.7 Scorecard output (Target 1, Target 2, Stop-loss, Entry zone, "Why for you")
- [ ] 4.8 Education/RAG endpoint (Explain concepts at Beginner, Intermediate, Confident levels)
- [ ] 4.9 Embedding generation + vector search (FAISS/ChromaDB)
- [ ] 4.10 Seed vector DB with financial education content
- [ ] 4.11 Agent chat endpoint (used strictly for follow-up questions)
- [ ] 4.12 LangChain ReAct agent + tools wiring
- [ ] 4.13 LLM client wrapper (OpenAI-first, mockable)
- [ ] 4.14 Alerts creation endpoint
- [ ] 4.15 Alerts listing endpoint
- [ ] 4.16 Background alert checker

## Phase 5 — Frontend UX: "User Reacts, Not Types"
- [ ] 5.1 Stage 1: Onboarding flow (5-7 tap-to-select questions -> Persona Reveal)
- [ ] 5.2 Stage 2: Dashboard (Portfolio Health, Daily Picks, Market Pulse)
- [ ] 5.3 Stage 3: Explore (Stock Scorecard visual, "Why for you", Explainers)
- [ ] 5.4 Stage 4: Act (Trade Setup UI, Position Sizing logic)
- [ ] 5.5 Chat UI (On-demand panel for concept learning & follow-ups)
- [ ] 5.6 Alerts screen (create + manage)
- [ ] 5.7 Education panel component mapping
- [ ] 5.8 Persistent SEBI disclaimer banner on analysis screens

## Phase 6 — Quality
- [ ] 6.1 Backend tests: ≥1 per endpoint
- [ ] 6.2 ETL tests: idempotency + metric accuracy
- [ ] 6.3 AI output contract test (`tests/test_agent_contract.py`) — NEVER DELETE
- [ ] 6.4 Frontend: React Testing Library for critical flows
- [ ] 6.5 Accessibility: ARIA labels, keyboard nav, contrast ≥ 4.5:1
- [ ] 6.6 Disclaimer presence test on analysis/advisory routes

## Phase 7 — Hardening
- [ ] 7.1 Rate limiting on LLM-calling endpoints
- [ ] 7.2 Auth middleware on all `/api/v1/` routes
- [ ] 7.3 Input validation (Pydantic + Zod)
- [ ] 7.4 Secrets audit (no hardcoded values)
- [ ] 7.5 Structured JSON logging (structlog) + request ID propagation
- [ ] 7.6 Stale data warnings on analysis output (>24h)
- [ ] 7.7 Market data response caching (Redis or in-memory TTL)
- [ ] 7.8 Deployment: Vercel (frontend), Render/Railway (backend), Supabase (DB)

---

## Needs Human Review
<!-- Agent adds items here. Human removes only after reviewing. -->
