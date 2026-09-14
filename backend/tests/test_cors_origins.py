"""CORS origins survive the ways a URL gets pasted into a dashboard (audit CORS-01).

Found on the first deploy, 2026-09-14: the browser's preflight to the Render
backend (`OPTIONS /api/v1/profiles/`) got 400 from CORSMiddleware, because
CORS_ALLOW_ORIGINS did not match the frontend origin character for character.
Starlette compares exactly and a browser never sends a trailing slash or quotes,
so either one, copied along with the URL, locked out every browser request.
"""
import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.config import Settings

FRONTEND = "https://invr.example.workers.dev"


@pytest.mark.parametrize("raw, expected", [
    (f"{FRONTEND}/", [FRONTEND]),
    (f'"{FRONTEND}"', [FRONTEND]),
    (f"'{FRONTEND}/'", [FRONTEND]),
    (f" {FRONTEND}/ , http://localhost:5173 ", [FRONTEND, "http://localhost:5173"]),
    (f"{FRONTEND},,", [FRONTEND]),
])
def test_origins_are_normalised_to_what_a_browser_sends(monkeypatch, raw, expected):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", raw)
    assert Settings(_env_file=None).cors_origins == expected


def _preflight(setting, origin, monkeypatch):
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", setting)
    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=Settings(_env_file=None).cors_origins,
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    @app.get("/api/v1/profiles/")
    def profile():
        return {}

    return TestClient(app).options("/api/v1/profiles/", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization",
    })


def test_a_setting_pasted_with_a_trailing_slash_still_admits_the_frontend(monkeypatch):
    """The exact failure from the deploy log, through the real middleware."""
    r = _preflight(f"{FRONTEND}/", FRONTEND, monkeypatch)
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == FRONTEND


def test_an_origin_that_is_not_listed_is_still_refused(monkeypatch):
    r = _preflight(FRONTEND, "https://someone-else.example", monkeypatch)
    assert r.status_code == 400
