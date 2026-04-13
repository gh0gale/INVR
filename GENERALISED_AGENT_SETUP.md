# Generalised AI Agent Project Setup
# Works for any project — web app, API, ML system, data pipeline, mobile, infra

---

## THE UNIVERSAL FOLDER STRUCTURE

```
your-project/
│
├── .agents/                         ← Everything the agent needs. Full stop.
│   │
│   ├── AGENT.md                     ← Primary instruction file
│   ├── TODO.md                      ← Session memory + progress tracker
│   ├── PS.md                        ← Problem statement
│   │
│   ├── context-sync.md              ← Rolling one-line-per-session state log
│   ├── human_in_the_loop.md         ← Decisions needing human sign-off
│   ├── model-config.md              ← Which model does what (if using multiple)
│   │
│   ├── skills/
│   │   ├── ui.md                    ← UI component patterns
│   │   ├── frontend.md              ← Frontend patterns + anti-hallucination
│   │   ├── backend.md               ← Backend patterns + stay-on-point
│   │   ├── ml.md                    ← ML/AI pipeline patterns
│   │   ├── etl.md                   ← Data pipeline patterns
│   │   └── skill-creator.md         ← How to build new skills
│   │
│   └── docs/                        ← Agent writes everything here in Phase 0
│       ├── extracted_requirements.md
│       ├── implementation_plan.md
│       ├── architecture/
│       │   ├── system_overview.md
│       │   └── directory_structure.md
│       └── decisions/
│           └── ADR-001-tech-stack.md
│
├── .env.example                     ← All env vars, no real values
├── .gitignore                       ← .agents/ is gitignored by default
│
└── [source code]                    ← Decided by agent in Phase 0
    └── backend/ frontend/ src/ ...
```

**The only things that are fixed:** the 4 root files, `.agents/`, `.skills/`, and `docs/`.
Everything else — `backend/`, `frontend/`, `src/`, `api/` — is decided in Phase 0.

---

## TEMPLATE 1 — AGENT.md (universal)

Copy this. Fill in the bracketed sections for your project.

```markdown
# AGENT.md — [Project Name]

You are a [senior engineer / AI architect / full-stack developer] building [one-sentence
description]. Your job is to plan first, then implement — making every structural decision
explicit and traceable before writing production code.

Read this file fully before doing anything. Follow phases in order. Do not skip ahead.

---

## Session Protocol

**Start of every session:**
1. Read this file top to bottom.
2. Run `cat TODO.md` — continue from next unchecked item.
3. If confused about current state, read `.agents/context-sync.md`.

**End of every session:**
1. Update `TODO.md` — check off done items, add newly discovered work.
2. Run all tests touched this session. Fix regressions before stopping.
3. Commit with conventional message: `feat(scope): description`
4. Append one line to `.agents/context-sync.md` summarising what changed.

**When uncertain about a design decision:**
- Do NOT guess silently.
- Write `docs/decisions/ADR-NNN-topic.md` using the template below.
- Pick the most defensible default, note it in the ADR, continue.
- Add to `TODO.md` under `## Needs Human Review`.

**When you feel yourself drifting from the plan:**
- Stop. Re-read this file from the top.
- Re-read `TODO.md`.
- Resume from next unchecked item only.

**ADR template:**
# ADR-NNN: [Topic]
## Context — why this decision is needed
## Options considered
## Decision — what we're doing and why
## Consequences — what this makes easier or harder

---

## Users

[Name each user type. 2–3 sentences each: tech level, environment, needs, language.]

- **[User A]** — ...
- **[User B]** — ...

---

## Phase 0 — Plan Before You Build

No application code until all of these exist.

### 0.1 Extract Requirements
Read `PS.md`. Write `docs/extracted_requirements.md`:
- Functional requirements — grouped by user type
- Non-functional requirements — scale, latency, language, offline, bandwidth
- AI/ML requirements — list each explicitly (only if the system has AI)
- Ambiguities — list, do NOT assume answers

### 0.2 Map the System
Write `docs/architecture/system_overview.md`:
- All services/modules and which calls which
- End-to-end data flow: "user does X" → "system does Y" → "user sees Z"

