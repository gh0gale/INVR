"""Guards the synthesis cache added for audit finding P4-06.

A cache on an LLM call is only safe if its key covers everything that changes
the answer. These tests pin the two ways it could go wrong: serving one user
the wording written for another, and caching a retry that exists precisely
because the previous answer was wrong.
"""
import asyncio
import json
import os

import pytest

from app.services.cache_service import get_cached_dict, set_cached_dict


@pytest.fixture(autouse=True)
def _cache_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("INVR_CACHE_DIR", str(tmp_path / "c"))


class TestCacheDirectoryIsRedirectable:
    def test_writes_land_in_the_configured_directory(self, tmp_path):
        asyncio.run(set_cached_dict("probe", {"v": 1}, 60))
        written = list((tmp_path / "c").glob("*.json"))
        assert [p.name for p in written] == ["probe.json"]

    def test_a_value_round_trips(self):
        asyncio.run(set_cached_dict("probe", {"raw_json_string": "hello"}, 60))
        got = asyncio.run(get_cached_dict("probe", 60))
        assert got == {"raw_json_string": "hello"}

    def test_an_expired_entry_is_a_miss(self):
        asyncio.run(set_cached_dict("probe", {"v": 1}, 60))
        assert asyncio.run(get_cached_dict("probe", 0)) is None

    def test_a_missing_entry_is_a_miss_not_an_error(self):
        assert asyncio.run(get_cached_dict("never-written", 60)) is None


class TestCacheKeyCoversEverythingThatChangesTheAnswer:
    """Read the orchestrator's key construction rather than trusting it by eye."""

    @staticmethod
    def _key_source() -> str:
        import inspect

        from app import orchestrator

        src = inspect.getsource(orchestrator.llm_synthesizer_node)
        start = src.index("cache_key = ")
        return src[start : src.index("cached = await get_cached_dict")]

    @pytest.mark.parametrize(
        "field",
        ["prompt_version", "ticker", "timeframe", "goal", "risk", "verdict", "gates", "silver"],
    )
    def test_key_includes(self, field):
        """Each of these appears in the prompt, so each must appear in the key.

        Dropping `risk` or `goal` would serve a conservative investor the
        aggressive investor's narrative - a correctness bug dressed as a
        performance win.
        """
        assert f'"{field}"' in self._key_source()

    def test_a_retry_bypasses_the_cache_entirely(self):
        """A correction_note means the previous answer failed validation.

        Re-serving it from cache would loop the self-healing retry forever.
        """
        assert 'if not state.get("correction_note")' in self._key_source()


class TestConfiguredSettings:
    """Audit finding P5-03."""

    def test_cors_origins_parse_from_a_comma_separated_string(self, monkeypatch):
        from app.config import Settings

        monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://a.example, https://b.example")
        assert Settings().cors_origins == ["https://a.example", "https://b.example"]

    def test_an_unknown_guardrail_mode_is_rejected(self, monkeypatch):
        """Fail at startup, not at the first request that needed screening."""
        from pydantic import ValidationError

        from app.config import Settings

        monkeypatch.setenv("GUARDRAIL_MODE", "off")
        with pytest.raises(ValidationError):
            Settings()

    def test_defaults_hold_when_nothing_is_set(self, monkeypatch):
        from app.config import Settings

        for var in ("MARKET_SUFFIX", "ROUTER_MODE", "GUARDRAIL_MODE", "CORS_ALLOW_ORIGINS"):
            monkeypatch.delenv(var, raising=False)
        s = Settings(_env_file=None)
        assert s.MARKET_SUFFIX == ".NS"
        assert s.ROUTER_MODE == "enforce"
        assert s.GUARDRAIL_MODE == "block"
        assert s.cors_origins == ["http://localhost:5173"]


class TestKeySurvivesAJsonRoundTrip:
    """Audit finding CACHE-01, found by the live E2E run on 2026-08-23.

    Bronze caches its price frame with `DataFrame.to_json`, and pandas writes
    fewer significant digits than a float64 holds. The first analysis of a
    ticker therefore computes Silver from full-precision yfinance floats and
    every later one computes it from the trimmed values, so a hash over the raw
    numbers differed between run 1 and run 2 - and the cache missed exactly the
    repeat it exists to serve. Two distinct keys were written for one ticker
    inside a single test run.
    """

    def test_serialisation_noise_produces_the_same_key(self):
        from app.orchestrator import _quantize_for_key

        fresh = 1390.1500244140625        # straight from yfinance
        round_tripped = 1390.1500244141   # after to_json -> read_json
        assert fresh != round_tripped
        assert _quantize_for_key(fresh) == _quantize_for_key(round_tripped)

    def test_a_genuinely_different_price_still_differs(self):
        """Quantising must not blur real movement into a stale narrative."""
        from app.orchestrator import _quantize_for_key

        assert _quantize_for_key(1390.15) != _quantize_for_key(1390.85)

    def test_it_reaches_nested_metrics(self):
        from app.orchestrator import _quantize_for_key

        got = _quantize_for_key({"sma": [1.23456789012], "g": {"rsi": 55.000000001}})
        assert got == {"sma": [1.234568], "g": {"rsi": 55.0}}

    def test_non_numeric_values_pass_through(self):
        from app.orchestrator import _quantize_for_key

        assert _quantize_for_key({"regime": "bullish", "flag": True, "x": None}) == {
            "regime": "bullish", "flag": True, "x": None,
        }

    def test_the_real_pandas_round_trip_is_covered(self):
        """Reproduces the exact serialisation Bronze uses, not a hand-picked pair."""
        import io

        import pandas as pd

        from app.orchestrator import _quantize_for_key

        df = pd.DataFrame({"Close": [1387.4000244140625, 1390.1500244140625]})
        back = pd.read_json(io.StringIO(df.to_json(orient="index")), orient="index")
        a = float(df["Close"].iloc[-1])
        b = float(back["Close"].iloc[-1])
        assert a != b, "pandas round-trip no longer loses precision; revisit this guard"
        assert _quantize_for_key(a) == _quantize_for_key(b)
