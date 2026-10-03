"use client";
// Settings (MASTER_SPEC Part 28): Model access and Spend controls. The API key is write-only:
// it is typed here, sent once to the backend (which encrypts it), and the field is cleared.
// It is never kept in browser storage, and the backend only ever returns its last 4 characters.
import { useEffect, useState } from "react";
import { getJSON, sendJSON } from "@/lib/api";
import { usd } from "./Dashboards";

type Provider = "anthropic" | "onprem" | "bedrock";
interface ModelAccess { provider: Provider; endpoint: string | null; model: string; key_set: boolean; key_masked: string | null; updated_at: string | null }
interface TestResult { ok: boolean; latency_ms: number | null; model: string | null; error: string | null; warning?: string; provider: string }
interface Caps { per_design_usd: number; daily_usd: number; spent_today_usd: number; source: string }

const PROVIDERS: [Provider, string][] = [["anthropic", "Anthropic API"], ["onprem", "On-prem model endpoint"], ["bedrock", "AWS Bedrock"]];

function ModelAccessCard() {
  const [cfg, setCfg] = useState<ModelAccess | null>(null);
  const [provider, setProvider] = useState<Provider>("anthropic");
  const [endpoint, setEndpoint] = useState("");
  const [key, setKey] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [test, setTest] = useState<TestResult | null>(null);
  const [busy, setBusy] = useState<"" | "save" | "test">("");

  useEffect(() => {
    getJSON<ModelAccess>("/settings/model-access").then((c) => {
      setCfg(c); setProvider(c.provider); setEndpoint(c.endpoint ?? "");
    }).catch((e: Error) => setMsg({ ok: false, text: `Cannot reach the backend: ${e.message}` }));
  }, []);

  const save = async () => {
    setBusy("save"); setMsg(null); setTest(null);
    try {
      const c = await sendJSON<ModelAccess>("PUT", "/settings/model-access", { provider, api_key: key || null, endpoint: endpoint || null });
      setCfg(c); setKey("");
      setMsg({ ok: true, text: "Saved on the server (encrypted)." });
    } catch (e) {
      setMsg({ ok: false, text: (e as Error).message });
    } finally {
      setBusy("");
    }
  };
  const runTest = async () => {
    setBusy("test"); setTest(null);
    try { setTest(await sendJSON<TestResult>("POST", "/settings/model-access/test")); }
    catch (e) { setTest({ ok: false, latency_ms: null, model: null, error: (e as Error).message, provider }); }
    finally { setBusy(""); }
  };

  return (
    <section className="card set-card" data-testid="model-access" aria-labelledby="ma-h">
      <h2 id="ma-h">Model access</h2>
      <p className="muted desc">How S2S reaches a model. Paste a key once: it is stored on the server, encrypted, and can be replaced but never read back.</p>
      <div className="field">
        <span className="lbl" id="prov-l">Provider</span>
        <div className="seg" role="group" aria-labelledby="prov-l">
          {PROVIDERS.map(([p, label]) => (
            <button key={p} type="button" className="btn" aria-pressed={provider === p} data-testid={`provider-${p}`}
              onClick={() => setProvider(p)}>{label}</button>
          ))}
        </div>
        {provider === "bedrock" && <small className="muted" data-testid="bedrock-note">Bedrock can be selected and saved; model calls through it are not wired yet (Part 28.6, hardened version).</small>}
      </div>
      {provider === "onprem" && (
        <div className="field">
          <label htmlFor="endpoint" className="lbl">On-prem model endpoint</label>
          <input id="endpoint" className="inp" data-testid="endpoint" placeholder="https://models.internal.example.net"
            value={endpoint} onChange={(e) => setEndpoint(e.target.value)} autoComplete="off" spellCheck={false} />
          <small className="muted">Must speak the Anthropic Messages API. Model calls stay inside your network.</small>
        </div>
      )}
      <div className="field">
        <label htmlFor="apikey" className="lbl">API key{provider === "onprem" ? " (if your endpoint needs one)" : ""}</label>
        {cfg?.key_set && <div className="mono" data-testid="key-masked">Saved key: {cfg.key_masked}</div>}
        <div className="inrow">
          <input id="apikey" className="inp" data-testid="apikey" type="password" autoComplete="off" spellCheck={false}
            placeholder={cfg?.key_set ? "Paste a new key to replace it" : "Paste your Anthropic API key"}
            value={key} onChange={(e) => setKey(e.target.value)} />
          <button type="button" className="btn primary" data-testid="save-access" disabled={busy !== ""} onClick={save}>Save</button>
        </div>
        <small className="muted">Model for all agents: <b className="mono" data-testid="model">{cfg?.model ?? "claude-sonnet-5-5"}</b></small>
      </div>
      {msg && <p className={msg.ok ? "ok-text" : "bad-text"} role="status" data-testid="access-msg">{msg.text}</p>}
      <div className="inrow" style={{ marginTop: 6 }}>
        <button type="button" className="btn" data-testid="test-connection" disabled={busy !== "" || !cfg} onClick={runTest}>
          {busy === "test" ? "Testing…" : "Test connection"}
        </button>
        {test && (
          <span className={test.ok ? "ok-text" : "bad-text"} role="status" data-testid="test-result" data-ok={test.ok}>
            {test.ok ? "✓ Connected" : "✕ Failed"}
            {test.latency_ms !== null && <> · <span className="mono">{test.latency_ms} ms</span></>}
            {test.model && <> · <span className="mono">{test.model}</span></>}
            {test.error && <> · {test.error}</>}
            {test.warning && <> · {test.warning}</>}
          </span>
        )}
      </div>
    </section>
  );
}

