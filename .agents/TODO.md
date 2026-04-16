# TODO — AI Investment Intelligence System

> [!IMPORTANT]
> **Project Implementation Context & Sync**: For detailed architectural blueprints, progress tracking (TODOs), and product specifications, always refer to the [`.agents/`](file:///.agents) directory.

PLANNING_COMPLETE=true

---

## Phase 0 — Planning
- [x] 0.1 Read PS.md and write `.agents/docs/extracted_requirements.md` (Done)
- [x] 0.2 Write `.agents/docs/architecture/system_overview.md` (Done)
- [x] 0.3 Write `.agents/docs/decisions/ADR-001-tech-stack.md` (Done)
- [x] 0.4 Write `.agents/docs/architecture/directory_structure.md` (Done)
- [x] 0.5 Set PLANNING_COMPLETE=true

## Phase 1 — Scaffold
- [x] 1.1 Create full directory skeleton (Backend skeleton done)
- [x] 1.2 `backend/requirements.txt` with pinned versions (Done via uv pyproject.toml)
- [x] 1.3 `frontend/package.json` — NextJS, TypeScript, Tailwind, React Query, etc. (Done)
- [x] 1.4 `docker-compose.yml` — backend + frontend dev servers (Done)
- [x] 1.5 `.env` setup in both backend and frontend (Done)
- [x] 1.6 Verify: backend starts (`uvicorn`), frontend starts (`npm run dev`) (Verified via scripts/verify_system.py)

## Phase 2 — Database Layer
- [x] 2.1 Define all Supabase table schemas (`user_profiles`, `user_personas`, etc.) (Completed)
- [ ] 2.2 Supabase Auth integration
- [ ] 2.3 SQLAlchemy async models (for local dev / tests)
- [x] 2.4 Run migrations / apply `schema.sql` via Supabase Dashboard (Completed)
- [x] 2.5 Seed script: `db/seed_data.py` (Completed)

## Phase 3 — Market Data ETL Pipeline
- [x] 3.1 `backend/etl/market_fetcher.py` — yfinance wrapper (Completed)
- [x] 3.2 Compute derived metrics (PE, PEG, ROE, RSI, SMA, MACD, Beta, Volatility) (Completed)
- [x] 3.3 `backend/etl/pipeline.py` — idempotent pipeline (Completed)
- [x] 3.4 Data quality verification after each run (Verified via audit/verify scripts)
- [x] 3.5 ETL tests (Manual verification successful)
- [x] 3.6 Sync with Supabase market_data (Completed)

## Phase 4 — Backend API
- [ ] 4.1 Auth endpoints (register, login via Supabase Auth)
- [x] 4.2 User profile ingestion (`POST /api/v1/users/profile`) (Completed)
- [x] 4.3 Persona logic: Risk score mapping + scoring_weight_profile (Completed)
- [x] 4.4 Portfolio Normalizer: Text-to-Weight logic (Completed)
- [x] 4.5 Seeding script: `scripts/seed_user.py` (Verified)
- [ ] 4.5 Advisory endpoint (gap detection vs ideal persona templates)
- [ ] 4.6 Stock analysis endpoint (Full 6-Lens Analysis: Funda, Tech, Val, Quant, Sent, Macro)
- [ ] 4.7 Scorecard output (Target 1, Target 2, Stop-loss, Entry zone, "Why for you")
- [ ] 4.8 Education/RAG endpoint (Explain concepts at Beginner, Intermediate, Confident levels)
- [ ] 4.9 Embedding generation + vector search (Supabase pgvector)
- [ ] 4.10 Seed pgvector with financial education content
- [ ] 4.11 Agent Lead PM setup (`agent/lead_pm.py` and `agent/prompt.py`)
- [ ] 4.12 LangChain strict tool wiring (`tools/` wrapping `services/`)
- [ ] 4.13 LLM client wrapper (Groq API, Llama-3-70B)
- [x] 4.14 Thesis Repo — `ai_investment_theses` table (Schema created)
- [ ] 4.15 Alerts creation endpoint
- [ ] 4.16 Alerts listing endpoint
- [ ] 4.17 Background alert checker

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

## Phase 7 — Hardening
- [ ] 7.1 Rate limiting on LLM-calling endpoints
- [ ] 7.2 Auth middleware on all `/api/v1/` routes
- [ ] 7.3 Input validation (Pydantic + Zod)
- [ ] 7.4 Secrets audit (no hardcoded values)
- [ ] 7.5 Structured JSON logging (structlog) + request ID propagation
- [ ] 7.6 Stale data warnings on analysis output (>24h)
- [ ] 7.7 Market data response caching (Redis or in-memory TTL)
- [ ] 7.8 Deployment: Vercel (frontend), Render/Railway (backend), Supabase (DB)
