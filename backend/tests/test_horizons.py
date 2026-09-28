"""Per-stock horizon: one of the engine's four timeframes, saved per user and
ticker, against an in-memory Supabase (tests/_fake_supabase.py)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import app.api.routes.horizons as horizons
from app.api import deps
from app.pipeline.router import PIPELINE_CONFIG
from app.rate_limit import limiter
from app.schemas.horizon import Timeframe
from _fake_supabase import FakeSupabase


class _FakeAuth:
    """Treats the bearer token as the user id."""

    def get_user(self, token):
        user = type("User", (), {"id": token})()
        return type("Resp", (), {"user": user})()


@pytest.fixture
def db(monkeypatch):
    fake = FakeSupabase()
    monkeypatch.setattr(horizons, "supabase_admin", fake)
    monkeypatch.setattr(deps, "supabase", type("Client", (), {"auth": _FakeAuth()})())
    limiter.reset()
    return fake


@pytest.fixture
def client(db):
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(horizons.router, prefix="/h")
    return TestClient(app)


ALICE = {"Authorization": "Bearer alice"}
BOB = {"Authorization": "Bearer bob"}


def test_horizons_are_exactly_the_engine_timeframes():
    assert set(Timeframe.__args__) == set(PIPELINE_CONFIG)


def test_unset_stock_has_no_saved_horizon(client):
    assert client.get("/h/stock/TCS", headers=ALICE).json() == {"ticker": "TCS.NS", "timeframe": None}


def test_set_then_read_back_in_either_ticker_form(client):
    assert client.put("/h/stock/tcs", json={"timeframe": "intraday"}, headers=ALICE).status_code == 200
    assert client.get("/h/stock/TCS.NS", headers=ALICE).json()["timeframe"] == "intraday"


def test_changing_the_horizon_overwrites_the_one_row(client, db):
    client.put("/h/stock/TCS", json={"timeframe": "swing"}, headers=ALICE)
    client.put("/h/stock/TCS", json={"timeframe": "long_term"}, headers=ALICE)
    assert client.get("/h/stock/TCS", headers=ALICE).json()["timeframe"] == "long_term"
    assert len(db.tables["stock_horizons"]) == 1


def test_choices_are_per_user(client):
    client.put("/h/stock/TCS", json={"timeframe": "positional"}, headers=ALICE)
    assert client.get("/h/stock/TCS", headers=BOB).json()["timeframe"] is None


@pytest.mark.parametrize("bad", ["1 month", "daily", "", "LONG_TERM"])
def test_anything_but_the_four_is_422(client, bad):
    assert client.put("/h/stock/TCS", json={"timeframe": bad}, headers=ALICE).status_code == 422


@pytest.mark.parametrize("bad", ["TCS.BO", "a b", "X" * 21])
def test_non_nse_ticker_is_422(client, bad):
    assert client.get(f"/h/stock/{bad}", headers=ALICE).status_code == 422
