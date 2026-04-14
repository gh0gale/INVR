Markdown
# 🎯 GitHub Copilot Instruction File: Backend Architecture Setup

**System Context:**
You are an expert Python Backend Developer setting up an AI-Powered Personalized Investment Intelligence System. We are building a robust, async backend using `FastAPI`, entirely managed by `uv` for dependency and environment management. 

**Goal:**
Scaffold the complete directory structure and boilerplate files for the backend application according to the specifications below. Do not implement complex business logic yet; focus entirely on wiring up the skeleton, creating the necessary folders, and generating the entry-point boilerplates.

---

## - [x] 🛠️ Step 1: Initialize the Project & Dependencies
1. Create a root folder named `backend/` and navigate into it.
2. Initialize a new `uv` project.
3. Use `uv add` to install the following dependencies:
   - `fastapi`
   - `uvicorn`
   - `yfinance`
   - `langchain-community`
   - `sentence-transformers`
   - `faiss-cpu`
   - `supabase`
   - `python-dotenv`

---

## - [x] 🗂️ Step 2: Scaffold the Directory Structure
Inside the `backend/` directory, create the exact following folder and file structure. Leave the files empty for now unless specified in Step 3.

```text
backend/
├── .env
├── main.py
└── app/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── routes.py
    │   └── dependencies.py
    ├── db/
    │   ├── __init__.py
    │   └── supabase.py
    ├── agent/
    │   ├── __init__.py
    │   ├── core_agent.py
    │   └── tools.py
    ├── services/
    │   ├── __init__.py
    │   ├── market_data.py
    │   ├── scoring_engine.py
    │   └── portfolio.py
    └── rag/
        ├── __init__.py
        ├── data_sources/
        ├── vector_db/
        ├── 1_document_loaders/
        │   └── loader.py
        ├── 2_embedder/
        │   └── embed.py
        ├── 3_vector_store/
        │   └── store.py
        └── 4_retrieval_chain/
            └── retriever.py
- [x] 📝 Step 3: Generate Core Boilerplate Code
Please populate the following key files with boilerplate code to ensure the app compiles and runs.

1. backend/main.py
Write a standard FastAPI entry point.

Include from fastapi import FastAPI.

Initialize the app instance.

Add a basic root GET / endpoint returning a health check status (e.g., {"status": "AI Investment Backend is running"}).

Include CORS middleware allowing all origins for development purposes.

2. backend/.env
Create a template for environment variables. Include placeholders for:

SUPABASE_URL=

SUPABASE_ANON_KEY=

HUGGINGFACE_API_KEY=

3. backend/app/api/routes.py
Set up an APIRouter.

Include from fastapi import APIRouter.

Initialize router = APIRouter().

Create a dummy POST /chat endpoint that accepts a simple Pydantic model (e.g., {"query": "string"}) and returns a mocked string response.

4. backend/app/db/supabase.py
Set up the Supabase client connection.

Import os and the supabase python client.

Load the environment variables.

Initialize and expose a supabase_client object.