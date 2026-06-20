import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api.routes import profile,analytics,tutor
from app.database import supabase_admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Algorithmic Portfolio Analyzer Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Allows your Vite React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(profile.router, prefix="/api/v1/profiles", tags=["Phase 0: Ingestion"])

app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Phase 2: Quant Engine"])

app.include_router(tutor.router, prefix="/api/v1/tutor")


@app.get("/health")
def health_check():
    cache_ok = os.path.isdir(".local_cache")
    db_ok = supabase_admin is not None
    return {
        "status": "healthy",
        "cache_writable": cache_ok,
        "database_connected": db_ok,
        "system": "FinAI Orchestrator"
    }