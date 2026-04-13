---
name: skill-creator
description: >
  Creates new skill files (.agents/skills/NAME.md) for the AI Investment Intelligence
  project. Use when: adding a new domain the agent will work in repeatedly, the agent
  makes the same mistake 2+ times in a domain, a pattern appears in 3+ files with no
  canonical reference, or a human corrected the agent's approach.
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
.agents/skills/
  [domain].md              ← the skill file
```

## Skill Quality Checklist

- [ ] Description has specific trigger phrases (what the user would actually type)
- [ ] Has at least one real, copyable code example
- [ ] Has an anti-patterns section
- [ ] Explains WHY, not just WHAT
- [ ] Under 300 lines (extract longer content to separate docs)
- [ ] Tested on a real task before finalising

## Existing Skills in This Project

| Skill | File | Domain |
|-------|------|--------|
| UI Components | `ui.md` | React components, disclaimers, scorecards |
| Frontend Patterns | `frontend.md` | API layer, React Query, forms, state |
| Backend Patterns | `backend.md` | FastAPI routers, services, schemas, tests |
| ML Pipeline | `ml.md` | LLM wrapper, ReAct agent, RAG, analysis engine |
| ETL Pipeline | `etl.md` | yfinance fetcher, metrics, daily pipeline |
| Skill Creator | `skill-creator.md` | This file — how to create new skills |
