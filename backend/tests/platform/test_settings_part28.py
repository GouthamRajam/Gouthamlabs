"""Settings -> Model access and Spend controls (MASTER_SPEC Part 28), against real Postgres/Redis
and, for Test connection, the real Anthropic API (with a deliberately invalid key: the API
really answers 401; no test here can produce a passing connection without a real key)."""
from __future__ import annotations

import json
import secrets as pysecrets
import stat
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from tests.platform.conftest import REPO, new_design, wait_for
from tests.platform.test_m03_acceptance import _events, _run_status

FAKE_KEY = f"sk-ant-api03-S2STESTONLY-{pysecrets.token_hex(16)}-Q9Z4"  # not a real key


def _client():
    from s2s.api.app import app
    return TestClient(app)


def test_key_is_encrypted_at_rest_masked_and_write_only(platform):
    c = _client()
    assert c.get("/settings/model-access").json()["key_set"] is False
    r = c.put("/settings/model-access", json={"provider": "anthropic", "api_key": FAKE_KEY})
    assert r.status_code == 200, r.text
    view = r.json()
    print("\nPUT response:", json.dumps(view))
    assert view["key_set"] and view["key_masked"] == "••••••••Q9Z4" and view["model"] == "claude-sonnet-5-5"
    assert FAKE_KEY not in r.text and FAKE_KEY[:-4] not in c.get("/settings/model-access").text

    d = Path(platform.env["S2S_SECRETS_DIR"])
    enc, master = d / "model_access.enc", d / "master.key"
    for f in (enc, master):
        mode = stat.S_IMODE(f.stat().st_mode)
        print(f"{f.name}: mode {oct(mode)}, {f.stat().st_size} bytes")
        assert mode == 0o600
    blob = enc.read_bytes()
    assert FAKE_KEY.encode() not in blob and b"sk-ant" not in blob and b"Q9Z4" not in blob
    print("ciphertext starts:", blob[:24].decode(), "...")

    from s2s import secrets
    assert secrets.get("model_access")["api_key"] == FAKE_KEY  # decrypts only server-side

    # replace without resending: provider change keeps the stored key; a new key replaces it
    assert c.put("/settings/model-access", json={"provider": "anthropic"}).json()["key_masked"].endswith("Q9Z4")
    assert c.put("/settings/model-access", json={"provider": "anthropic", "api_key": "sk-ant-new-ABCD"}).json()["key_masked"].endswith("ABCD")
    # bad input: rejected, and the submitted value is never echoed back
    assert c.put("/settings/model-access", json={"provider": "nope"}).status_code == 400
    long_key = "sk-ant-" + "x" * 600
    r = c.put("/settings/model-access", json={"provider": "anthropic", "api_key": long_key})
    assert r.status_code == 422 and "xxxxxxxx" not in r.text
    assert c.put("/settings/model-access", json={"provider": "onprem", "endpoint": "not a url"}).status_code == 400


def test_secret_files_are_gitignored():
    import subprocess
    for p in ("var/secrets/model_access.enc", "var/secrets/master.key", "backend/x/model_access.enc"):
        out = subprocess.run(["git", "check-ignore", "-v", p], cwd=REPO, capture_output=True, text=True)
        print(out.stdout.strip())
        assert out.returncode == 0, f"{p} is not ignored"


def test_test_connection_reaches_the_real_api(platform):
    c = _client()
    r = c.post("/settings/model-access/test").json()
    print("\nno key saved ->", r)
    assert r["ok"] is False and "no API key saved" in r["error"]

    c.put("/settings/model-access", json={"provider": "anthropic", "api_key": FAKE_KEY})
    r = c.post("/settings/model-access/test").json()
    print("invalid key  ->", r)
    assert r["ok"] is False and r["model"] == "claude-sonnet-5-5" and r["latency_ms"] > 0
    assert "HTTP 401" in r["error"] and "authentication_error" in r["error"]  # the real API said no
    assert FAKE_KEY not in json.dumps(r)

    c.put("/settings/model-access", json={"provider": "bedrock"})
    r = c.post("/settings/model-access/test").json()
    print("bedrock      ->", r)
    assert r["ok"] is False and "not wired yet" in r["error"]


def test_gateway_sends_the_stored_key(platform, monkeypatch):
    """The agents' gateway reads the key from the secret: with the fake key saved, a gateway
    call reaches the real API and is refused (401) for that key; nothing is metered."""
    import anthropic
    from s2s.db.models import UsageRecord
    from s2s.db.session import session
    from s2s.finance.meter import TaskRef
    from s2s.models import access
    from s2s.models.gateway import ModelGateway
    from s2s.orchestrator.engine import create_run
    monkeypatch.setenv("S2S_MODEL_PROVIDER", "anthropic")  # this test is about the API path
    _client().put("/settings/model-access", json={"provider": "anthropic", "api_key": FAKE_KEY})
    sdk_client, model = access.client()
    assert sdk_client.api_key == FAKE_KEY and model == "claude-sonnet-5-5"
    with session() as s:
        run = create_run(s, new_design(s), to_stage="spec")
        task = TaskRef(id=f"tsk_gw", run_id=run.id, agent_id="Iris", stage="spec", team_id=None, budget={})
    with pytest.raises(anthropic.AuthenticationError) as e:
        ModelGateway.from_settings().complete(task=task, system="s", messages=[{"role": "user", "content": "hi"}],
                                              max_tokens=8)
    print("\ngateway call with the stored fake key ->", type(e.value).__name__, e.value.status_code)
    assert FAKE_KEY not in str(e.value)
    with session() as s:
        assert s.scalar(select(UsageRecord).where(UsageRecord.agent_id == "Iris")) is None