### 0.3 Tech Stack Decision
Write `docs/decisions/ADR-001-tech-stack.md`.
Justify every choice against the non-functional requirements.

### 0.4 Directory Structure
Write `docs/architecture/directory_structure.md` — full intended tree.
One-line purpose comment per directory. Do not create directories yet.

### 0.5 Gate
Only when 0.1–0.4 are all written: set `PLANNING_COMPLETE=true` in `TODO.md`.
Then begin Phase 1.

---

## Phase 1 — Scaffold
[List the specific scaffold steps for your project type:
- Directory creation
- Config files
- Environment setup
- Docker / package files
- Verify step]

## Phase 2 — [Core Layer]
[Database / Data models / Schema — whatever is foundational for your project]

## Phase 3 — [Main Feature Layer]
[API endpoints / Business logic / Core services]

## Phase 4 — [Secondary Layer]
[AI engine / Background tasks / Integrations — if applicable]

## Phase 5 — [UI Layer]
[Frontend screens / CLI / Dashboard — whatever the user sees]

## Phase 6 — [Quality]
[Testing, i18n, accessibility, localisation — if applicable]

## Phase 7 — Hardening
[Security, rate limiting, observability, performance]

---

## Non-Negotiable Rules

These apply in every file, every phase, always:

1. Never hardcode secrets, URLs, or credentials. Always read from config.
2. Every endpoint/function needs at least one test before moving on.
3. Wrap all external dependencies (APIs, models, storage) for mockability.
4. Never silently resolve a design ambiguity — write an ADR.
5. Run all tests at end of every phase. Fix regressions before moving on.
6. Keep `TODO.md` current every session.
7. Keep `.agents/context-sync.md` current every session.
8. When in doubt about scope: re-read this file. Do not invent requirements.

[Add project-specific rules here, e.g.:]
[9. The AI output contract test must never be deleted.]
[10. On any pipeline exception: log, set record to REVIEW, do not crash worker.]
```

---

## TEMPLATE 2 — TODO.md (universal)

```markdown
# TODO — [Project Name]

PLANNING_COMPLETE=false

## Phase 0 — Planning
- [ ] 0.1 Write `docs/extracted_requirements.md`
- [ ] 0.2 Write `docs/architecture/system_overview.md`
- [ ] 0.3 Write `docs/decisions/ADR-001-tech-stack.md`
- [ ] 0.4 Write `docs/architecture/directory_structure.md`
- [ ] 0.5 Set PLANNING_COMPLETE=true

## Phase 1 — Scaffold
- [ ] 1.1 Create directory skeleton from 0.4
- [ ] 1.2 Config files + `.env.example`
- [ ] 1.3 Infrastructure (docker-compose / package.json / requirements.txt)
- [ ] 1.4 Verify startup

## Phase 2 — [Core Layer]
- [ ] 2.1 ...
- [ ] 2.2 ...

## Phase 3 — [Main Feature Layer]
- [ ] 3.1 ...

## Phase 4 — [Secondary Layer]
- [ ] 4.1 ...

## Phase 5 — [UI Layer]
- [ ] 5.1 ...

## Phase 6 — [Quality]
- [ ] 6.1 ...

## Phase 7 — Hardening
- [ ] 7.1 Security controls
- [ ] 7.2 Performance + indexes
- [ ] 7.3 Observability + logging

## Needs Human Review
<!-- Agent adds items here. Human removes only after reviewing. -->
```

---

## TEMPLATE 3 — .agents/context-sync.md

```markdown
# Context Sync

Format: `YYYY-MM-DD: [what changed or was decided]`
Agent appends one line at end of every session. Never delete old entries.

[DATE]: Project initialised. AGENT.md, PS.md, TODO.md created. Planning not started.
```

---

## TEMPLATE 4 — .agents/human_in_the_loop.md

```markdown
# Human In The Loop

Decisions requiring human sign-off before agent proceeds.
Agent adds items. Human removes after reviewing.

## Open
<!-- - [ ] [DATE]: [what the agent is blocked on] -->

