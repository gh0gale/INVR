from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase
from app.config import settings

security = HTTPBearer()

async def get_current_user_id(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials

    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")

    # Recorded for the rate limiter, which keys on the account rather than the
    # client address (audit MU-01, see app/rate_limit.py).
    request.state.user_id = user_response.user.id
    return user_response.user.id
