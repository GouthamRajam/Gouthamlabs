"use client";
// 3D view of a run's GDSII: every layer as boxes at the PDK's own height and thickness (from the
// SKY130 Magic tech file, via GET /runs/{id}/layout3d). Drag to rotate, scroll to zoom, right-drag
// (or two fingers) to pan. A display aid only: never used for any check.
import { useEffect, useRef, useState } from "react";
import { getJSON } from "@/lib/api";

type Layer = { name: string; gds: string; z_um: number; t_um: number; boxes: number[][]; count: number; truncated: boolean };
type Geometry = { top: string; bbox_um: number[]; layers: Layer[] };

// one distinct color per layer, ordered bottom to top (wells/diffusion warm, metals cool, vias light)
const COLORS: Record<string, number> = {
  nwell: 0x5b6b3a, diff: 0x3f9e5a, tap: 0x2f7d47, poly: 0xd2453c, licon: 0x9aa3a8, li1: 0xb9773a, mcon: 0xd8dcdf,
  met1: 0x3b7fd6, via: 0xe2e6e8, met2: 0xc04fc4, via2: 0xe2e6e8, met3: 0x24a8a0, via3: 0xe2e6e8, met4: 0xd9a52b,
  via4: 0xe2e6e8, met5: 0x8a63d2,
};

