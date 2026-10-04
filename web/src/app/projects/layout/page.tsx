"use client";
// Full-screen 3D view of one run's GDSII: /projects/layout?run=<run_id>
import dynamic from "next/dynamic";
import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

const Layout3D = dynamic(() => import("@/components/Layout3D").then((m) => m.Layout3D), { ssr: false });

function View() {
  const run = useSearchParams().get("run");
  return (
    <div className="pj-wrap">
      <div className="pj-top">
        <span className="display pj-brand">GDSII 3D view</span>
        <Link href="/projects" className="btn">Projects</Link>
      </div>
      {run ? <Layout3D runId={run} onClose={() => window.history.back()} />
        : <p className="muted">Add ?run=&lt;run id&gt; to the address, or open a design that has a GDSII on the Projects page.</p>}
    </div>
  );
}

export default function Page() {
  return <Suspense fallback={<p className="muted">Loading…</p>}><View /></Suspense>;
}
