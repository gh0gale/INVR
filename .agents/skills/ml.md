---
name: ml-pipeline
description: >
  ML and LLM pipeline patterns for the AI Investment Intelligence platform.
  Use when building or modifying: the ReAct agent, LLM client wrapper, RAG pipeline,
  stock analysis engine, investor persona classifier, or risk scoring logic.
  Triggers on: "add a model", "LLM integration", "ReAct agent", "RAG pipeline",
  "stock analysis engine", "scoring logic", "wrap the model", "agent tool",
  "persona classifier", "embedding generation".
  CRITICAL: also triggers when the agent attempts to call OpenAI, LangChain tools,
  or FAISS directly without a wrapper class.
---

# ML Pipeline Patterns — Investment Intelligence Platform

## Core Rule — Wrap Everything

Every model, LLM call, or vector DB call must be wrapped in a class that:
1. Takes its client/model as a constructor argument (injectable mock)
2. Has typed input and output (Pydantic models)
3. Handles its own exceptions — never propagate crashes to the pipeline
4. Checks `LLM_MOCK=true` before making real API calls

## LLM Client Wrapper

```python
# backend/services/llm_client.py
import os
import openai
import structlog

logger = structlog.get_logger()

class LLMClient:
    def __init__(self, client=None):
        self._mock = os.getenv("LLM_MOCK") == "true"
        self._model = os.getenv("LLM_MODEL_PRIMARY", "gpt-4o")
        self._max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))
        self._client = client or openai.AsyncOpenAI()

    async def complete(self, prompt: str, max_tokens: int | None = None) -> str:
        if self._mock:
            return '{"verdict": "Wait", "score": 6, "reason": "Mock response for testing."}'
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens or self._max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("llm_complete_failed", error=str(e))
            return ""  # never crash the pipeline

    async def complete_json(self, prompt: str, max_tokens: int | None = None) -> dict:
        import json
        raw = await self.complete(prompt, max_tokens)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error("llm_json_parse_failed", raw=raw[:200])
            return {}  # safe default
```

## ReAct Agent — Tool Registration Pattern

```python
# backend/services/agent_service.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI

def build_agent(
    llm=None,
    market_data_svc=None,
    rag_svc=None,
    analysis_svc=None,
    portfolio_svc=None,
) -> AgentExecutor:
    llm = llm or ChatOpenAI(model=os.getenv("LLM_MODEL_PRIMARY", "gpt-4o"))

    tools = [
        Tool(
            name="market_data",
            description="Fetch current price, PE, PEG, RSI, moving averages for a stock ticker.",
            func=lambda ticker: market_data_svc.get_summary(ticker),
        ),
        Tool(
            name="portfolio_analyzer",
            description="Analyse user's portfolio sectors for gaps and concentration risk.",
            func=lambda user_id: portfolio_svc.analyze(user_id),
        ),
        Tool(
            name="rag_search",
            description="Retrieve educational explanations for financial concepts (PE, PEG, RSI, etc.) mapped to 3 Literacy Levels (Beginner, Intermediate, Confident).",
            func=lambda query, level: rag_svc.search(query, literacy_level=level),
        ),
        Tool(
            name="stock_analysis",
            description="Run full multi-dimension stock analysis (6 lenses) + 'Why For You' context alignment.",
            func=lambda ticker: analysis_svc.analyze(ticker),
        ),
    ]

    agent = create_react_agent(llm, tools, prompt=INVESTMENT_AGENT_PROMPT)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
```

## RAG Pipeline

```python
# backend/services/rag_service.py
from sentence_transformers import SentenceTransformer
import faiss, numpy as np

class RAGService:
    def __init__(self, model=None, index=None, documents=None):
        self._encoder = model or SentenceTransformer("all-MiniLM-L6-v2")
        self._index = index   # FAISS index loaded at startup
        self._documents = documents or []  # parallel list of doc strings

    def search(self, query: str, top_k: int = 3) -> list[str]:
        try:
            vec = self._encoder.encode([query]).astype("float32")
            _, indices = self._index.search(vec, top_k)
            return [self._documents[i] for i in indices[0] if i < len(self._documents)]
        except Exception as e:
            logger.error("rag_search_failed", error=str(e))
            return []  # degrade gracefully — LLM still answers without context

    def build_index(self, documents: list[str]):
        """Call once at startup or when seeding new content."""
        embeddings = self._encoder.encode(documents).astype("float32")
        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatL2(dim)
        self._index.add(embeddings)
        self._documents = documents
```

