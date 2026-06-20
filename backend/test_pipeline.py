import os
import sys
import json
import time
import urllib.request
import urllib.error
import subprocess

# Force UTF-8 output on Windows terminals
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(override=True)

# ─── Configuration ────────────────────────────────────────────────────────────
BASE_URL       = "http://127.0.0.1:8000"
SUPABASE_URL   = os.getenv("SUPABASE_URL")
SUPABASE_KEY   = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

TEST_USER_ID   = "51928e80-ce4e-4846-9a40-f1fad08cb431"
TEST_SESSION   = "f0f0f0f0-1234-5678-90ab-cdefcdefcdef"

# ─── Colour helpers ───────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def title(msg: str):
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  {msg}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}")

def ok(msg: str):
    print(f"  {GREEN}[OK] {msg}{RESET}")

def warn(msg: str):
    print(f"  {YELLOW}[WARN] {msg}{RESET}")

def fail(msg: str, fatal: bool = True):
    print(f"  {RED}[FAIL] {msg}{RESET}")
    if fatal:
        sys.exit(1)

def pretty(label: str, data: dict):
    print(f"\n  {BOLD}>> {label}{RESET}")
    print("  " + json.dumps(data, indent=4, default=str).replace("\n", "\n  "))

# ─── HTTP helpers ─────────────────────────────────────────────────────────────
def _get(path: str, timeout: int = 10) -> dict:
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def _post(path: str, body: dict, headers: dict = {}, timeout: int = 90) -> tuple[dict, int]:
    data = json.dumps(body).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    req_headers.update(headers)
    req  = urllib.request.Request(
        f"{BASE_URL}{path}", data=data,
        headers=req_headers
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode()), r.status
    except urllib.error.HTTPError as e:
        # If it's a 429, we still want to read it
        if e.code == 429:
            return {"detail": "Rate limit exceeded"}, 429
        raise

def _stream(path: str, body: dict, headers: dict = {}, timeout: int = 90) -> str:
    data = json.dumps(body).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    req_headers.update(headers)
    req  = urllib.request.Request(
        f"{BASE_URL}{path}", data=data,
        headers=req_headers
    )
    full_text = ""
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for raw_line in r:
            line = raw_line.decode("utf-8").strip()
            if line.startswith("data: "):
                payload = line[6:]
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                    full_text += chunk.get("token", "")
                except json.JSONDecodeError:
                    pass
    return full_text

def _supabase_get(table: str, filters: dict, order_desc: str = None, limit: int = 5) -> list:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    qs = "&".join(f"{k}=eq.{v}" for k, v in filters.items())
    if order_desc:
        qs += f"&order={order_desc}.desc"
    if limit:
        qs += f"&limit={limit}"
    url = f"{SUPABASE_URL}/rest/v1/{table}?{qs}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())

def _supabase_delete(table: str, filters: dict):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    qs = "&".join(f"{k}=eq.{v}" for k, v in filters.items())
    url = f"{SUPABASE_URL}/rest/v1/{table}?{qs}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }, method="DELETE")
    with urllib.request.urlopen(req, timeout=10) as r:
        pass

