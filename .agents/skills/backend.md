---
name: backend-patterns
description: >
  Backend architecture patterns for the AI Investment Intelligence platform.
  Stack: FastAPI + Uvicorn + Pydantic v2 + SQLAlchemy (async) + Supabase (PostgreSQL).
  Use for: creating API endpoints, writing services, defining Pydantic schemas,
  writing tests, calling external services (yfinance, OpenAI, Supabase).
  CRITICAL: also triggers when the agent references a model field or database column
  without verifying it exists in the model file.
  Triggers on: "add an endpoint", "write a route", "backend for X", "service for Y",
  "auth middleware", "database query".
---

# Backend Patterns — Investment Intelligence Platform

## Rule 1 — Never Reference Fields That Don't Exist

Before writing any endpoint or service:
1. Open the SQLAlchemy model file for that domain
2. Copy the exact field names
3. Only then write schemas, queries, or responses

If a field doesn't exist yet, add it to the model first and write a migration.

## Rule 2 — One Domain at a Time

For each domain, complete in this order before the next:
1. SQLAlchemy model (if changed)
2. Alembic migration (if model changed)
3. Pydantic schemas (request/response)
4. Service / business logic
5. Router / controller
6. Tests

Never mix domain work.

## Domain Structure

```
backend/
  routers/
    auth.py            ← POST /register, POST /login
    users.py           ← GET/PUT /users/me/profile
    portfolio.py       ← GET/PUT /users/me/portfolio
    advisory.py        ← POST /advisory/suggest
    analysis.py        ← POST /analysis/stock
    education.py       ← POST /education/explain
    agent.py           ← POST /agent/chat
    alerts.py          ← GET/POST /alerts
  schemas/
    auth.py            ← RegisterRequest, LoginResponse
    users.py           ← UserProfileRequest, UserPersonaResponse (score 0-100, label, weights)
    portfolio.py       ← PortfolioModelRequest (allocation ranges), GapAnalysisResponse
    advisory.py        ← AdvisoryRequest, AdvisoryRecommendation
    analysis.py        ← AnalysisRequest, StockScorecard (6-lens), AnalysisResponse
    education.py       ← ExplainRequest, ExplainResponse
    agent.py           ← ChatMessage, AgentResponse
    alerts.py          ← AlertCreate, AlertResponse
  services/
    user_service.py        ← risk_score_computation, persona_classification
    portfolio_service.py   ← gap_detection, diversification_logic
    advisory_service.py    ← recommendation generation
    analysis_service.py    ← multi-dimension stock scoring
    rag_service.py         ← embedding search + explanation generation
    agent_service.py       ← LangChain ReAct orchestration
    alert_service.py       ← alert creation, background checker
  models/
    user.py            ← UserProfile, UserPreferences SQLAlchemy models
    portfolio.py       ← PortfolioModel
    chat.py            ← ChatHistory
    market.py          ← MarketDataCache
    alert.py           ← Alert
  etl/
    market_fetcher.py  ← yfinance wrapper
    metrics.py         ← PE, PEG, RSI, etc. computation
    pipeline.py        ← idempotent daily pipeline
  tests/
    test_users.py
    test_advisory.py
    test_analysis.py
    test_agent.py
    test_agent_contract.py  ← NEVER DELETE
    test_etl.py
```

## Router Pattern

```python
# routers/analysis.py
from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_current_user
from ..schemas.analysis import AnalysisRequest, AnalysisResponse
from ..services import analysis_service

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])

@router.post("/stock", response_model=AnalysisResponse, status_code=200)
async def analyze_stock(
    data: AnalysisRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Run multi-dimension stock analysis.
    Returns scorecard, verdict (Buy/Wait/Avoid), entry, stop-loss, target.
    Always includes SEBI disclaimer in response.
    """
    return await analysis_service.analyze(db, user_id=current_user.id, request=data)
```

## Risk Score Computation

```python
# services/user_service.py
def compute_risk_score(age: int, horizon_months: int, risk_appetite: str, monthly_surplus: int) -> float:
    \"\"\"Returns risk score 0–100 based on exact weighted formula.\"\"\"
    # Horizon (30%), Appetite (35%), Age (20%), Surplus (15%)
    # [Implementation details to be fully built out according to PS.md]
    score = 50.0 # calculate based on weights
    return max(0.0, min(100.0, score))

def classify_persona(risk_score: float) -> str:
    if risk_score <= 30: return "Conservative Income Seeker"
    if risk_score <= 55: return "Balanced Growth Investor"
    if risk_score <= 75: return "Growth-Oriented Investor"
    return "Aggressive Wealth Builder"
```

## External Service Wrapper

Never call yfinance, OpenAI, Supabase, FAISS directly in routes or services.
Always wrap for mockability:

```python
# services/market_data_service.py
class MarketDataService:
    def __init__(self, fetcher=None):
        self._fetcher = fetcher or yfinance.Ticker

    def get_fundamentals(self, ticker: str) -> dict:
        try:
            t = self._fetcher(ticker)
            info = t.info
            return {
                "pe_ratio": info.get("trailingPE"),
                "peg_ratio": info.get("pegRatio"),
                "roe": info.get("returnOnEquity"),
            }
        except Exception as e:
            logger.error("market_data_fetch_failed", ticker=ticker, error=str(e))
            return {}  # safe default — never crash the pipeline

# In tests: MarketDataService(fetcher=MockYFinanceTicker)
```

## SEBI Disclaimer — Must Be in Every Analysis/Advisory Response

```python
# schemas/analysis.py
SEBI_DISCLAIMER = (
    "⚠️ Disclaimer: This analysis is for educational and informational purposes only. "
    "It does not constitute financial advice. Always consult a SEBI-registered investment "
    "advisor before making investment decisions."
)

class AnalysisResponse(BaseModel):
    ticker: str
    scorecard: StockScorecard
    verdict: Literal["Buy", "Wait", "Avoid"]
    entry_price: float | None
    stop_loss: float | None
    target_price: float | None
    justification: str
    disclaimer: str = SEBI_DISCLAIMER  # always included
    data_freshness: datetime
```

## Error Convention

```python
raise HTTPException(404, "Stock data not found for this ticker")
raise HTTPException(400, "Ticker symbol is required")
raise HTTPException(403, "Not your alert")
raise HTTPException(422, f"Invalid risk appetite value: {value}")
raise HTTPException(503, "Market data provider temporarily unavailable")
```

## Test Pattern

```python
@pytest.mark.asyncio
async def test_analyze_stock_success(client, auth_token):
    r = await client.post(
        "/api/v1/analysis/stock",
        json={"ticker": "HDFCBANK.NS"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] in ("Buy", "Wait", "Avoid")
    assert 0 <= body["scorecard"]["overall"] <= 10
    assert "disclaimer" in body
    assert body["disclaimer"].startswith("⚠️")

@pytest.mark.asyncio
async def test_analyze_stock_unauthenticated(client):
    r = await client.post("/api/v1/analysis/stock", json={"ticker": "HDFCBANK.NS"})
    assert r.status_code == 401
```

## Anti-Patterns — Never

- Reference a model field without opening the model file first
- Write business logic in a router (routers: HTTP only)
- Call yfinance, OpenAI, or Supabase without wrapping in a class
- Skip tests before moving to the next domain
- Use 500 for domain errors — always use specific HTTP codes
- Return an analysis response without the disclaimer field
- Crash the pipeline on a single model or API failure