## Resolved
<!-- Move resolved items here with outcome -->
```

---

## TEMPLATE 5 — .agents/model-config.md (only if using LLMs)

```markdown
# Model Configuration

## Routing Table

| Task | Model | Reason |
|------|-------|--------|
| Code generation | Claude (claude-sonnet-*) | Best for code |
| Structured extraction | Claude | Best instruction-following |
| High-volume batch | Gemini Pro / Flash | Cost-effective |
| Multimodal / PDF | Gemini Pro | Strong multimodal |
| Explanation / prose | Claude | Better nuanced text |

## Fallback Policy
If primary model fails → retry once → try secondary → return safe default.
Never fail the whole pipeline because one LLM call failed.

## Cost Controls
- Always set max_tokens explicitly
- Never make LLM calls in tests — use LLM_MOCK=true

## Mocking
Set LLM_MOCK=true in .env.test.
Router returns deterministic fixture responses when flag is set.
```

---

## SKILL TEMPLATE 1 — .skills/ui/SKILL.md

```markdown
---
name: ui-component-generator
description: >
  Generates production-ready UI components with correct props, state handling,
  accessibility, and i18n wiring. Use whenever building any screen, component,
  form, card, modal, table, or interactive element. Triggers on: "build a screen",
  "create a component", "make a form", "add a modal", "UI for X", "design the
  [screen name]", or any request involving visual interface elements.
---

# UI Component Generator

## Before Writing Any Component

Answer these first:
- Which user type sees this?
- What data does it display? (list the fields)
- What actions can the user take? (list the events)
- What language(s) must it support?
- What are the loading, empty, and error states?

## Every Component Must Have

1. Typed props interface (TypeScript) or equivalent
2. Loading state — never render nothing while waiting
3. Empty state — never leave a blank screen
4. Error state — never let it crash silently
5. All user-visible strings in i18n keys, never hardcoded
6. ARIA labels on every interactive element

## Screen Component Pattern

```typescript
import { useTranslation } from 'react-i18next';
import { useData } from '@/hooks/useData';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { EmptyState } from '@/components/EmptyState';
import { ErrorBanner } from '@/components/ErrorBanner';

interface ScreenProps { id: string; }

export function MyScreen({ id }: ScreenProps) {
  const { t } = useTranslation();
  const { data, isLoading, error } = useData(id);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorBanner message={t('errors.load_failed')} />;
  if (!data.length) return <EmptyState message={t('screen.empty')} />;

  return (
    <main role="main" aria-label={t('screen.aria_label')}>
      <h1>{t('screen.title')}</h1>
      {data.map(item => <ItemCard key={item.id} item={item} />)}
    </main>
  );
}
```

## i18n Key Convention

```
{user_type}.{screen}.{element}
admin.dashboard.title
customer.orders.empty_state
partner.upload.submit_button
```

## Anti-Patterns — Never

- Hardcode any user-facing string
- Fetch data directly inside a component — use a hook
- Return `null` for loading/error states
- Use `any` type in TypeScript
- Mix business logic with rendering in the same file

## Component File Structure

```
ComponentName/
  index.tsx          ← component
  ComponentName.test.tsx
  ComponentName.types.ts
```
```

---

## SKILL TEMPLATE 2 — .skills/frontend/SKILL.md

```markdown
---
name: frontend-patterns
description: >
  Frontend architecture patterns, anti-hallucination guardrails, stay-on-point
  rules, and data-fetching conventions. Use for: API integration, state management,
  routing, form handling, custom hooks. CRITICAL: also use whenever the agent
  seems to be inventing API shapes or drifting from the current TODO phase. Triggers
  on: "wire up the API", "connect to backend", "add state for", "create a hook",
  "frontend for X", or when the agent references a field or endpoint without
  verifying it exists.
---

# Frontend Patterns

## Rule 1 — Never Invent API Shapes

Before writing ANY API call, the agent must:
1. Read the backend router file for that domain
2. Copy the exact endpoint path, method, request body fields, and response fields
3. Only then write the frontend API call