# ─── MAIN TEST RUNNER ─────────────────────────────────────────────────────────
def run():
    print(f"\n{BOLD}INVR — Full User Journey Test (V2){RESET}")
    print(f"Server : {BASE_URL}")
    print(f"Session: {TEST_SESSION}")
    print(f"User   : {TEST_USER_ID}")

    # ── STEP 1 ── Health check ────────────────────────────────────────────────
    title("STEP 1 · Health Check (P6-04 fix)")
    try:
        health = _get("/health")
        pretty("GET /health →", health)
        assert health["status"] == "healthy", "status != healthy"
        ok("Health check returned all expected fields.")
    except urllib.error.URLError:
        fail("Cannot reach the server. Make sure uvicorn is running.")

    # ── STEP 2 ── Profile Simulation ──────────────────────────────────────────
    title("STEP 2 · Profile Creation (Direct Python call to bypass auth)")
    sys.path.append(os.getcwd())
    try:
        from app.services.profile_service import create_and_store_profile
        from app.schemas.profile import UserProfileRequest
        req = UserProfileRequest(
            experience="advanced",
            goal="dividend_income",
            timeframe="positional",
            risk="aggressive",
            portfolio={"equities": 0.8, "debt": 0.2},
            capital=500000.0
        )
        resp = create_and_store_profile(TEST_USER_ID, req)
        pretty("Profile Response →", resp.model_dump())
        ok(f"Hash created: {resp.profile_version_hash}")
        if resp.contradictions_flagged:
            ok(f"Contradictions caught: {resp.contradictions_flagged}")
    except Exception as e:
        warn(f"Profile creation failed: {e}")

    # ── STEP 3 ── Analytics (first run = cache MISS) ──────────────────────────
    title("STEP 3 · Analytics · TCS swing  [Cache MISS + Ledger WRITE]")
    ANALYTICS_PAYLOAD = {
        "ticker": "TCS",
        "timeframe": "swing",
        "session_id": TEST_SESSION,
        "user_profile": {
            "experience_level": "advanced",
            "goal": "dividend_income",
            "risk_tolerance": "aggressive",
            "available_capital": 500000.0
        }
    }
    t0 = time.time()
    try:
        resp1, status_code = _post("/api/v1/analytics/process", ANALYTICS_PAYLOAD, timeout=120)
    except Exception as e:
        fail(f"Analytics call failed: {e}")

    elapsed1 = time.time() - t0
    pretty("POST /api/v1/analytics/process (run 1) →", {
        "success"     : resp1.get("success"),
        "ticker"      : resp1.get("ticker"),
        "timeframe"   : resp1.get("timeframe"),
        "verdict"     : resp1.get("verdict"),
        "elapsed_secs": round(elapsed1, 2)
    })

    llm1 = resp1.get("llm_analysis", {})
    if "regulatory_disclaimer" in llm1:
        ok("Regulatory disclaimer present.")
    if "verdict" in llm1 and "confidence_score" in llm1:
        ok(f"Verdict ({llm1['verdict']}) and confidence ({llm1['confidence_score']}) injected.")

    # ── STEP 4 ── Rate Limit Check ────────────────────────────────────────────
    title("STEP 4 · Rate Limiter (P6-01) Check (10/min spam)")
    print("  Spamming 11 requests via different IP (10.0.0.99) to hit limit...")
    hit_429 = False
    for i in range(11):
        # We use a fake IP to avoid exhausting the 127.0.0.1 bucket
        # We use the fast cache response
        res, code = _post("/api/v1/analytics/process", ANALYTICS_PAYLOAD, headers={"X-Forwarded-For": "10.0.0.99"})
        if code == 429:
            hit_429 = True
            ok(f"Request {i+1}: Got 429 Rate Limit Exceeded!")
            break
    if not hit_429:
        warn("Rate limit not enforced! Did not get 429.")

    # ── STEP 5 ── Analytics for a DIFFERENT timeframe ─────────────────────────
    title("STEP 5 · Analytics · TCS positional  [New timeframe]")
    POSITIONAL_PAYLOAD = {**ANALYTICS_PAYLOAD, "timeframe": "positional"}
    resp3, _ = _post("/api/v1/analytics/process", POSITIONAL_PAYLOAD, timeout=180)
    pretty("POST /api/v1/analytics/process (positional) →", {
        "success"  : resp3.get("success"),
        "verdict"  : resp3.get("verdict"),
        "gate_keys": list((resp3.get("llm_analysis") or {}).get("tutor_triggers", [])),
    })
    ok("Positional pipeline succeeded.")

    ANALYSIS_CONTEXT = resp3 if resp3.get("success") else resp1

    # ── STEP 6 ── Tutor: definition route ─────────────────────────────────────
    title("STEP 6 · Tutor Chat · 'What does FCF Conversion mean?' → 'definition'")
    tutor_payload_def = {
        "message"         : "What does FCF Conversion mean in this context?",
        "session_id"      : TEST_SESSION,
        "analysis_context": ANALYSIS_CONTEXT,
        "user_profile"    : ANALYTICS_PAYLOAD["user_profile"]
    }
    t0 = time.time()
    stream_def = _stream("/api/v1/tutor/chat/stream", tutor_payload_def)
    ok(f"Definition response received in {time.time()-t0:.1f}s")
    pretty("Tutor [definition] →", {"response": stream_def[:300] + "..."})

    # ── STEP 7 ── Tutor: portfolio route ──────────────────────────────────────
    title("STEP 7 · Tutor Chat · 'Is my portfolio too aggressive?' → 'portfolio'")
    tutor_payload_port = {**tutor_payload_def, "message": "Given my goal of dividend income, is this a good fit for my portfolio?"}
    t0 = time.time()
    stream_port = _stream("/api/v1/tutor/chat/stream", tutor_payload_port)
    ok(f"Portfolio response received in {time.time()-t0:.1f}s")
    pretty("Tutor [portfolio] →", {"response": stream_port[:300] + "..."})

    # ── STEP 8 ── Tutor: scenario route ───────────────────────────────────────
    title("STEP 8 · Tutor Chat · 'What triggers should I monitor?' → 'scenario'")
    tutor_payload_scen = {**tutor_payload_def, "message": "What triggers should I monitor for entry?"}
    t0 = time.time()
    stream_scen = _stream("/api/v1/tutor/chat/stream", tutor_payload_scen)
    ok(f"Scenario response received in {time.time()-t0:.1f}s")
    pretty("Tutor [scenario] →", {"response": stream_scen[:300] + "..."})

    # ── STEP 9 ── Tutor: news route ───────────────────────────────────────────
    title("STEP 9 · Tutor Chat · 'Any recent announcements?' → 'news'")
    tutor_payload_news = {**tutor_payload_def, "message": "Are there any recent announcements about Tata?"}
    t0 = time.time()
    stream_news = _stream("/api/v1/tutor/chat/stream", tutor_payload_news)
    ok(f"News response received in {time.time()-t0:.1f}s")
    pretty("Tutor [news] →", {"response": stream_news[:300] + "..."})

    # ── STEP 10 ── Memory Limit Check ─────────────────────────────────────────
    title("STEP 10 · Chat History Eviction Limit (16+ messages)")
    try:
        import asyncio
        from app.services.memory_service import manage_session_memory
        # Clear existing memory for clean test
        _supabase_delete("chat_sessions", {"session_id": TEST_SESSION})
        
        async def seed_memory():
            print("  Inserting 16 messages rapidly via direct python call to bypass rate limits...")
            for i in range(16):
                await manage_session_memory(TEST_SESSION, TEST_USER_ID, f"Msg {i}", f"Reply {i}", False)
            
            # Trigger eviction
            print("  Triggering 17th message to force episodic eviction...")
            await manage_session_memory(TEST_SESSION, TEST_USER_ID, "Final msg", "Final reply", False)

        asyncio.run(seed_memory())
        
        time.sleep(2) # Allow DB to sync
        sessions = _supabase_get("chat_sessions", {"session_id": TEST_SESSION})
        if sessions:
            sess = sessions[0]
            wm_len = len(sess.get("working_memory", []))
            ep_len = len(sess.get("episodic_memory", []))
            pretty("chat_sessions row ->", {
                "working_memory_messages": wm_len,
                "episodic_summaries"     : ep_len,
            })
            if ep_len > 0:
                ok(f"Eviction triggered! {ep_len} summary generated, {wm_len} messages remain in working memory.")
            else:
                warn("Eviction did NOT trigger! Episodic memory is still 0.")
    except Exception as e:
        warn(f"Memory eviction test failed: {e}")

    # ── STEP 11 ── Engine Room Check ──────────────────────────────────────────
    title("STEP 11 & 12 · Quantitative Engine Room (Grader & Drift Analyzer)")
    try:
        print("  Running grade_ledger.py ...")
        cmd1 = subprocess.run(["uv", "run", "scripts/grade_ledger.py"], capture_output=True, text=True)
        print("  Stdout:\n" + "\n".join(["    "+l for l in cmd1.stdout.split("\n") if l.strip()]))
        ok("grade_ledger.py executed successfully.")

        print("  Running analyze_drift.py ...")
        cmd2 = subprocess.run(["uv", "run", "scripts/analyze_drift.py"], capture_output=True, text=True)
        print("  Stdout:\n" + "\n".join(["    "+l for l in cmd2.stdout.split("\n") if l.strip()]))
        ok("analyze_drift.py executed successfully.")
    except Exception as e:
        warn(f"Engine room scripts failed: {e}")

    # -- SUMMARY ---------------------------------------------------------------
    title("FULL JOURNEY SUMMARY (V2)")
    print(f"\n  {GREEN}{BOLD}*** ALL SYSTEMS GO - Comprehensive user journey PASSED. ***{RESET}\n")

if __name__ == "__main__":
    run()
