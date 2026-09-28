"""First-login workspace tour flag: stored on the profile so it survives a device
change, stamped once, and never cleared by re-saving the profile."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.routes.profile as profile_routes
import app.services.profile_service as profile_service
from app.api import deps
from app.schemas.profile import UserProfileRequest
from _fake_supabase import FakeSupabase

ROW = {
    "id": "alice",
    "experience": "beginner",
    "goal": "wealth_growth",
    "timeframe": "swing",
    "risk": "moderate",
    "portfolio": {},
    "capital": 100000.0,
    "profile_version_hash": "0" * 32,
    "tour_completed_at": None,
}


class _FakeAuth:
    def get_user(self, token):
        user = type("User", (), {"id": token})()
        return type("Resp", (), {"user": user})()


@pytest.fixture
def db(monkeypatch):
    fake = FakeSupabase()
    fake.tables["user_profiles"] = [dict(ROW)]
    monkeypatch.setattr(profile_routes, "supabase_admin", fake)
    monkeypatch.setattr(profile_service, "supabase_admin", fake)
    monkeypatch.setattr(deps, "supabase", type("Client", (), {"auth": _FakeAuth()})())
    return fake


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(profile_routes.router, prefix="/p")
    return TestClient(app)


AUTH = {"Authorization": "Bearer alice"}


def test_new_profile_has_not_seen_the_tour(client):
    assert client.get("/p/", headers=AUTH).json()["tour_completed_at"] is None


def test_completing_the_tour_is_stored_and_returned(client):
    stamped = client.post("/p/tour", headers=AUTH).json()["tour_completed_at"]
    assert stamped
    assert client.get("/p/", headers=AUTH).json()["tour_completed_at"] is not None


def test_completing_twice_keeps_the_first_stamp(client, db):
    client.post("/p/tour", headers=AUTH)
    first = db.tables["user_profiles"][0]["tour_completed_at"]
    client.post("/p/tour", headers=AUTH)
    assert db.tables["user_profiles"][0]["tour_completed_at"] == first


def test_resaving_the_profile_does_not_replay_the_tour(client, db):
    client.post("/p/tour", headers=AUTH)
    req = UserProfileRequest(
        experience="advanced", goal="wealth_growth", timeframe="swing", risk="moderate", portfolio={}, capital=5.0
    )
    profile_service.create_and_store_profile("alice", req)
    assert db.tables["user_profiles"][0]["tour_completed_at"] is not None


def test_unknown_profile_is_404(client):
    assert client.post("/p/tour", headers={"Authorization": "Bearer nobody"}).status_code == 404