If the backend route doesn't exist yet:
```typescript
// TODO: endpoint not yet implemented — Phase 3.2
// Expected: POST /api/v1/orders with { puja_type_id, scheduled_at }
const mockOrder = { id: 'mock', status: 'PENDING' };
```

## Rule 2 — Stay On Point

If you find yourself building something not in the current TODO phase:
1. Stop
2. Add it to TODO.md under the correct future phase
3. Return to the current task

## API Layer — All calls go through src/api/

```typescript
// src/api/orders.ts
import { apiClient } from './client';
import type { Order, CreateOrderInput } from './types';

export const ordersApi = {
  list: (params?: { status?: string }) =>
    apiClient.get<Order[]>('/api/v1/orders/', { params }),
  getById: (id: string) =>
    apiClient.get<Order>(`/api/v1/orders/${id}`),
  create: (data: CreateOrderInput) =>
    apiClient.post<Order>('/api/v1/orders/', data),
};
```

Never call fetch/axios directly in a component or hook.

## Data Fetching — React Query

```typescript
// src/hooks/useOrders.ts
import { useQuery } from '@tanstack/react-query';
import { ordersApi } from '@/api/orders';

export function useOrders(params?: { status?: string }) {
  return useQuery({
    queryKey: ['orders', params],
    queryFn: () => ordersApi.list(params),
    staleTime: 30_000,
  });
}
```

## State Rules

| State type | Tool |
|---|---|
| Server data | React Query — never put API responses in Redux |
| Local UI state | useState / useReducer |
| Global UI (theme, language, user) | Context API |
| Forms | React Hook Form + Zod |

## Form Pattern

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1),
  scheduled_at: z.string().datetime(),
});

export function MyForm() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm({ resolver: zodResolver(schema) });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} />
      {errors.name && <span>{errors.name.message}</span>}
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? t('common.saving') : t('form.submit')}
      </button>
    </form>
  );
}
```

## Anti-Patterns — Never

- Reference a field name without verifying it's in the backend schema
- Call an endpoint without checking it exists in the router file
- Put API response data into Redux / Zustand
- Fetch inside a component directly
- Build features outside the current TODO phase
```

---

## SKILL TEMPLATE 3 — .skills/backend/SKILL.md

```markdown
---
name: backend-patterns
description: >
  Backend architecture patterns, domain-driven structure, dependency injection,
  external service wrapping, and anti-hallucination guardrails. Use for: creating
  API endpoints, writing services, defining schemas, writing tests, calling
  external services or AI models. CRITICAL: also triggers when the agent references
  a model field or database column without verifying it exists in the model file.
  Triggers on: "add an endpoint", "write a route", "backend for X", "service for Y".
---

# Backend Patterns

## Rule 1 — Never Reference Fields That Don't Exist

Before writing any endpoint or service:
1. Open the model file for that domain
2. Copy the exact field names from the model
3. Only then write schemas, queries, or responses using those fields

If a field doesn't exist yet, add it to the model first and write a migration.

## Rule 2 — One Domain at a Time

For each domain, complete in this order before the next domain:
1. Model (if changed)
2. Migration (if model changed)
3. Schema (Pydantic / Zod / equivalent)
4. Service / business logic
5. Router / controller
6. Tests

Never mix domain work.

## Domain Structure (FastAPI)

```
routers/orders.py      ← HTTP only: path, method, auth, call service
schemas/orders.py      ← Request/response models (Pydantic)
services/order_service.py  ← Business logic, isolated from HTTP
models/order.py        ← SQLAlchemy model
tests/test_orders.py   ← Tests for all of the above
```

## Router Pattern

```python
# routers/orders.py
from fastapi import APIRouter, Depends, HTTPException, status
from ..dependencies import require_role
from ..schemas.orders import OrderCreate, OrderResponse
from ..models.user import UserRole

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(
    data: OrderCreate,
    db=Depends(get_db),
    current_user=Depends(require_role(UserRole.CUSTOMER)),
):
    return await order_service.create(db, user_id=current_user.id, data=data)