function SpendCard() {
  const [caps, setCaps] = useState<Caps | null>(null);
  const [perDesign, setPerDesign] = useState("");
  const [daily, setDaily] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    getJSON<Caps>("/settings/spend-caps").then((c) => {
      setCaps(c); setPerDesign(String(c.per_design_usd)); setDaily(String(c.daily_usd));
    }).catch((e: Error) => setMsg({ ok: false, text: `Cannot reach the backend: ${e.message}` }));
  }, []);

  const save = async () => {
    setMsg(null);
    try {
      const c = await sendJSON<Caps>("PUT", "/settings/spend-caps", { per_design_usd: Number(perDesign), daily_usd: Number(daily) });
      setCaps(c); setPerDesign(String(c.per_design_usd)); setDaily(String(c.daily_usd));
      setMsg({ ok: true, text: `Saved to ${c.source}.` });
    } catch (e) {
      setMsg({ ok: false, text: (e as Error).message });
    }
  };

  return (
    <section className="card set-card" data-testid="spend-caps" aria-labelledby="sc-h">
      <h2 id="sc-h">Spend controls</h2>
      <p className="muted desc">Hard caps. Once a cap is reached the run stops: no further model call is made. (The call that crosses the cap has already happened; its cost is only known when it returns.)</p>
      <div className="field">
        <label htmlFor="cap-design" className="lbl">Per-design cap (USD)</label>
        <input id="cap-design" className="inp" data-testid="cap-design" inputMode="decimal" value={perDesign} onChange={(e) => setPerDesign(e.target.value)} />
      </div>
      <div className="field">
        <label htmlFor="cap-daily" className="lbl">Daily cap (USD, all work, since 00:00 UTC)</label>
        <input id="cap-daily" className="inp" data-testid="cap-daily" inputMode="decimal" value={daily} onChange={(e) => setDaily(e.target.value)} />
        {caps && <small className="muted">Spent today: <span className="mono" data-testid="spent-today">{usd(caps.spent_today_usd)}</span></small>}
      </div>
      <div className="inrow" style={{ marginTop: 6 }}>
        <button type="button" className="btn primary" data-testid="save-caps" onClick={save}>Save caps</button>
        {msg && <span className={msg.ok ? "ok-text" : "bad-text"} role="status" data-testid="caps-msg">{msg.text}</span>}
      </div>
    </section>
  );
}

export function Settings() {
  return (
    <div className="set-wrap" data-testid="settings">
      <ModelAccessCard />
      <SpendCard />
    </div>
  );
}
