---
name: frontend-patterns
description: >
  Frontend architecture patterns for the AI Investment Intelligence platform.
  Stack: React 18 + TypeScript + Vite + Tailwind CSS + React Query + React Hook Form
  + Zod + Recharts + React Router v6.
  Use for: API integration, state management, routing, form handling, custom hooks,
  chart wiring. CRITICAL: also use whenever the agent seems to be inventing API shapes
  or drifting from the current TODO phase.
  Triggers on: "wire up the API", "connect to backend", "add state for", "create a hook",
  "frontend for X", or when the agent references a field or endpoint without verifying it
  exists in the backend router file.
---

# Frontend Patterns — Investment Intelligence Platform

## Rule 1 — Never Invent API Shapes

Before writing ANY API call:
1. Open the backend router file for that domain (e.g., `backend/routers/analysis.py`)
2. Copy the exact endpoint path, method, request body fields, and response fields
3. Only then write the frontend API call

If the backend route doesn't exist yet:
```typescript
// TODO: endpoint not yet implemented — Phase 4.6
// Expected: POST /api/v1/analysis/stock with { ticker: string }
const mockAnalysis = { verdict: 'Wait', score: 6, scorecard: {} };
```

## Rule 2 — Stay On Point

If you find yourself building something not in the current TODO phase:
1. Stop
2. Add it to `.agents/TODO.md` under the correct future phase
3. Return to the current task

## Rule 3 — "The User Reacts, Not Types" (UX Core Principle)

The frontend represents a 4-Stage Flow:
1. **Onboarding**: One-time 5-7 tap-to-select questions. Ends in a Persona Reveal.
2. **Dashboard**: Default landing view. Proactively shows portfolio health, 3-4 daily picks, and market pulse. No typing needed.
3. **Explore**: Deep-dive into a stock with a Scorecard, a "Why for you" explainer, and expandable jargon definitions via RAG.
4. **Act**: Trade setup with entry, target, and position sizing logic based on monthly investable surplus.

**Important**: The chat interface is only for secondary follow-up ("Ask anything about this"). Do not make the entire app a chat bot.

## API Layer — All calls go through `src/api/`

```typescript
// src/api/analysis.ts
import { apiClient } from './client';
import type { StockAnalysisResult } from './types';

export const analysisApi = {
  analyze: (ticker: string) =>
    apiClient.post<StockAnalysisResult>('/api/v1/analysis/stock', { ticker }),
};

// src/api/advisory.ts
import type { AdvisoryResult } from './types';
export const advisoryApi = {
  suggest: () =>
    apiClient.post<AdvisoryResult>('/api/v1/advisory/suggest', {}),
};

// src/api/agent.ts
import type { AgentMessage } from './types';
export const agentApi = {
  chat: (message: string, sessionId: string) =>
    apiClient.post<AgentMessage>('/api/v1/agent/chat', { message, session_id: sessionId }),
};
```

Never call fetch/axios directly in a component or hook.

## Data Fetching — React Query

```typescript
// src/hooks/useStockAnalysis.ts
import { useMutation } from '@tanstack/react-query';
import { analysisApi } from '@/api/analysis';

export function useStockAnalysis() {
  return useMutation({
    mutationFn: (ticker: string) => analysisApi.analyze(ticker),
  });
}

// src/hooks/useChat.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { agentApi } from '@/api/agent';

export function useChat(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (message: string) => agentApi.chat(message, sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatHistory', sessionId] });
    },
  });
}
```

## State Rules

| State type | Tool |
|---|---|
| Server data (analysis, portfolio, alerts) | React Query — never put in Redux |
| Local UI state (modal open, selected tab) | `useState` / `useReducer` |
| Global UI (theme, user profile, auth) | Context API |
| Forms | React Hook Form + Zod |

## API Client Setup

```typescript
// src/api/client.ts
import axios from 'axios';
import { supabase } from '@/lib/supabase';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30_000,  // LLM calls can be slow
});

apiClient.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});
```

## Form Pattern (Profile Setup Wizard)

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const profileSchema = z.object({
  age: z.number().min(18).max(100),
  income_bracket: z.enum(['<5L', '5-10L', '10-25L', '25L+']),
  monthly_investable: z.number().min(500),
  risk_appetite: z.enum(['conservative', 'moderate', 'aggressive']),
  investment_horizon_months: z.number().min(6),
  primary_goal: z.enum(['wealth_creation', 'retirement', 'child_education', 'other']),
  portfolio_sectors: z.string().optional(), // Or JSON string representation of sector_exposure
});

type ProfileFormData = z.infer<typeof profileSchema>;

export function ProfileSetupForm() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm<ProfileFormData>({ resolver: zodResolver(profileSchema) });

  return (
    <form onSubmit={handleSubmit(onSubmit)} aria-label="Investor profile setup">
      {/* fields */}
      <button type="submit" disabled={isSubmitting} aria-busy={isSubmitting}>
        {isSubmitting ? 'Saving...' : 'Save Profile'}
      </button>
    </form>
  );
}
```

## Environment Variables Required

```
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

## Anti-Patterns — Never

- Reference a field name without verifying it's in the backend Pydantic schema
- Call an endpoint without checking it exists in the backend router file
- Put API response data into Redux or Zustand
- Fetch inside a component directly
- Build features outside the current TODO phase
- Set API timeout < 30s (LLM calls can legitimately take 10–20s)