```

## External Service Wrapper

Never call S3, Stripe, Firebase, Claude API, etc. directly in routes or services.
Always wrap for mockability:

```python
class StorageService:
    def __init__(self, client=None):
        self._client = client or boto3.client("s3")

    async def upload(self, key: str, data: bytes) -> str:
        self._client.put_object(Bucket=settings.BUCKET, Key=key, Body=data)
        return key

# In tests: StorageService(client=MockS3())
```

## Test Pattern

```python
@pytest.mark.asyncio
async def test_create_order_wrong_role(client, partner_token):
    r = await client.post("/api/v1/orders/", json={...},
                          headers={"Authorization": f"Bearer {partner_token}"})
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_create_order_success(client, customer_token):
    r = await client.post("/api/v1/orders/", json={...},
                          headers={"Authorization": f"Bearer {customer_token}"})
    assert r.status_code == 201
    assert r.json()["status"] == "PENDING"
```

## Error Convention

```python
raise HTTPException(404, "Order not found")
raise HTTPException(403, "Not your order")
raise HTTPException(400, f"Invalid transition: {old} → {new}")
raise HTTPException(409, "Already has a result")
```

## Anti-Patterns — Never

- Reference a model field without opening the model file first
- Write business logic in a router
- Call external services without wrapping them in a class
- Skip tests before moving to the next domain
- Use 500 for domain errors — always use specific codes
```

---

## SKILL TEMPLATE 4 — .skills/ml/SKILL.md

```markdown
---
name: ml-pipeline
description: >
  ML inference pipeline patterns for vision, audio, NLP, and multi-modal systems.
  Use when building or modifying an AI inference service, adding model wrappers,
  writing pipeline orchestration, implementing scoring/fraud detection logic, or
  integrating with LLM APIs (Claude, Gemini, OpenAI). Triggers on: "add a model",
  "inference pipeline", "audio analysis", "scoring logic", "fraud detection",
  "LLM integration", "vision module", "wrap the model".
---

# ML Pipeline Patterns

## Core Rule — Wrap Everything

Every model or API call must be wrapped in a class that:
1. Takes its client/model as a constructor argument (injectable mock)
2. Has typed input and output (dataclass or Pydantic)
3. Handles its own exceptions — never propagate crashes to the pipeline

```python
from dataclasses import dataclass

@dataclass
class DetectionResult:
    detected_classes: list[str]
    confidence_map: dict[str, float]
    frame_timestamps: list[float]

class ObjectDetector:
    def __init__(self, model=None, model_path="yolov8n.pt"):
        self._model = model or YOLO(model_path)

    def detect(self, video_path: str) -> DetectionResult:
        try:
            # inference logic
            ...
        except Exception as e:
            logger.error("detection_failed", error=str(e))
            return DetectionResult([], {}, [])  # safe default

# In tests: ObjectDetector(model=MockYOLO())
```

## Pipeline Orchestration

```python
async def run_pipeline(request: PipelineRequest) -> PipelineOutput:
    # Run independent steps in parallel
    result_a, result_b = await asyncio.gather(
        asyncio.to_thread(step_a, request),
        asyncio.to_thread(step_b, request),
    )
    # Sequential steps that depend on earlier results
    result_c = await asyncio.to_thread(step_c, request, result_a)
    
    return assemble_output(result_a, result_b, result_c)
```

## LLM Client Wrapper

```python
class LLMClient:
    def __init__(self, client=None):
        self._mock = os.getenv("LLM_MOCK") == "true"
        self._client = client or anthropic.AsyncAnthropic()

    async def complete(self, prompt: str, max_tokens: int = 500) -> str:
        if self._mock:
            return "Mock LLM response."
        try:
            msg = await self._client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception as e:
            logger.error("llm_failed", error=str(e))
            return ""  # never crash the pipeline
```

## Output Contract Test — Never Delete

```python
"""
THIS FILE ENFORCES THE AI OUTPUT CONTRACT.
NEVER DELETE THIS TEST.
If the output shape changes: update AGENT.md AND this test together.
"""
@pytest.mark.asyncio
async def test_pipeline_contract(mock_request):
    result = await run_pipeline(mock_request)
    # Assert every field in the contract
    assert isinstance(result.score, int)
    assert 0 <= result.score <= 100
    assert result.status in ("APPROVED", "REJECTED", "REVIEW")
    assert isinstance(result.explanation, list)
