# Directory Structure

> **Status:** ⏳ Not started — Agent writes this in Phase 0.4
> **Rule:** Do NOT create any directories until this file is written and Phase 0.5 gate passes.

## Intended Tree
<!-- Full project directory tree with one-line purpose comments per directory -->

```
ai-stock/
├── .agents/              ← Agent meta-layer (gitignored)
├── backend/              ← FastAPI application
│   ├── routers/          ← HTTP route handlers
│   ├── schemas/          ← Pydantic request/response models
│   ├── services/         ← Business logic
│   ├── models/           ← SQLAlchemy ORM models
│   ├── etl/              ← Market data pipelines
│   └── tests/            ← pytest test files
├── frontend/             ← React + Vite application
│   ├── src/
│   │   ├── api/          ← API client layer
│   │   ├── components/   ← Reusable UI components
│   │   ├── hooks/        ← Custom React hooks
│   │   ├── pages/        ← Route-level page components
│   │   └── lib/          ← Utilities (supabase client, etc.)
│   └── public/
└── ...
```

<!-- Agent will fill this out fully in Phase 0.4 -->
