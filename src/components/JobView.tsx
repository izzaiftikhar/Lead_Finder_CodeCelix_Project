"use client";
import { useCallback, useEffect, useState } from "react";
import { cancelJob, exportUrl, job as getJob, jobLeads, rerunJob, resumeJob } from "@/lib/api";
import { COUNTRY, NICHE } from "@/lib/types";
import type { Job, Lead } from "@/lib/types";
import LeadTable from "./LeadTable";
import { Badge, ErrorBox, Skeleton, StatusBadge, fmtDate } from "./ui";

const LABEL: Record<string, string> = {
  no_website: "No website", no_whatsapp: "No WhatsApp number", whatsapp_not_confirmed: "WhatsApp not confirmed (confirmed-only is on)",
  filter_chatbot: "Rejected by chatbot filter", filter_manual: "Rejected by manual-WhatsApp filter", duplicate: "Duplicates",
  previously_exported: "Already exported earlier", inspection_failed: "Site blocked / timed out", suppressed: "On suppression list",
};

export default function JobView({ id, onOpen }: { id: string; onOpen: (id: string) => void }) {
  const [j, setJ] = useState<Job | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const active = j?.status === "QUEUED" || j?.status === "RUNNING";

  const load = useCallback(async () => {
    try { const [a, b] = await Promise.all([getJob(id), jobLeads(id)]); setJ(a); setLeads(b.items); setError(""); }
    catch (e) { setError(e instanceof Error ? e.message : "Failed to load job"); }
  }, [id]);
  useEffect(() => { setJ(null); load(); }, [load]);
  useEffect(() => { if (!active) return; const t = setInterval(load, 2500); return () => clearInterval(t); }, [active, load]);

  async function act(fn: () => Promise<unknown>) { setBusy(true); try { await fn(); await load(); } catch (e) { setError(e instanceof Error ? e.message : "Failed"); } finally { setBusy(false); } }

  if (error && !j) return <ErrorBox msg={error} onRetry={load} />;
  if (!j) return <Skeleton rows={4} />;
  const pct = Math.min(100, Math.round((j.accepted_count / j.lead_count) * 100));
  const bd = Object.entries(j.shortfall?.breakdown ?? {}).filter(([, v]) => v > 0);
  return (
    <div>
      <h1>{NICHE[j.niche] ?? j.niche} · {COUNTRY[j.country] ?? j.country} <StatusBadge s={j.status} /> {j.mode === "demo" && <Badge>Demo data</Badge>}</h1>
      <div className="card stack">
        <div className="progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}><i style={{ width: `${pct}%` }} /></div>
        <p><b>{j.accepted_count}</b> of <b>{j.lead_count}</b> leads accepted · {j.candidates_seen} candidates found · {j.inspected_count} inspected · started {fmtDate(j.started_at ?? j.created_at)}</p>
        {active && <p className="status" role="status">Running in the background — you can leave this page and come back.</p>}
        {j.message && !active && <p className={j.status === "FAILED" ? "err" : "status"}>{j.message}</p>}
        {bd.length > 0 && j.status === "PARTIAL" && (<><h3>Why fewer leads?</h3><ul className="plain">{bd.map(([k, v]) => <li key={k}>{LABEL[k] ?? k}: <b>{v}</b></li>)}</ul></>)}
        <div className="badges">
          {active && <button className="btn ghost" disabled={busy} onClick={() => act(() => cancelJob(j.id))}>Cancel</button>}
          {(j.status === "CANCELLED" || j.status === "FAILED" || j.status === "PARTIAL") && <button className="btn ghost" disabled={busy} onClick={() => act(() => resumeJob(j.id))}>Resume</button>}
          <button className="btn ghost" disabled={busy} onClick={() => act(async () => onOpen((await rerunJob(j.id)).id))}>Re-run</button>
          <a className="btn ghost" href={exportUrl(j.id, "csv")}>Export CSV</a>
          <a className="btn ghost" href={exportUrl(j.id, "xlsx")}>Export XLSX</a>
        </div>
        {error && <p className="err" role="alert">{error}</p>}
      </div>
      <div style={{ height: 16 }} />
      <LeadTable leads={leads} onChange={(l) => setLeads((p) => p.map((x) => (x.id === l.id ? l : x)))} />
    </div>
  );
}