```

## Exception Policy

```python
# In each model wrapper — return safe default, never raise:
except Exception as e:
    logger.error("step_failed", step=self.__class__.__name__, error=str(e))
    return self._safe_default()

# In pipeline — degrade gracefully:
# Step A fails → score that dimension as 0, add "unavailable" to explanation
# Step B fails → skip it, do not fail the whole pipeline
# All steps fail → status = REVIEW, explain why, do not crash
```

## Anti-Patterns — Never

- Call a model or API directly in the pipeline (always wrap)
- Make real API calls in tests (use LLM_MOCK=true)
- Let a model exception propagate and crash the pipeline
- Delete the contract test
- Hardcode model paths or API keys
```

---

## SKILL TEMPLATE 5 — .skills/etl/SKILL.md

```markdown
---
name: etl-pipeline
description: >
  ETL and data pipeline patterns: idempotency, validation, DB seeding, frame
  extraction, synthetic data generation, and data quality verification. Use when
  building any script for data ingestion, transformation, loading, annotation prep,
  or DB seeding. Triggers on: "process data", "extract frames", "seed database",
  "generate dataset", "transform X", "load data", "data pipeline", "annotation
  script", "prepare training data".
---

# ETL Pipeline Patterns

## Rule 1 — Every Script Must Be Idempotent

Safe to run multiple times with the same result:

```python
def process_item(item, output_dir: Path) -> bool:
    output = output_dir / f"{item.id}.json"
    if output.exists():
        print(f"  SKIP {item.id}")
        return False
    result = transform(item)
    output.write_text(json.dumps(result))
    print(f"  DONE {item.id}")
    return True
```

## Script Structure

```python
#!/usr/bin/env python
"""
scripts/my_pipeline.py

One-sentence description of what this script does.

Usage:
    python scripts/my_pipeline.py --input-dir data/raw --output-dir data/processed

Outputs:
    data/processed/{id}.json
"""
import argparse
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    return p.parse_args()

def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    items = list(args.input_dir.glob("*"))
    print(f"Found {len(items)} items")

    done, skipped, failed = 0, 0, 0
    for item in items:
        try:
            created = process_item(item, args.output_dir)
            if created: done += 1
            else: skipped += 1
        except Exception as e:
            print(f"  FAIL {item.name}: {e}")
            failed += 1

    print(f"\nDone: {done}  Skipped: {skipped}  Failed: {failed}")
    if failed > 0:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
```

## DB Seed Pattern

```python
async def seed():
    async with session() as db:
        await seed_table_a(db)
        await seed_table_b(db)
        await db.commit()
        await verify_counts(db)

async def seed_table_a(db):
    items = [ModelA(code="x", ...), ModelA(code="y", ...)]
    for item in items:
        exists = await db.scalar(select(ModelA).where(ModelA.code == item.code))
        if not exists:
            db.add(item)
            print(f"  CREATED {item.code}")
        else:
            print(f"  SKIP {item.code}")

async def verify_counts(db):
    n = await db.scalar(select(func.count()).select_from(ModelA))
    print(f"\n  model_a: {n} rows")
    assert n > 0, "Seed failed — no rows"
