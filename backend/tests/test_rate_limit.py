"""Rate limits are per account, not per address (audit MU-01).

Behind a hosting proxy every request arrives from the proxy's address, so an
address-keyed limit put all users in one bucket. The fix keys on the user id
that `get_current_user_id` records on `request.state`. That only works if
slowapi evaluates the key AFTER FastAPI has resolved the dependency, which is
an ordering assumption about a third-party library - so it is tested against a
real app rather than assumed.
"""
import asyncio
import inspect

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request as StarletteRequest

from app.api import deps
from app.rate_limit import limiter as shared_limiter
from app.rate_limit import rate_limit_key


def _request(ip="10.0.0.1"):
    return StarletteRequest({"type": "http", "client": (ip, 1234), "headers": [], "method": "GET", "path": "/"})


class _FakeAuth:
    """Treats the bearer token as the user id."""

    def get_user(self, token):
        user = type("User", (), {"id": token})()
        return type("Resp", (), {"user": user})()


@pytest.fixture
def fake_auth(monkeypatch):
    monkeypatch.setattr(deps, "supabase", type("Client", (), {"auth": _FakeAuth()})())


class TestKey:
    def test_authenticated_requests_are_keyed_on_the_account(self):
        req = _request()
        req.state.user_id = "alice"
        assert rate_limit_key(req) == "user:alice"

    def test_two_accounts_behind_one_proxy_get_two_buckets(self):
        a, b = _request("10.0.0.1"), _request("10.0.0.1")
        a.state.user_id, b.state.user_id = "alice", "bob"
        assert rate_limit_key(a) != rate_limit_key(b)

    def test_unauthenticated_falls_back_to_the_address(self):
        assert rate_limit_key(_request("203.0.113.7")) == "ip:203.0.113.7"

    def test_the_auth_dependency_records_the_user(self, fake_auth):
        req = _request()
        creds = type("Creds", (), {"credentials": "alice"})()
        assert asyncio.run(deps.get_current_user_id(req, creds)) == "alice"
        assert req.state.user_id == "alice"


class TestEnforcement:
    def test_one_users_limit_does_not_lock_out_another(self, fake_auth):
        limiter = Limiter(key_func=rate_limit_key)
        app = FastAPI()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        @app.get("/limited")
        @limiter.limit("2/minute")
        async def limited(request: Request, user_id: str = Depends(deps.get_current_user_id)):
            return {"user": user_id}

        client = TestClient(app)
        alice = {"Authorization": "Bearer alice"}
        bob = {"Authorization": "Bearer bob"}

        assert client.get("/limited", headers=alice).status_code == 200
        assert client.get("/limited", headers=alice).status_code == 200
        assert client.get("/limited", headers=alice).status_code == 429
        # Same client address as alice. Under the old per-IP key this was a 429.
        assert client.get("/limited", headers=bob).status_code == 200


class TestWiring:
    def test_routes_use_the_shared_user_keyed_limiter(self):
        import app.api.routes.analytics as analytics
        import app.api.routes.tutor as tutor

        assert analytics.limiter is shared_limiter
        assert tutor.limiter is shared_limiter

    def test_no_module_builds_an_address_keyed_limiter(self):
        import app.api.routes.analytics as analytics
        import app.api.routes.tutor as tutor

        for module in (analytics, tutor):
            assert "get_remote_address" not in inspect.getsource(module)
