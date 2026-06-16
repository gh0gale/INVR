# INVR Backend — Full System Diagnosis

## The Primary Bug (Why `/stream` Gets Stuck)

**File:** [`tutor_graph.py`](file:///c:/codes/INVR/INVR/backend/app/pipeline/tutor_graph.py)  
**Location:** `generation_node`, line 75  
**Symptom:** Server prints `[Tutor] Generating response via mode: SCENARIO...` then hangs forever with no output.

### Root Cause: Sync `.ainvoke()` Call Without Streaming Handoff

```python
# Line 75 — CURRENT (BROKEN)
response = await llm.ainvoke(messages)          # waits for the COMPLETE response first
return {"messages": [response]}                  # only then returns it
```

`llm` is initialized with `streaming=True` (line 46), but then `.ainvoke()` is used instead of an async generator. This means:

1. `streaming=True` on `ChatOllama` has **no effect** when you call `.ainvoke()` — it waits for the full response before returning.
2. The `event_generator()` in `tutor.py` calls `tutor_graph.astream(..., stream_mode="messages")` — this correctly wires up LangGraph's streaming. However, the `generation_node` itself never **yields** tokens; it blocks waiting for the full response from Ollama.
3. For a typical LLM response from a local Llama 3.1 model, generating 300–500 tokens at ~20 tok/sec takes **15–25 seconds** with zero output, which appears to the caller as a hang.
4. **FastAPI's streaming response connection** can time out or the client closes it during this silence window, which is why the server shows `200 OK` immediately (the `StreamingResponse` object was returned) but the client gets nothing.

The fix requires using `llm.astream(messages)` and yielding chunks directly. But since you're in a LangGraph node (not directly in the route), the correct approach is to use `stream_mode="messages"` properly — which requires the **node itself to call `llm` via streaming**, not `ainvoke`.

---

## Bug #2: Blocking Sync Call in Async Pipeline (`orchestrator.py`)

**File:** [`orchestrator.py`](file:///c:/codes/INVR/INVR/backend/app/orchestrator.py)  
**Location:** `llm_synthesizer_node`, lines 52–119  
**Severity:** HIGH — Blocks the entire async event loop

```python
# Line 108 — CURRENT (BROKEN)
def llm_synthesizer_node(state: AnalysisState) -> AnalysisState:   # <-- sync def
    ...
    response = chain.invoke({...})   # <-- sync, blocking call to Ollama
```

The `llm_synthesizer_node` is a **synchronous** function that calls `chain.invoke()` — a fully blocking network call to the local Ollama server. LangGraph runs this in the same async event loop managed by uvicorn.

- A single request to `/process` blocks the uvicorn event loop for the entire duration of Ollama's inference (~10–30 seconds for Llama 3.1).
- **No other requests can be served** while this is running.
- This is also why `/process` appears to "work" (returns `200 OK`) but freezes the server: the node runs synchronously on the event loop thread.

**Fix:** Either change the function to `async def` and use `await chain.ainvoke({...})`, or wrap it in `await asyncio.to_thread(chain.invoke, {...})`.

---

## Bug #3: Duplicate Field Definition in `SilverMetrics` Schema

**File:** [`schemas/silver.py`](file:///c:/codes/INVR/INVR/backend/app/schemas/silver.py)  
**Location:** Lines 15–18  
**Severity:** MEDIUM — Silent data loss (Pydantic keeps only the last definition)

```python
# Lines 15-18 — DUPLICATED
sma_20: Optional[float] = None   # Line 15  <-- under "Core Technical Metrics"
...
sma_20: Optional[float] = None   # Line 18  <-- DUPLICATE under a second "Core Technical Metrics" comment
```

`sma_20` is defined twice. Python classes resolve this by keeping the last definition. While Pydantic won't crash, this is a latent bug: the first section header comment says "Core Technical Metrics" and then the second block also says "Core Technical Metrics" — the schema is clearly in an incomplete/copy-paste state. If someone adds a field between the two `sma_20` lines, it will silently vanish.

---

## Bug #4: `bronze_service.py` — `institutional_activity` Hardcoded to `None`

**File:** [`bronze_service.py`](file:///c:/codes/INVR/INVR/backend/app/services/bronze_service.py)  
**Location:** Lines 81–96  
**Severity:** MEDIUM — `inst_activity` is built but never used

```python
# Lines 81-95
inst_activity = None
if manifest["needs_institutional"]:
    inst_activity = {
        "fii_net_activity": 125.5,
        "dii_net_activity": -40.2
    }

return BronzePayload(
    ...
    institutional_activity=None   # <-- inst_activity is NEVER passed, always None
)
```

The variable `inst_activity` is populated correctly when `needs_institutional=True`, but the `BronzePayload` return call hardcodes `institutional_activity=None`. So `silver_service.py`'s swing-timeframe logic that reads `inst.get("fii_net_activity", 0.0)` will always receive an empty dict, and `institutional_bias` will always be `"neutral"` regardless of actual data.

---

## Bug #5: `fetch_nse_circuit_status` — `upper` and `lower` Are Set to the Same Value

**File:** [`integrations/market_data.py`](file:///c:/codes/INVR/INVR/backend/app/integrations/market_data.py)  
**Location:** Lines 47–48  
**Severity:** MEDIUM — Circuit detection is broken; `lower` circuit can never be triggered

```python
upper = quote.get('priceInfo', {}).get('intraDayHighLow', {}).get('value')
lower = upper  # Simplifying for prototype if exact lower isn't found
```

`lower` is assigned the same value as `upper`. The subsequent check `if current_price <= (lower * 1.005)` compares the current price against the **upper** circuit limit — which will virtually never be true for a lower circuit condition. This means the `BLOCK` verdict for lower circuits will almost never fire.

---

## Bug #6: `EPS CAGR` Calculated on Scaled Data (Incorrect Units)

**File:** [`integrations/market_data.py`](file:///c:/codes/INVR/INVR/backend/app/integrations/market_data.py)  
**Location:** Lines 91–95  
**Severity:** HIGH — EPS CAGR figure will be wildly wrong

```python
# EPS is derived by dividing Net Income (in absolute rupees) by 1e8
"eps": [inc / 1e8 for inc in (net_inc[-5:] if len(net_inc) >= 5 else net_inc)]
```

EPS (Earnings Per Share) = Net Income / Shares Outstanding. Dividing by `1e8` is arbitrary and has no relationship to the actual share count of RELIANCE.NS (which has ~6.77 billion shares outstanding). This produces a completely fictional EPS series, and by extension, the `eps_cagr_5y` calculated in `silver_service.py` will be garbage — even though it passes through the `eps_growth` hard gate in `gold_service.py`.

---

## Bug #7: `revenue_cagr_5y` Fallback Returns YoY Growth (Not 5Y CAGR)

**File:** [`silver_service.py`](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py)  
**Location:** Lines 141–145  
**Severity:** MEDIUM — Metric semantics mismatch

```python
rev_5y = calculate_cagr(inc.get("revenue", []))
m["revenue_cagr_5y"] = rev_5y if rev_5y is not None else float(f.get("revenueGrowth", 0.0))
```

If yfinance can't supply 5 years of revenue history (common for some tickers), the fallback is `revenueGrowth` from `info` — which is a **year-over-year percentage** (e.g., `0.12` = 12% last year), not a 5-year CAGR. The `eps_cagr_5y` field has the same problem. Downstream LLM analysis will describe these as "5-year CAGRs" when they're actually single-year figures.

---

## Bug #8: `stream_mode="messages"` Returns `(chunk, metadata)` Tuples — But Only for AI Message Chunks

**File:** [`tutor.py`](file:///c:/codes/INVR/INVR/backend/app/api/routes/tutor.py)  
**Location:** Lines 27–32  
**Severity:** MEDIUM — Stream silently emits nothing if `generation_node` uses `ainvoke`

```python
async for chunk, metadata in tutor_graph.astream(initial_state, stream_mode="messages"):
    if metadata.get("langgraph_node") == "generate":
        if chunk.content:
            yield f"data: {json.dumps({'token': chunk.content})}\\n\\n"
```

This streaming wiring is correct **only if** the `generation_node` itself uses `llm.astream()`. Since `generation_node` uses `llm.ainvoke()` (Bug #1), the "messages" mode will yield a single complete `AIMessage` object — not incremental token chunks. The `chunk.content` will be a full multi-sentence paragraph in one shot, which technically works but destroys the token-by-token streaming UX.

---

## Bug #9: No Session State — `session_id` in `ChatRequest` Is Never Used

**File:** [`schemas/tutor.py`](file:///c:/codes/INVR/INVR/backend/app/schemas/tutor.py) + [`tutor.py`](file:///c:/codes/INVR/INVR/backend/app/api/routes/tutor.py)  
**Severity:** LOW — Feature gap, not a crash bug

The `ChatRequest` schema accepts a `session_id`, but neither the route nor the graph does anything with it. Every request starts with a fresh `HumanMessage` only — there's no conversation history retrieval. Multi-turn conversation (e.g., follow-up questions) is not actually supported despite the schema suggesting it.

---

## Bug #10: `sector_history` Missing for `RELIANCE.NS` — RS Gate Is Always Skipped

**File:** [`bronze_service.py`](file:///c:/codes/INVR/INVR/backend/app/services/bronze_service.py)  
**Location:** Lines 69–78  
**Severity:** MEDIUM — Sector RS metric silently absent for Reliance

```python
SECTOR_INDEX_MAP = {
    "Auto": "^CNXAUTO",
    "IT": "^CNXIT",
    "Bank": "^NSEBANK",
    "Financial Services": "^CNXFIN",
    "FMCG": "^CNXFMCG"
}
```

RELIANCE.NS belongs to the **"Energy"** sector (as returned by yfinance). `"Energy"` is not in `SECTOR_INDEX_MAP`, so `index_ticker` is `None`, `sector_df` stays `None`, and `silver_service.py` skips all sector RS and `market_regime` computation entirely. For `long_term` timeframe, this means `stock_vs_sector_rs` and `market_regime` are both absent from the output — the LLM gets no macro context for one of the most commonly queried stocks.

---

## Bug #11: `sma_200` Computed for Long-Term But Gate Label Is Misleading ("200-week SMA")

**File:** [`gold_service.py`](file:///c:/codes/INVR/INVR/backend/app/services/gold_service.py) + [`silver_service.py`](file:///c:/codes/INVR/INVR/backend/app/services/silver_service.py)  
**Severity:** LOW — Misleading output, not a crash

For `long_term`, yfinance data is fetched with `interval="1wk"`. `sma_200` is computed by `rolling(200)` on this weekly data — making it a **200-week (~4 year) SMA**, not the standard 200-day SMA.

The gold service `watch_list` then appends: `"Wait for structural recovery above the 200-week SMA"` — which is technically accurate for the weekly interval, but the label in `GATE_NAMES` is `"Long-Term Trend (200 DMA)"` (DMA = Daily Moving Average), which is wrong and will mislead the user.

---

## Summary Table

| # | File | Issue | Severity |
|---|------|--------|----------|
| 1 | `tutor_graph.py` L75 | `ainvoke` instead of `astream` — **root cause of hang** | 🔴 CRITICAL |
| 2 | `orchestrator.py` L44 | Sync `chain.invoke()` blocks the async event loop | 🔴 HIGH |
| 3 | `schemas/silver.py` L15,18 | `sma_20` defined twice | 🟡 MEDIUM |
| 4 | `bronze_service.py` L95 | `inst_activity` built but `institutional_activity=None` hardcoded | 🟡 MEDIUM |
| 5 | `integrations/market_data.py` L48 | `lower = upper` — lower circuit check is broken | 🟡 MEDIUM |
| 6 | `integrations/market_data.py` L94 | EPS scaled by `1e8` instead of real share count | 🔴 HIGH |
| 7 | `silver_service.py` L142,145 | Fallback uses YoY growth instead of CAGR | 🟡 MEDIUM |
| 8 | `tutor.py` L27 | `stream_mode="messages"` streaming wiring only works with `astream` in node | 🔴 HIGH |
| 9 | `schemas/tutor.py` / `tutor.py` | `session_id` accepted but never used; no multi-turn memory | 🟢 LOW |
| 10 | `bronze_service.py` L16-22 | RELIANCE sector "Energy" not in `SECTOR_INDEX_MAP`; RS gate skipped | 🟡 MEDIUM |
| 11 | `gold_service.py` L154 | Gate label says "200 DMA" but data is weekly (200-week SMA) | 🟢 LOW |