export function Layout3D({ runId, onClose }: { runId: string; onClose: () => void }) {
  const host = useRef<HTMLDivElement>(null);
  const [geo, setGeo] = useState<Geometry | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [visible, setVisible] = useState<Record<string, boolean>>({});
  const [zScale, setZScale] = useState(6);
  const api = useRef<{ setVisible: (n: string, v: boolean) => void; setZ: (z: number) => void; view: (v: string) => void } | null>(null);

  useEffect(() => {
    getJSON<Geometry>(`/runs/${runId}/layout3d`, 120000).then((g) => {
      setGeo(g);
      setVisible(Object.fromEntries(g.layers.map((l) => [l.name, l.name !== "nwell"])));
    }).catch((e: Error) => setErr(e.message));
  }, [runId]);

  useEffect(() => {
    if (!geo || !host.current) return;
    let disposed = false;
    let cleanup = () => {};
    (async () => {
      const THREE = await import("three");
      const { OrbitControls } = await import("three/examples/jsm/controls/OrbitControls.js");
      if (disposed || !host.current) return;
      const el = host.current;
      const w = el.clientWidth, h = el.clientHeight;
      let renderer: InstanceType<typeof THREE.WebGLRenderer>;
      try {
        renderer = new THREE.WebGLRenderer({ antialias: true });
      } catch {
        setErr("This browser cannot open a WebGL view.");
        return;
      }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(w, h);
      el.appendChild(renderer.domElement);
      const dark = getComputedStyle(document.documentElement).colorScheme.includes("dark") ||
        document.documentElement.getAttribute("data-theme") === "dark";
      const scene = new THREE.Scene();
      scene.background = new THREE.Color(dark ? 0x0d1315 : 0xf2f5f4);
      const [x1, y1, x2, y2] = geo.bbox_um;
      const cx = (x1 + x2) / 2, cy = (y1 + y2) / 2, span = Math.max(x2 - x1, y2 - y1);
      const camera = new THREE.PerspectiveCamera(40, w / h, span / 1000, span * 20);
      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      scene.add(new THREE.AmbientLight(0xffffff, 0.75));
      const sun = new THREE.DirectionalLight(0xffffff, 1.1);
      sun.position.set(span, -span, span * 1.5);
      scene.add(sun);
      // die outline on the substrate plane
      const outline = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.PlaneGeometry(x2 - x1, y2 - y1)),
        new THREE.LineBasicMaterial({ color: dark ? 0x5c6f6c : 0x8a9997 }));
      outline.position.set(cx, cy, 0);
      scene.add(outline);
      const unit = new THREE.BoxGeometry(1, 1, 1);
      const meshes: Record<string, { mesh: InstanceType<typeof THREE.InstancedMesh>; layer: Layer }> = {};
      const m4 = new THREE.Matrix4();
      const place = (z: number) => {
        for (const { mesh, layer } of Object.values(meshes)) {
          layer.boxes.forEach((b, i) => {
            const bw = Math.max(b[2] - b[0], 0.001), bh = Math.max(b[3] - b[1], 0.001);
            m4.makeScale(bw, bh, layer.t_um * z);
            m4.setPosition((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, (layer.z_um + layer.t_um / 2) * z);
            mesh.setMatrixAt(i, m4);
          });
          mesh.instanceMatrix.needsUpdate = true;
          mesh.computeBoundingSphere();
        }
      };
      for (const layer of geo.layers) {
        if (!layer.boxes.length) continue;
        const isVia = /^(licon|mcon|via\d?)$/.test(layer.name);
        const mat = new THREE.MeshStandardMaterial({ color: COLORS[layer.name] ?? 0x999999, roughness: 0.55, metalness: isVia ? 0.1 : 0.35,
          transparent: layer.name === "nwell", opacity: layer.name === "nwell" ? 0.35 : 1 });
        const mesh = new THREE.InstancedMesh(unit, mat, layer.boxes.length);
        meshes[layer.name] = { mesh, layer };
        scene.add(mesh);
      }
      place(zScale);
      const view = (v: string) => {
        const d = span * 1.25;
        if (v === "top") camera.position.set(cx, cy, d * 1.4);
        else if (v === "side") camera.position.set(cx, cy - d * 1.4, d * 0.15);
        else camera.position.set(cx + d * 0.6, cy - d, d * 0.9);
        camera.up.set(0, 0, 1);
        controls.target.set(cx, cy, 0);
        controls.update();
      };
      view("iso");
      for (const [n, v] of Object.entries(visible)) if (meshes[n]) meshes[n].mesh.visible = v;
      api.current = {
        setVisible: (n, v) => { if (meshes[n]) meshes[n].mesh.visible = v; },
        setZ: (z) => place(z),
        view,
      };
      let raf = 0;
      const loop = () => { controls.update(); renderer.render(scene, camera); raf = requestAnimationFrame(loop); };
      loop();
      const ro = new ResizeObserver(() => {
        const W = el.clientWidth, H = el.clientHeight;
        renderer.setSize(W, H); camera.aspect = W / H; camera.updateProjectionMatrix();
      });
      ro.observe(el);
      cleanup = () => {
        cancelAnimationFrame(raf); ro.disconnect(); controls.dispose();
        Object.values(meshes).forEach(({ mesh }) => { (mesh.material as { dispose: () => void }).dispose(); mesh.dispose(); });
        unit.dispose(); renderer.dispose(); renderer.domElement.remove();
      };
    })();
    return () => { disposed = true; cleanup(); api.current = null; };
    // the scene is built once per geometry; toggles and the z scale go through api.current
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geo]);

  const total = geo?.layers.reduce((a, l) => a + l.count, 0) ?? 0;
  return (
    <section className="card pj-3d" aria-label="3D layout view">
      <div className="pj-3d-bar">
        <b className="display">3D layout{geo ? ` · ${geo.top}` : ""}</b>
        <span className="mono muted pj-small">{geo ? `${(geo.bbox_um[2] - geo.bbox_um[0]).toFixed(1)} × ${(geo.bbox_um[3] - geo.bbox_um[1]).toFixed(1)} µm · ${total.toLocaleString()} shapes` : "loading the GDSII…"}</span>
        <span className="pj-3d-actions">
          {(["iso", "top", "side"] as const).map((v) => <button key={v} type="button" className="btn" onClick={() => api.current?.view(v)}>{v}</button>)}
          <label className="mono pj-small">height ×{zScale}
            <input type="range" min={1} max={20} value={zScale} onChange={(e) => { const z = Number(e.target.value); setZScale(z); api.current?.setZ(z); }} />
          </label>
          <button type="button" className="btn" onClick={onClose}>Close</button>
        </span>
      </div>
      {err && <p className="pj-err" style={{ padding: "0 12px" }}>3D view unavailable: {err}</p>}
      <div className="pj-3d-body">
        <div ref={host} className="pj-3d-canvas" />
        {geo && (
          <ul className="pj-3d-layers">
            {[...geo.layers].reverse().map((l) => (
              <li key={l.name}>
                <label>
                  <input type="checkbox" checked={!!visible[l.name]} onChange={(e) => {
                    setVisible((p) => ({ ...p, [l.name]: e.target.checked })); api.current?.setVisible(l.name, e.target.checked);
                  }} />
                  <i style={{ background: `#${(COLORS[l.name] ?? 0x999999).toString(16).padStart(6, "0")}` }} />
                  <span>{l.name}</span>
                  <em className="mono">{l.count.toLocaleString()}{l.truncated ? "+" : ""}</em>
                </label>
              </li>
            ))}
          </ul>
        )}
      </div>
      <p className="mono muted pj-small" style={{ padding: "0 12px 10px", margin: 0 }}>
        Drag to rotate · scroll to zoom · right-drag to pan. Layer heights and thicknesses from the SKY130 PDK stack; vertical scale exaggerated ×{zScale}.
      </p>
    </section>
  );
}
