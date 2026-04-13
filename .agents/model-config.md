# Model Configuration

## Routing Table

| Task | Model | Reason |
|------|-------|--------|
| Agent orchestration / ReAct reasoning | `claude-sonnet-4-6` | Best multi-step instruction following |
| Stock analysis engine (complex prompt) | `claude-sonnet-4-6` | Nuanced financial reasoning |
| RAG explanation / educational prose | `claude-sonnet-4-6` | Better at clear, natural explanation |
| Structured extraction (JSON output) | `claude-sonnet-4-6` | Strongest instruction-following |
| High-volume batch scoring | `gemini-pro-flash` | Cost-effective for bulk metric parsing |
| Embedding generation | `sentence-transformers/all-MiniLM-L6-v2` | Local, fast, no API cost |
| Code generation (development) | `claude-sonnet-4-6` | Best for code |

## Fallback Policy

If primary model fails → retry once with exponential backoff → try secondary model →
return safe default response.

**Never fail the whole pipeline because one LLM call failed.**

For agent: if tool call fails → log error → skip that tool → continue reasoning with available context.
For stock analysis: if LLM step fails → return partial scorecard with `"unavailable"` on failed dimension.
For RAG: if vector search fails → return LLM response without retrieved context (still useful).

## Cost Controls

- Always set `max_tokens` explicitly on every LLM call.
- Development / test: use `LLM_MOCK=true` — never make real API calls in tests.
- Log estimated token usage per request to monitor costs.
- Set daily spend alerts in OpenAI dashboard.

## Mocking

Set `LLM_MOCK=true` in `.env.test`.
All LLM client wrappers check this flag and return deterministic fixture responses.

```python
# backend/services/llm_client.py
import os

class LLMClient:
    def __init__(self, client=None):
        self._mock = os.getenv("LLM_MOCK") == "true"
        self._client = client or openai.AsyncOpenAI()

    async def complete(self, prompt: str, max_tokens: int = 1000) -> str:
        if self._mock:
            return '{"verdict": "Wait", "score": 6, "reason": "Mock response."}'
        try:
            response = await self._client.chat.completions.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("llm_failed", error=str(e))
            return ""  # never crash the pipeline
```

## Environment Variables Required

```
OPENAI_API_KEY=
LLM_MODEL_PRIMARY=gpt-4o              # or claude-sonnet-4-6 via proxy
LLM_MODEL_BATCH=gpt-4o-mini
LLM_MAX_TOKENS=2000
LLM_MOCK=false                        # set true in .env.test
```
