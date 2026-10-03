// Event sources for the three modes (Part 12.3). All feed the same store.applyEvent().
import { getJSON, runEvents, wsBase } from "./api";
import { demoScript } from "./demo";
import { useOffice } from "./store";
import type { S2SEvent } from "./types";

type Stop = () => void;

/** Live mode: subscribe to /ws/events; backfill recent history; reconnect from the last id. */
export function startLive(): Stop {
  const { apply, applyMany, set } = useOffice.getState();
  let ws: WebSocket | null = null;
  let stopped = false;
  let lastStreamId: string | undefined;
  let retry = 500;

  const backfill = async () => {
    try {
      const recent = await getJSON<S2SEvent[]>("/events?limit=300");
      applyMany(recent.reverse());
    } catch { /* live stream still works without history */ }
  };

  const connect = () => {
    if (stopped) return;
    set({ connection: "connecting" });
    const url = `${wsBase()}/ws/events${lastStreamId ? `?since=${encodeURIComponent(lastStreamId)}` : ""}`;
    ws = new WebSocket(url);
    ws.onopen = () => { retry = 500; set({ connection: "open" }); if (!lastStreamId) void backfill(); };
    ws.onmessage = (m) => {
      const ev = JSON.parse(m.data as string) as S2SEvent & { from?: string };
      if ((ev as { type: string }).type === "stream.subscribed") return;
      if (ev.stream_id) lastStreamId = ev.stream_id;
      apply(ev);
    };
    ws.onclose = () => {
      if (stopped) return;
      set({ connection: "closed" });
      setTimeout(connect, retry);
      retry = Math.min(retry * 2, 8000);
    };
  };
  connect();
  return () => { stopped = true; ws?.close(); };
}

/** Replay mode: play a stored run's events at 1x-50x. Idle gaps over 3 s are shortened. */
export const MAX_GAP_MS = 3000;
export function startReplay(runId: string, speed: number): Stop {
  const store = useOffice.getState();
  let stopped = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let events: S2SEvent[] = [];
  let i = 0;

  const tick = () => {
    if (stopped) return;
    const s = useOffice.getState();
    if (!s.replay?.playing) { timer = setTimeout(tick, 100); return; }
    if (i >= events.length) { store.set({ replay: { ...s.replay, playing: false, position: i } }); return; }
    store.apply(events[i]);
    i += 1;
    const next = events[i];
    const gap = next ? Math.min(MAX_GAP_MS, Math.max(0, Date.parse(next.ts) - Date.parse(events[i - 1].ts))) : 0;
    const sp = useOffice.getState().replay?.speed ?? speed;
    useOffice.getState().set({ replay: { ...useOffice.getState().replay!, position: i } });
    timer = setTimeout(tick, gap / sp);
  };

  store.set({ connection: "connecting", replay: { runId, speed, playing: false, position: 0, total: 0 } });
  void runEvents(runId).then((evs) => {
    events = evs;
    store.set({ connection: "open", replay: { runId, speed, playing: true, position: 0, total: evs.length } });
    tick();
  }).catch(() => store.set({ connection: "closed" }));
  return () => { stopped = true; if (timer) clearTimeout(timer); };
}

/** Demo mode: the built-in scripted simulation (clearly labeled; never real output). */
export function startDemo(speed = 1): Stop {
  const store = useOffice.getState();
  let stopped = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let loop = 0;
  const run = () => {
    const script = demoScript(loop++);
    let i = 0;
    const step = () => {
      if (stopped) return;
      if (i >= script.length) { timer = setTimeout(run, 1500); return; }
      const [delay, ev] = script[i++];
      timer = setTimeout(() => { store.apply({ ...ev, ts: new Date().toISOString() }); step(); }, delay / speed);
    };
    step();
  };
  store.set({ connection: "offline" });
  run();
  return () => { stopped = true; if (timer) clearTimeout(timer); };
}