## Stock Analysis Engine — Multi-Dimension Scoring

```python
# backend/services/analysis_service.py
from dataclasses import dataclass

@dataclass
class StockScorecard:
    fundamental: int  # 0–10
    technical: int    # 0–10
    valuation: int    # 0–10
    quant_risk: int   # 0–10
    sentiment: int    # 0–10
    macro: int        # 0–10
    
    def overall(self, persona_weights: dict) -> float:
        # persona_weights injected from user_personas.scoring_weight_profile
        # dict example: {"fundamental": 0.35, "valuation": 0.25, ...}
        scores  = {"fundamental": self.fundamental, "technical": self.technical,
                   "valuation": self.valuation, "quant_risk": self.quant_risk,
                   "sentiment": self.sentiment, "macro": self.macro}
        return round(sum(w * scores[key] for key, w in persona_weights.items()), 1)

    def verdict(self, overall_score: float, overridden_to_wait: bool = False) -> str:
        if overridden_to_wait: return "Wait" # Downgraded due to concentration rules
        if overall_score >= 7.5: return "Strong Buy"
        if overall_score >= 6.5: return "Buy"
        if overall_score >= 5.5: return "Wait"
        if overall_score >= 4.0: return "Weak/Watchlist"
        return "Avoid"

class AnalysisService:
    def __init__(self, llm_client=None, market_data_svc=None):
        self._llm = llm_client or LLMClient()
        self._market = market_data_svc or MarketDataService()

    async def analyze(self, ticker: str, user_context: dict) -> dict:
        try:
            # 1. Fetch
            metrics = self._market.get_all_metrics(ticker)
            # 2. Score via LLM engine based on PS.md rules
            scorecard = await self._score_all_dimensions(ticker, metrics)
            # 3. Calculate weighted composite
            persona_weights = user_context.get("scoring_weight_profile", {})
            overall = scorecard.overall(persona_weights)
            # 4. Context Override Check
            overridden = user_context.get("concentration_flags", {}).get(metrics.sector, False)
            verdict = scorecard.verdict(overall, overridden)
            
            return {
                "scorecard": scorecard,
                "verdict": verdict,
                "overall": overall,
                "why_for_you": "Generated paragraph explaining fit...",
                "disclaimer": SEBI_DISCLAIMER,
            }
        except Exception as e:
            logger.error("analysis_failed", ticker=ticker, error=str(e))
            return {"scorecard": None, "verdict": "unavailable", "disclaimer": SEBI_DISCLAIMER}
```

## Output Contract Test — NEVER DELETE

```python
# tests/test_agent_contract.py
"""
THIS FILE ENFORCES THE AI OUTPUT CONTRACT.
NEVER DELETE THIS TEST.
If the output shape changes: update AGENT.md AND this test together.
"""
import pytest

@pytest.mark.asyncio
async def test_analysis_contract(mock_request):
    result = await analysis_service.analyze("HDFCBANK.NS", user_context={})
    assert result["verdict"] in ("Buy", "Wait", "Avoid", "unavailable")
    if result["scorecard"]:
        sc = result["scorecard"]
        for dim in ("macro", "sector", "fundamental", "valuation", "technical", "risk"):
            assert 0 <= getattr(sc, dim) <= 10
    assert "disclaimer" in result
    assert result["disclaimer"].startswith("⚠️")

@pytest.mark.asyncio
async def test_agent_contract(mock_agent_executor):
    response = await agent_service.chat("Should I invest in HDFC Bank?", user_id="u1", session_id="s1")
    assert isinstance(response.message, str)
    assert len(response.message) > 0
    assert isinstance(response.sources, list)
```

## Exception Policy

```python
# In each wrapper — return safe default, never raise:
except Exception as e:
    logger.error("step_failed", step=self.__class__.__name__, error=str(e))
    return self._safe_default()

# In pipeline — degrade gracefully:
# LLM step fails → score that dimension as 0, add "unavailable" to explanation
# RAG fails → skip retrieved context, LLM answers from training knowledge
# Market data fails → return cached data if <24h old, else error with explanation
# All steps fail → verdict = "unavailable", recommend human advisor, do not crash
```

## Anti-Patterns — Never

- Call OpenAI, FAISS, or yfinance directly in routes or services (always wrap)
- Make real LLM or API calls in tests (use `LLM_MOCK=true`)
- Let an exception propagate and crash the agent pipeline
- Delete `tests/test_agent_contract.py`
- Hardcode model names or API keys — always read from env vars
- Return a verdict without the accompanying disclaimer
