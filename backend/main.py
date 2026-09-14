import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware # Corrected import
from fastapi.responses import RedirectResponse

from app.database import supabase_admin

# 1. INITIALIZE TELEMETRY FIRST (Must happen before LangGraph imports)
from app.telemetry import init_telemetry
tracer = init_telemetry()

# 2. NOW IMPORT ROUTES
from app.api.routes import profile, analytics, tutor
from app.rate_limit import limiter
from app.llm import Task, model_identity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

logger = logging.getLogger("main")

app = FastAPI(
    title="Algorithmic Portfolio Analyzer Engine",
    version="1.0.0"
)

# One limiter, keyed on the authenticated user (audit MU-01, app/rate_limit.py)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middlewares (CORS must generally be the outermost layer)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)

@app.on_event("startup")
def print_health_checks():
    cache_ok = os.path.isdir(".local_cache")
    db_ok = supabase_admin is not None
    logger.info("=== System Health Checks ===")
    logger.info(f"Cache writable: {cache_ok}")
    logger.info(f"Database connected: {db_ok}")
    logger.info(f"System: FinAI Orchestrator")
    logger.info("============================")


app.include_router(profile.router, prefix="/api/v1/profiles", tags=["Phase 0: Ingestion"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Phase 2: Quant Engine"])
app.include_router(tutor.router, prefix="/api/v1/tutor")

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.get("/health")
def health_check():
    # Must stay cheap: the hosting health check and the frontend's warm-up
    # ping both hit it (deployment_plan.md §2.4). It reports configuration
    # only, and never calls Supabase or a model.
    cache_ok = os.path.isdir(".local_cache")
    db_ok = supabase_admin is not None
    return {
        "status": "healthy",
        "cache_writable": cache_ok,
        "database_connected": db_ok,
        "llm": model_identity(Task.SYNTHESIS),
        "system": "FinAI Orchestrator"
    }