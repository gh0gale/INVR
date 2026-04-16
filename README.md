# AI Investment Intelligence System

> [!IMPORTANT]
> **Project Implementation Context & Sync**: For detailed architectural blueprints, progress tracking (TODOs), and product specifications, always refer to the [`.agents/`](file:///.agents) directory.

An end-to-end, privacy-aware financial advisory platform designed for retail investors. This system combines Data Engineering pipelines, LLM-based reasoning, RAG (Retrieval-Augmented Generation), and rule-based logic to evaluate stocks and provide personalized, educational recommendations.

## Overview

This project is built using a highly structured, agent-driven development process. The core architecture relies on a hybrid intelligence approach:
*   **Privacy-Aware:** Provides recommendations without requiring the user to disclose their exact portfolio wealth or holdings; relies on rough sector exposures and risk profiles.
*   **Education First:** Every recommendation is accompanied by context-aware educational explanations (e.g., explaining *why* a specific P/E or PEG ratio matters for a given stock).
*   **Fund-Manager Grade Analysis:** Utilizes a multi-dimensional prompt system (Fundamental, Technical, Sentiment, Quantitative, Derivative) to evaluate assets.

## Technology Stack

*   **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Recharts
*   **Backend:** FastAPI, Python, SQLAlchemy
*   **Database:** Supabase (PostgreSQL + Auth)
*   **AI/Local:** LangChain (ReAct Agent), OpenAI/Claude APIs, FAISS/ChromaDB for Vector Search
*   **Data Pipelines (ETL):** `yfinance`, Pandas, APScheduler

## Agentic Meta-Layer

This repository is governed by an AI Agent Meta-Layer located in the `.agents/` directory.

> **Note for Developers/AI Assistants:**
> Before making any changes or starting a development session, you **MUST** read [`.agents/AGENT.md`](file:///c:/CODES/DE/AI%20Stock/.agents/AGENT.md) and [`.agents/TODO.md`](file:///c:/CODES/DE/AI%20Stock/.agents/TODO.md). Do not start writing application code without consulting the session state.

## Getting Started (Once Scaffolded)

*(Full instructions will be populated here after Phase 1 setup is complete regarding how to spin up the local Docker environment, Supabase local instance, and React dev servers).*
