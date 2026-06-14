from fastapi import FastAPI
from app.api.routes import profile,analytics


app = FastAPI(
    title="Algorithmic Portfolio Analyzer Engine",
    version="1.0.0"
)


app.include_router(profile.router, prefix="/api/v1/profiles", tags=["Phase 0: Ingestion"])

app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Phase 2: Quant Engine"])


@app.get("/health")
def health_check():
    return {"status": "healthy"}