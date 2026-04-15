from fastapi import FastAPI
from app.api.v1 import users
import uvicorn

app = FastAPI(
    title="AI Stock Investment Intelligence API",
    description="Backend for personalized investment analysis and multi-agent advisory.",
    version="0.1.0"
)

# Include Routers
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

@app.get("/")
def read_root():
    return {"message": "AI Stock Intelligence API is live", "version": "0.1.0"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
