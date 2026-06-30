from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import supabase
from app.config import settings

security = HTTPBearer()

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    
    # Secure test bypass: if client provides service role key, map to the default test user
    if settings.SUPABASE_SERVICE_ROLE_KEY and token == settings.SUPABASE_SERVICE_ROLE_KEY:
        return "51928e80-ce4e-4846-9a40-f1fad08cb431"
        
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user_response.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")