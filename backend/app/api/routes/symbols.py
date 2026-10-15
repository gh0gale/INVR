"""NSE symbol search for the workspace ticker autocomplete.

Provider: Yahoo Finance search (the endpoint behind `yfinance.Search`, called with region=IN). The pipeline already
fetches every price and fundamental from Yahoo through yfinance, so a symbol
Yahoo lists under NSE is by construction one the pipeline can run, and this adds
no key and no new failure mode. Alpha Vantage (25 requests/day free), Finnhub and
FMP (US-centric free tiers) were rejected; Twelve Data is the fallback if this
unofficial endpoint breaks. See docs/workspace_features_plan.md.

Only NSE equities are returned, as `SYMBOL.NS`: the run API appends `.NS` to
anything without it, so a BSE `.BO` symbol would reach Bronze as `X.BO.NS`.
"""
import asyncio
import hashlib
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from yfinance.data import YfData

from app.api.deps import get_current_user_id
from app.rate_limit import limiter
from app.services.cache_service import get_cached_dict, set_cached_dict

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Symbols"])

CACHE_TTL_SECONDS = 24 * 3600
PROVIDER_TIMEOUT_SECONDS = 5
MAX_RESULTS = 8
QUERY_RE = re.compile(r"^[A-Za-z0-9 .&-]{1,32}$")
NSE_SYMBOL_RE = re.compile(r"^[A-Z0-9&-]{1,20}\.NS$")


class Suggestion(BaseModel):
    symbol: str     # exactly what the run API takes, e.g. "TCS.NS"
    name: str
    exchange: str   # always "NSE" for now


def to_suggestions(quotes: list[dict]) -> list[Suggestion]:
    """Keep NSE equities only, one per symbol, in provider order."""
    out: list[Suggestion] = []
    seen: set[str] = set()
    for q in quotes:
        symbol = str(q.get("symbol") or "").upper()
        if q.get("exchange") != "NSI" or q.get("quoteType") != "EQUITY":
            continue
        if not NSE_SYMBOL_RE.match(symbol) or symbol in seen:
            continue
        # ponytail: Yahoo also lists NSE trade-series variants (e.g. TMCV-BL.NS)
        # with no long name; dropping nameless rows removes them. Filter on the
        # series suffix if a real listing ever lacks a long name.
        name = q.get("longname")
        if not name:
            continue
        seen.add(symbol)
        out.append(Suggestion(symbol=symbol, name=str(name), exchange="NSE"))
        if len(out) == MAX_RESULTS:
            break
    return out


SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"


def _search(query: str) -> list[dict]:
    # region=IN is what makes a short prefix ("mar", "ta") rank Indian listings:
    # without it Yahoo ranks globally, returns about 5 hits, and none are NSE.
    # yf.Search has no region argument, so this goes through yfinance's own
    # session (cookies, rate handling) instead of a new HTTP dependency.
    resp = YfData().cache_get(
        url=SEARCH_URL,
        params={"q": query, "quotesCount": 20, "newsCount": 0, "listsCount": 0,
                "enableCb": False, "region": "IN", "lang": "en-IN"},
        timeout=PROVIDER_TIMEOUT_SECONDS,
    )
    return resp.json().get("quotes", [])


@router.get("/search", response_model=list[Suggestion])
@limiter.limit("60/minute")
async def search_symbols(
    request: Request,
    q: str = Query(..., min_length=1, max_length=32),
    user_id: str = Depends(get_current_user_id),
):
    query = " ".join(q.split()).lower()
    if not QUERY_RE.match(query):
        raise HTTPException(status_code=422, detail="Use letters, numbers, spaces, '.', '&' or '-'.")

    key = "symbols_in_" + hashlib.sha256(query.encode()).hexdigest()[:24]
    cached = await get_cached_dict(key, CACHE_TTL_SECONDS)
    if cached is not None:
        return cached["items"]

    try:
        quotes = await asyncio.to_thread(_search, query)
    except Exception as err:
        logger.warning("Symbol search failed for %r: %s", query, err)
        raise HTTPException(status_code=502, detail="Stock search is unavailable right now.")

    items = [s.model_dump() for s in to_suggestions(quotes or [])]
    await set_cached_dict(key, {"items": items}, CACHE_TTL_SECONDS)
    return items
