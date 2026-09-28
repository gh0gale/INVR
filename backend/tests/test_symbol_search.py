"""Ticker autocomplete: Yahoo quotes are mapped to exactly the ticker form the
run API takes (`SYMBOL.NS`), everything else is dropped, and the provider is
never called for a cached query. No network: `_search` is stubbed."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import app.api.routes.symbols as symbols
from app.api import deps
from app.rate_limit import limiter
from app.schemas.api import PipelineRequest

QUOTES = [
    {"symbol": "TCS.NS", "longname": "Tata Consultancy Services Limited", "exchange": "NSI", "quoteType": "EQUITY"},
    {"symbol": "TCS.BO", "longname": "Tata Consultancy Services Limited", "exchange": "BSE", "quoteType": "EQUITY"},
    {"symbol": "TCS", "longname": "The Container Store", "exchange": "NYQ", "quoteType": "EQUITY"},
    {"symbol": "TMCV-BL.NS", "longname": None, "exchange": "NSI", "quoteType": "EQUITY"},
    {"symbol": "M&M.NS", "longname": "Mahindra & Mahindra Limited", "exchange": "NSI", "quoteType": "EQUITY"},
    {"symbol": "BAJAJ-AUTO.NS", "longname": "Bajaj Auto Limited", "exchange": "NSI", "quoteType": "EQUITY"},
    {"symbol": "TCS.NS", "longname": "Tata Consultancy Services Limited", "exchange": "NSI", "quoteType": "EQUITY"},
    {"symbol": "^NSEI", "longname": "NIFTY 50", "exchange": "NSI", "quoteType": "INDEX"},
]


class _FakeAuth:
    def get_user(self, token):
        user = type("User", (), {"id": token})()
        return type("Resp", (), {"user": user})()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(deps, "supabase", type("Client", (), {"auth": _FakeAuth()})())
    limiter.reset()
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(symbols.router, prefix="/s")
    return TestClient(app)


AUTH = {"Authorization": "Bearer alice"}


class TestMapping:
    def test_only_nse_equities_with_a_name_survive_once_each(self):
        assert [s.symbol for s in symbols.to_suggestions(QUOTES)] == ["TCS.NS", "M&M.NS", "BAJAJ-AUTO.NS"]

    def test_every_suggestion_is_a_valid_run_request(self):
        for s in symbols.to_suggestions(QUOTES):
            req = PipelineRequest(ticker=s.symbol, timeframe="swing")
            assert req.ticker.endswith(".NS") and req.ticker.count(".NS") == 1
            assert s.exchange == "NSE"

    def test_result_count_is_capped(self):
        many = [
            {"symbol": f"S{i}.NS", "longname": f"S{i}", "exchange": "NSI", "quoteType": "EQUITY"} for i in range(20)
        ]
        assert len(symbols.to_suggestions(many)) == symbols.MAX_RESULTS


class TestRoute:
    def test_search_returns_mapped_suggestions(self, client, monkeypatch):
        monkeypatch.setattr(symbols, "_search", lambda q: QUOTES)
        res = client.get("/s/search", params={"q": "tcs"}, headers=AUTH)
        assert res.status_code == 200
        assert res.json()[0] == {"symbol": "TCS.NS", "name": "Tata Consultancy Services Limited", "exchange": "NSE"}

    def test_cached_query_does_not_call_the_provider_again(self, client, monkeypatch):
        calls = []
        monkeypatch.setattr(symbols, "_search", lambda q: calls.append(q) or QUOTES)
        client.get("/s/search", params={"q": "TCS"}, headers=AUTH)
        client.get("/s/search", params={"q": "  tcs "}, headers=AUTH)
        assert calls == ["tcs"]

    def test_provider_failure_is_502(self, client, monkeypatch):
        def boom(q):
            raise RuntimeError("yahoo down")

        monkeypatch.setattr(symbols, "_search", boom)
        res = client.get("/s/search", params={"q": "infy"}, headers=AUTH)
        assert res.status_code == 502

    @pytest.mark.parametrize("q", ["", "x" * 33, "tcs; drop", "<script>"])
    def test_bad_queries_are_422(self, client, monkeypatch, q):
        monkeypatch.setattr(symbols, "_search", lambda q: QUOTES)
        assert client.get("/s/search", params={"q": q}, headers=AUTH).status_code == 422

    def test_requires_auth(self, client):
        assert client.get("/s/search", params={"q": "tcs"}).status_code in (401, 403)


class TestRunContract:
    def test_unknown_timeframe_is_rejected_before_the_graph(self):
        with pytest.raises(ValueError):
            PipelineRequest(ticker="TCS.NS", timeframe="1 month")
