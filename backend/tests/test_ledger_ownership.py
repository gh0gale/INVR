"""Guards the ownership boundary between the shared ledger and one user's history.

Audit finding ISO-01: two accounts signed in and saw the same stocks, because
the workspace read `algorithmic_ledger` directly and that table carries no
user_id. The fix keeps the ledger shared - it is deduplicated on
(ticker, timeframe, date, pipeline_version) so one deterministic verdict is
stored once and graded once - and puts ownership on `prediction_interactions`.

Two invariants therefore have to hold together, and breaking either one
reintroduces the bug or corrupts the grading cohort:

  1. the interaction row carries the authenticated user_id
  2. the ledger row does NOT

These tests use a fake Supabase client rather than a live one, so they run in
CI with no network, like the rest of the suite.
"""
import asyncio
import inspect

import pytest

from app.services import ledger_service


class FakeQuery:
    """Records what was written and answers the de-duplication select."""

    def __init__(self, table, sink, existing):
        self.table = table
        self.sink = sink
        self.existing = existing
        self._mode = None
        self._payload = None

    def select(self, *_args, **_kwargs):
        self._mode = "select"
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self._mode = "insert"
        self._payload = payload
        return self

    def execute(self):
        if self._mode == "insert":
            self.sink.setdefault(self.table, []).append(self._payload)
            return type("Res", (), {"data": [{"log_id": "log-1"}]})()
        if self.table == "algorithmic_ledger":
            return type("Res", (), {"data": self.existing})()
        return type("Res", (), {"data": []})()


class FakeSupabase:
    def __init__(self, existing=None):
        self.writes = {}
        self.existing = existing or []

    def table(self, name):
        return FakeQuery(name, self.writes, self.existing)


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeSupabase()
    monkeypatch.setattr(ledger_service, "supabase", db)
    return db


def run_log(user_id="user-abc"):
    return ledger_service.log_prediction_to_ledger(
        "session-1",
        {"ticker": "TEST.NS"},
        {"ticker": "TEST.NS", "timeframe": "swing", "verdict": "MONITOR"},
        {"summary": "narrative"},
        user_id,
    )


class TestInteractionOwnership:
    def test_interaction_row_carries_the_user_id(self, fake_db):
        asyncio.run(run_log("user-abc"))
        interactions = fake_db.writes["prediction_interactions"]
        assert len(interactions) == 1
        assert interactions[0]["user_id"] == "user-abc"

    def test_two_users_produce_two_distinct_interaction_rows(self, fake_db):
        asyncio.run(run_log("user-abc"))
        asyncio.run(run_log("user-xyz"))
        owners = [row["user_id"] for row in fake_db.writes["prediction_interactions"]]
        assert owners == ["user-abc", "user-xyz"]

    def test_interaction_is_still_written_when_the_ledger_row_already_exists(self):
        """The dedup path must not skip attribution.

        A second user analysing a ticker someone else already ran today hits the
        duplicate branch. If attribution lived only on the insert path, that
        user would silently get no history row - which is the reported bug
        wearing a different hat.
        """
        db = FakeSupabase(existing=[{"log_id": "log-existing"}])
        import app.services.ledger_service as mod

        original = mod.supabase
        mod.supabase = db
        try:
            asyncio.run(run_log("user-second"))
        finally:
            mod.supabase = original

        assert "algorithmic_ledger" not in db.writes, "should have taken the dedup path"
        interactions = db.writes["prediction_interactions"]
        assert interactions[0]["user_id"] == "user-second"
        assert interactions[0]["log_id"] == "log-existing"


class TestLedgerStaysShared:
    def test_ledger_row_has_no_user_id(self, fake_db):
        """The grading cohort must stay one row per (ticker, timeframe, date, version).

        Attaching a user to the ledger row would multiply identical predictions
        across accounts and inflate every win/loss count the Engine Room
        computes.
        """
        asyncio.run(run_log("user-abc"))
        ledger_rows = fake_db.writes["algorithmic_ledger"]
        assert len(ledger_rows) == 1
        assert "user_id" not in ledger_rows[0]

    def test_ledger_row_keeps_its_dedup_key(self, fake_db):
        asyncio.run(run_log())
        row = fake_db.writes["algorithmic_ledger"][0]
        for field in ("ticker", "timeframe", "date", "pipeline_version"):
            assert field in row, f"{field} is part of the de-duplication key"


class TestCallSignature:
    def test_user_id_is_the_fifth_positional_argument(self):
        """The analytics route passes these positionally through add_task.

        Inserting a parameter ahead of user_id would send the llm_output into
        the user_id slot without any type error to catch it.
        """
        params = list(
            inspect.signature(ledger_service.log_prediction_to_ledger).parameters
        )
        assert params == [
            "session_id",
            "silver_metrics",
            "verdict_draft",
            "llm_output",
            "user_id",
        ]

    def test_user_id_is_optional_so_cli_scripts_still_work(self):
        """`analyze_and_chat.py` calls this without an authenticated user."""
        sig = inspect.signature(ledger_service.log_prediction_to_ledger)
        assert sig.parameters["user_id"].default is None

    def test_route_passes_user_id_to_the_ledger_write(self):
        """Reads the route source rather than trusting the wiring by eye."""
        import app.api.routes.analytics as analytics

        source = inspect.getsource(analytics.process_pipeline)
        write = source[source.index("log_prediction_to_ledger("):]
        call = write[: write.index(")")]
        assert "user_id" in call, "the route must forward the authenticated user"
        assert call.index("llm_output") < call.index("user_id"), "argument order"


class TestWrittenBeforeResponding:
    """Audit MU-04. The row used to be written by a BackgroundTask after the
    response, so a worker recycle could lose it and the frontend waited a fixed
    three seconds hoping it had landed."""

    def test_route_awaits_the_write_instead_of_backgrounding_it(self):
        import app.api.routes.analytics as analytics

        source = inspect.getsource(analytics.process_pipeline)
        assert "await log_prediction_to_ledger(" in source
        assert "add_task" not in source

    def test_response_carries_the_log_id(self):
        import app.api.routes.analytics as analytics

        source = inspect.getsource(analytics.process_pipeline)
        assert "log_id=log_id" in source

    def test_returns_the_new_rows_log_id(self, fake_db):
        assert asyncio.run(run_log()) == "log-1"

    def test_returns_the_existing_rows_log_id_on_the_dedup_path(self, monkeypatch):
        db = FakeSupabase(existing=[{"log_id": "log-existing"}])
        monkeypatch.setattr(ledger_service, "supabase", db)
        assert asyncio.run(run_log()) == "log-existing"

    def test_a_failed_write_returns_none_rather_than_raising(self, monkeypatch):
        """The analysis is still valid without its ledger row; the request must not 500."""

        class Broken:
            def table(self, name):
                raise RuntimeError("supabase unreachable")

        monkeypatch.setattr(ledger_service, "supabase", Broken())
        assert asyncio.run(run_log()) is None