def test_key_never_logged_or_stored_in_plaintext(platform):
    """Drive the API over HTTP with debug logging, then search every log, the events table,
    usage records, the Redis event stream and the secrets dir for the key."""
    from s2s.config import settings
    from s2s.db.session import session
    from s2s.events.bus import redis_client
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    platform._spawn(["-m", "uvicorn", "s2s.api.app:app", "--port", str(port), "--log-level", "debug"], "api_debug.log")
    base = f"http://127.0.0.1:{port}"
    wait_for(lambda: _ok(f"{base}/health"), 15, every=0.1, what="api")
    assert httpx.put(f"{base}/settings/model-access", json={"provider": "anthropic", "api_key": FAKE_KEY}).status_code == 200
    httpx.post(f"{base}/settings/model-access/test", timeout=60)
    httpx.get(f"{base}/settings/model-access")
    httpx.put(f"{base}/settings/model-access", json={"provider": "anthropic", "api_key": "sk-" + "y" * 700})  # 422 path
    time.sleep(0.5)

    hits = []
    for f in Path(platform.tmp).rglob("*"):
        if f.is_file() and FAKE_KEY.encode() in f.read_bytes():
            hits.append(str(f))
    log = platform.log("api_debug.log")
    with session() as s:
        n_ev = s.scalar(text("select count(*) from events where cast(events as text) like :k"), {"k": f"%{FAKE_KEY}%"})
        n_use = s.scalar(text("select count(*) from usage_records where cast(usage_records as text) like :k"),
                         {"k": f"%{FAKE_KEY}%"})
    stream = json.dumps([[k, v] for k, v in redis_client().xrange(settings().event_stream)], default=str)
    print(f"\napi debug log: {len(log.splitlines())} lines; files containing key: {hits}; "
          f"events rows: {n_ev}; usage rows: {n_use}; redis stream entries containing key: {stream.count(FAKE_KEY)}")
    assert "PUT /settings/model-access" in log  # the log really captured these requests
    assert hits == [] and n_ev == 0 and n_use == 0 and FAKE_KEY not in stream


def _ok(url: str) -> bool:
    try:
        return httpx.get(url, timeout=0.5).status_code == 200
    except httpx.HTTPError:
        return False


@pytest.mark.parametrize("cap", ["per_design_usd", "daily_usd"])
def test_spend_cap_stops_the_run(platform, cap):
    """A cap set in Settings is written to finance.yaml and stops a real (dummy-agent) run:
    the task pauses with a hard stop, and no model call is made after the cap is reached."""
    from s2s.db.models import Task, UsageRecord
    from s2s.db.session import session
    from s2s.orchestrator.engine import create_run
    fin = Path(platform.tmp) / "finance.yaml"
    fin.write_text((REPO / "config" / "finance.yaml").read_text())  # the real file's layout
    platform.env["S2S_FINANCE_CONFIG"] = str(fin)
    platform._mp.setenv("S2S_FINANCE_CONFIG", str(fin))
    caps = {"per_design_usd": 75.0, "daily_usd": 150.0, cap: 0.004}  # a dummy run costs ~$0.014
    r = _client().put("/settings/spend-caps", json=caps)
    assert r.status_code == 200, r.text
    line = next(ln for ln in fin.read_text().splitlines() if ln.startswith("spend_caps:"))
    print(f"\nfinance.yaml now: {line}")
    assert r.json()["per_design_usd"] == caps["per_design_usd"] and r.json()["daily_usd"] == caps["daily_usd"]
    assert "# Hard spend caps (Part 28.3)" in fin.read_text()  # comments kept

    with session() as s:
        run_id = create_run(s, new_design(s), dummy={"step_delay_s": 0.02}).id
    platform.start_orchestrator()
    what = {"per_design_usd": "per-design spend cap", "daily_usd": "daily spend cap"}[cap]
    stop = wait_for(lambda: [e for e in _events(run_id, type="escalation") if e.detail.get("budget") == what],
                    60, every=0.2, what="spend-cap stop")[0]
    print("stop event:", stop.summary)
    with session() as s:
        n_calls = s.scalar(select(text("count(*)")).select_from(UsageRecord).where(UsageRecord.source == "llm"))
        spent = float(s.scalar(select(text("coalesce(sum(cost_usd),0)")).select_from(UsageRecord)))
        paused = s.scalars(select(Task).where(Task.run_id == run_id, Task.status == "paused")).all()
    time.sleep(2)  # nothing more is spent once the cap has stopped the run
    with session() as s:
        assert s.scalar(select(text("count(*)")).select_from(UsageRecord).where(UsageRecord.source == "llm")) == n_calls
    print(f"model calls metered: {n_calls}; spent ${spent:.6f} vs cap ${caps[cap]}; "
          f"paused: {[t.agent_id for t in paused]}; run status: {_run_status(run_id)}")
    assert paused and _run_status(run_id) != "completed"
    assert stop.detail["rule"] == "hard stop" and stop.detail["limit"] == caps[cap]
