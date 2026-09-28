"""The horizon a user last ran each stock on.

Horizons are the engine's four timeframes (intraday, swing, positional,
long_term), so there is nothing to create or delete: only a per-stock choice.
A stock with no saved row uses the profile's onboarding timeframe, which the
frontend already holds. Every query is filtered by the authenticated user id;
`supabase_admin` is used only after `get_current_user_id` has resolved.
"""
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_current_user_id
from app.config import settings
from app.database import supabase_admin
from app.rate_limit import limiter
from app.schemas.horizon import StockHorizon, StockHorizonIn

router = APIRouter(tags=["Horizons"])

TICKER_RE = re.compile(r"^[A-Z0-9&-]{1,20}$")


def _normalize_ticker(raw: str) -> str:
    """Same form the workspace sends to the run API: upper case, one `.NS`."""
    bare = raw.strip().upper()
    if bare.endswith(settings.MARKET_SUFFIX):
        bare = bare[: -len(settings.MARKET_SUFFIX)]
    if not TICKER_RE.match(bare):
        raise HTTPException(status_code=422, detail="Not an NSE ticker.")
    return f"{bare}{settings.MARKET_SUFFIX}"


@router.get("/stock/{ticker}", response_model=StockHorizon)
@limiter.limit("120/minute")
async def get_stock_horizon(request: Request, ticker: str, user_id: str = Depends(get_current_user_id)):
    symbol = _normalize_ticker(ticker)
    try:
        res = (
            supabase_admin.table("stock_horizons")
            .select("timeframe")
            .eq("user_id", user_id)
            .eq("ticker", symbol)
            .execute()
        )
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    return StockHorizon(ticker=symbol, timeframe=(res.data[0]["timeframe"] if res.data else None))


@router.put("/stock/{ticker}", response_model=StockHorizon)
@limiter.limit("60/minute")
async def set_stock_horizon(
    request: Request, ticker: str, payload: StockHorizonIn, user_id: str = Depends(get_current_user_id)
):
    symbol = _normalize_ticker(ticker)
    try:
        supabase_admin.table("stock_horizons").upsert(
            {
                "user_id": user_id,
                "ticker": symbol,
                "timeframe": payload.timeframe,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Database Error: {err}")
    return StockHorizon(ticker=symbol, timeframe=payload.timeframe)
