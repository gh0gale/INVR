from fastapi import FastAPI
from app.api.routes import profile,analytics,tutor


app = FastAPI(
    title="Algorithmic Portfolio Analyzer Engine",
    version="1.0.0"
)


app.include_router(profile.router, prefix="/api/v1/profiles", tags=["Phase 0: Ingestion"])

app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Phase 2: Quant Engine"])

app.include_router(tutor.router, prefix="/api/v1/tutor")


@app.get("/health")
def health_check():
    return {"status": "healthy"}