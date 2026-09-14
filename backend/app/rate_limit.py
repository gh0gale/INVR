"""The one rate limiter, keyed on the authenticated user.

Audit finding MU-01. Three modules each built their own
`Limiter(key_func=get_remote_address)`. Behind a hosting proxy the remote
address is the proxy's, so every user shared one bucket and the tenth analysis
from anyone locked out everybody; trusting X-Forwarded-For instead would make
the limit trivially bypassable.

The user id is already verified before any limited handler body runs:
slowapi checks route limits inside the endpoint wrapper, after FastAPI has
resolved `get_current_user_id`, which records the id on `request.state`. So the
key is the account, and the address is only a fallback for the rare limited
route that has no authenticated user.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import settings


def rate_limit_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=rate_limit_key, storage_uri=settings.RATE_LIMIT_STORAGE_URI)