```

## Data Quality Verification

Always verify after any ETL run:

```python
def verify_output(output_dir: Path, expected_count: int):
    files = list(output_dir.glob("*.json"))
    assert len(files) == expected_count, f"Expected {expected_count}, got {len(files)}"
    # Spot-check 10%
    import random
    for f in random.sample(files, max(1, len(files) // 10)):
        json.loads(f.read_text())  # raises if invalid JSON
    print(f"  Verified: {len(files)} files")
```

## Anti-Patterns — Never

- Run destructive operations without checking if output already exists
- Leave a script that crashes halfway with no progress report
- Silently swallow exceptions — always log and count failures
- Hardcode file paths — always use argparse
- Skip the final count/verification print
```

---

## SKILL TEMPLATE 6 — .skills/skill-creator/SKILL.md

```markdown
---
name: skill-creator
description: >
  Creates new Claude skill files (.skills/NAME/SKILL.md) for this project.
  Use when: adding a new domain the agent will work in repeatedly, the agent
  makes the same mistake 2+ times in a domain, a pattern appears in 3+ files
  with no canonical reference, or a human had to correct the agent's approach.
  Triggers on: "create a skill for X", "make a reusable pattern for Y", "teach
  the agent how to Z", "the agent keeps doing X wrong".
---

# Skill Creator

## When to Create a Skill

Create a new skill when you observe any of these:
- Agent makes the same mistake 2+ times in a domain
- A pattern appears in 3+ files with no canonical reference
- A new tool is introduced that the agent doesn't know well
- A human corrected the agent's approach to a domain

## Skill File Template

```markdown
---
name: [kebab-case-identifier]
description: >
  [One paragraph. Start with "Use when..." Include specific trigger phrases —
  the exact words a user would say to need this skill. Be specific about when
  to use vs. when not to use.]
---

# [Skill Title]

## Before Starting
[What to read or check before writing any code]

## Core Rule
[The single most important thing this skill teaches]

## Pattern
[Concrete, copyable code example — not pseudo-code]

## Anti-Patterns — Never
[The mistakes this skill prevents]

## Verification
[How to confirm the output is correct]
```

## Where Skills Live

```
.skills/
  [domain]/
    SKILL.md           ← the skill
    references/        ← additional docs (optional)
    examples/          ← example inputs/outputs (optional)
```

## Skill Quality Checklist

- [ ] Description has specific trigger phrases (what the user would actually type)
- [ ] Has at least one real, copyable code example
- [ ] Has an anti-patterns section
- [ ] Explains WHY, not just WHAT
- [ ] Under 300 lines (extract longer content to references/)
- [ ] Tested on a real task before finalising
```

---

## .gitignore (universal)

```gitignore
# Environment
.env
.env.*
!.env.example

# Python
__pycache__/
*.py[cod]
.venv/
venv/
env/
ENV/
*.egg-info/
dist/
build/

# Node
node_modules/
.next/
dist/
.cache/

# Agent meta (local only — never commit)
.agents/

# Data (generated, large)
data/
*.zip
*.tar.gz

# ML model weights
*.pt
*.bin
*.onnx
*.safetensors

# IDE
.vscode/
.idea/
*.swp
.DS_Store

# Test artifacts
.pytest_cache/
htmlcov/
.coverage
coverage/
```

---

## QUICK REFERENCE — What to Put Where

| What | Where | Who writes it |
|---|---|---|
| What you're building | `PS.md` | You (before starting) |
| How the agent builds it | `AGENT.md` | You + Claude |
| Agent's progress tracker | `TODO.md` | You (initial) + agent (updates) |
| Rolling state log | `.agents/context-sync.md` | Agent (one line per session) |
| Decisions needing review | `.agents/human_in_the_loop.md` | Agent (adds) + you (resolves) |
| LLM routing rules | `.agents/model-config.md` | You (if using multiple LLMs) |
| UI patterns | `.skills/ui/SKILL.md` | You (from template above) |
| Frontend patterns | `.skills/frontend/SKILL.md` | You (from template above) |
| Backend patterns | `.skills/backend/SKILL.md` | You (from template above) |
| ML patterns | `.skills/ml/SKILL.md` | You (if AI/ML project) |
| ETL patterns | `.skills/etl/SKILL.md` | You (if data pipeline) |
| Architecture decisions | `docs/decisions/ADR-NNN.md` | Agent (in Phase 0+) |
| System design docs | `docs/architecture/` | Agent (in Phase 0) |
| Source code | wherever Phase 0 decides | Agent (Phase 1+) |

## STARTING COMMAND

Once you've created the 4 root files and filled in `.skills/`:

```bash
# Claude Code
claude

# Or with a specific model
claude --model claude-sonnet-4-6

# Then say:
# "Read AGENT.md and TODO.md. Start from the first unchecked item."
```
