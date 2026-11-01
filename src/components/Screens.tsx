"use client";
import { useCallback, useEffect, useState } from "react";
import * as api from "@/lib/api";
import { COUNTRY, NICHE } from "@/lib/types";
import type { AdminConfig, Cost, Job, Lead, Stats } from "@/lib/types";
import LeadTable from "./LeadTable";
import { Empty, ErrorBox, Skeleton, StatusBadge, fmtDate } from "./ui";

function useLoad<T>(fn: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  const load = useCallback(() => { setLoading(true); setError(""); fn().then(setData).catch((e: Error) => setError(e.message)).finally(() => setLoading(false)); // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(load, [load]);
  return { data, setData, error, loading, load };
}

export function JobsTable({ items, onOpen, onRerun }: { items: Job[]; onOpen: (id: string) => void; onRerun?: (id: string) => void }) {
  return (
    <div className="card tablewrap"><table>
      <thead><tr><th>Created</th><th>Search</th><th>Cities</th><th>Result</th><th>Status</th><th /></tr></thead>
      <tbody>{items.map((j) => (
        <tr key={j.id}><td>{fmtDate(j.created_at)}</td><td>{NICHE[j.niche] ?? j.niche} · {COUNTRY[j.country] ?? j.country}{j.mode === "demo" ? " (demo)" : ""}</td>
          <td>{j.city_ids.length}</td><td>{j.accepted_count}/{j.lead_count}</td><td><StatusBadge s={j.status} /></td>
          <td className="actions"><button className="btn ghost" onClick={() => onOpen(j.id)}>Open</button>{onRerun && <button className="btn ghost" onClick={() => onRerun(j.id)}>Re-run</button>}</td></tr>))}</tbody>
    </table></div>
  );
}

export function Overview({ onOpen }: { onOpen: (id: string) => void }) {
  const { data: s, error, loading, load } = useLoad<Stats>(api.stats);
  if (loading) return <Skeleton />;
  if (error || !s) return <ErrorBox msg={error} onRetry={load} />;
  const cards: [string, number, string][] = [
    ["Leads found", s.total_leads, "all your searches"], ["Hot leads", s.hot_leads, "WhatsApp confirmed + manual + no chatbot found"],
    ["WhatsApp confirmed", s.whatsapp_confirmed, `${s.whatsapp_manual} manual · ${s.whatsapp_automated} automated`],
    ["Chatbot detected", s.chatbot_yes, "already automated"], ["Saved", s.saved, "your shortlist"], ["Searches", s.jobs, `${s.jobs_active} running`],
  ];
  return (
    <div>
      <h1>Overview</h1>
      <div className="stats">{cards.map(([t, n, sub]) => <div className="card stat" key={t}><span>{t}</span><b>{n}</b><small>{sub}</small></div>)}</div>
      <h2>Recent searches</h2>
      {s.recent_jobs.length === 0 ? <Empty title="No searches yet" hint="Start one from New Search." /> : <JobsTable items={s.recent_jobs} onOpen={onOpen} />}
      <p className="meta">All figures are counted from your stored leads and jobs.</p>
    </div>
  );
}

export function Jobs({ onOpen }: { onOpen: (id: string) => void }) {
  const { data, error, loading, load } = useLoad(api.jobs);
  const [err, setErr] = useState("");
  if (loading) return <Skeleton />;
  if (error || !data) return <ErrorBox msg={error} onRetry={load} />;
  return (
    <div><h1>Job history</h1>{err && <p className="err" role="alert">{err}</p>}
      {data.items.length === 0 ? <Empty title="No jobs yet" /> :
        <JobsTable items={data.items} onOpen={onOpen} onRerun={async (id) => { try { onOpen((await api.rerunJob(id)).id); } catch (e) { setErr(e instanceof Error ? e.message : "Failed"); } }} />}
    </div>
  );
}

export function Saved() {
  const { data, setData, error, loading, load } = useLoad(api.saved);
  if (loading) return <Skeleton />;
  if (error || !data) return <ErrorBox msg={error} onRetry={load} />;
  const upd = (l: Lead) => setData({ items: l.saved ? data.items.map((x) => (x.id === l.id ? l : x)) : data.items.filter((x) => x.id !== l.id) });
  return <div><h1>Saved leads</h1>{data.items.length === 0 ? <Empty title="Nothing saved yet" hint="Open a lead and press Save." /> : <LeadTable leads={data.items} onChange={upd} />}</div>;
}

export function Admin() {
  const { data: c, error, loading, load } = useLoad<AdminConfig>(api.adminConfig);
  const cost = useLoad<Cost>(api.adminCost);
  const [msg, setMsg] = useState(""); const [kw, setKw] = useState({ niche: "REAL_ESTATE", region: "ANY", lang: "en", keyword: "" });
  const [sig, setSig] = useState({ vendor: "", kind: "LIVE_CHAT", scope: "chatbot", pattern: "" }); const [sup, setSup] = useState("");
  async function run(fn: () => Promise<unknown>, ok = "Saved") { try { await fn(); setMsg(ok); load(); } catch (e) { setMsg(e instanceof Error ? e.message : "Failed"); } }
  if (loading) return <Skeleton />;
  if (error || !c) return <ErrorBox msg={error} onRetry={load} />;
  return (
    <div>
      <h1>Admin</h1>{msg && <p className="status" role="status">{msg}</p>}
      <h2>Country × niche matrix</h2>
      <div className="card tablewrap"><table><thead><tr><th>Country</th>{Object.keys(NICHE).map((n) => <th key={n}>{NICHE[n]}</th>)}</tr></thead>
        <tbody>{Object.keys(COUNTRY).map((cc) => <tr key={cc}><td>{COUNTRY[cc]}</td>{Object.keys(NICHE).map((n) => {
          const row = c.country_niches.find((x) => x.country === cc && x.niche === n);
          return <td key={n}><input type="checkbox" aria-label={`${COUNTRY[cc]} ${NICHE[n]}`} checked={!!row?.enabled} onChange={(e) => run(() => api.adminPut("country-niches", { country: cc, niche: n, enabled: e.target.checked }))} /></td>;
        })}</tr>)}</tbody></table></div>
      <h2>Limits</h2>
      <div className="card form">{c.limits.map((l) => <label key={l.key}>{l.key}<input defaultValue={l.value} onBlur={(e) => e.target.value !== l.value && run(() => api.adminPut("limits", { key: l.key, value: Number(e.target.value) }))} /></label>)}</div>
      <h2>Niche keywords ({c.keywords.length})</h2>
      <div className="card stack"><div className="toolbar tight">
        <select value={kw.niche} onChange={(e) => setKw({ ...kw, niche: e.target.value })}>{Object.keys(NICHE).map((n) => <option key={n} value={n}>{NICHE[n]}</option>)}</select>
        <select value={kw.region} onChange={(e) => setKw({ ...kw, region: e.target.value })}><option>ANY</option><option>GULF</option></select>
        <input placeholder="lang" value={kw.lang} onChange={(e) => setKw({ ...kw, lang: e.target.value })} style={{ width: 70 }} />
        <input placeholder="keyword" value={kw.keyword} onChange={(e) => setKw({ ...kw, keyword: e.target.value })} />
        <button className="btn solid" disabled={!kw.keyword} onClick={() => run(() => api.adminPut("niche-keywords", kw))}>Add</button></div>
        <div className="chips">{c.keywords.map((k) => <span key={k.id} className="chip">{NICHE[k.niche]} · {k.region} · {k.keyword} <button aria-label="Delete" onClick={() => run(() => api.adminDelete(`niche-keywords/${k.id}`), "Deleted")}>×</button></span>)}</div></div>
      <h2>Chatbot / WhatsApp-automation signatures ({c.signatures.length})</h2>
      <div className="card stack"><div className="toolbar tight">
        <input placeholder="vendor" value={sig.vendor} onChange={(e) => setSig({ ...sig, vendor: e.target.value })} />
        <select value={sig.kind} onChange={(e) => setSig({ ...sig, kind: e.target.value })}><option>LIVE_CHAT</option><option>AI_BOT</option><option>UNKNOWN_WIDGET</option></select>
        <select value={sig.scope} onChange={(e) => setSig({ ...sig, scope: e.target.value })}><option value="chatbot">chatbot</option><option value="whatsapp">whatsapp</option></select>
        <input placeholder="script domain / JS global" value={sig.pattern} onChange={(e) => setSig({ ...sig, pattern: e.target.value })} />
        <button className="btn solid" disabled={!sig.vendor || sig.pattern.length < 3} onClick={() => run(() => api.adminPut("chatbot-signatures", sig))}>Add</button></div>
        <div className="chips">{c.signatures.map((s) => <span key={s.id} className={`chip ${s.enabled ? "" : "off"}`}>{s.scope === "whatsapp" ? "WA " : ""}{s.vendor}: {s.pattern}
          <button aria-label="Toggle" onClick={() => run(() => api.adminPut("chatbot-signatures", { ...s, enabled: !s.enabled }))}>{s.enabled ? "⏸" : "▶"}</button>
          <button aria-label="Delete" onClick={() => run(() => api.adminDelete(`chatbot-signatures/${s.id}`), "Deleted")}>×</button></span>)}</div></div>
      <h2>Suppression list ({c.suppressed})</h2>
      <div className="card toolbar tight"><input placeholder="domain or phone number to exclude from all future jobs" value={sup} onChange={(e) => setSup(e.target.value)} />
        <button className="btn solid" disabled={sup.length < 3} onClick={() => run(async () => { await api.adminPost("suppression", { value: sup }); setSup(""); }, "Added")}>Add</button></div>
      <h2>Cost</h2>
      {cost.data ? <div className="card"><p>Total (estimated): <b>${cost.data.total_usd.toFixed(2)}</b></p><p className="meta">{cost.data.note}</p>
        <table><thead><tr><th>Day</th><th>Jobs</th><th>Leads</th><th>Est. cost</th></tr></thead><tbody>{cost.data.by_day.map((d) => <tr key={d.day}><td>{d.day}</td><td>{d.jobs}</td><td>{d.leads ?? 0}</td><td>${(d.cost_usd ?? 0).toFixed(2)}</td></tr>)}</tbody></table></div> : <Skeleton rows={2} />}
    </div>
  );
}

export function Account({ email, role, live }: { email: string; role: string; live: boolean }) {
  const { data, error, loading, load } = useLoad(api.health);
  if (loading) return <Skeleton rows={3} />;
  if (error || !data) return <ErrorBox msg={error} onRetry={load} />;
  return (
    <div><h1>Settings</h1><div className="card"><dl>
      <dt>Signed in as</dt><dd>{email} ({role})</dd><dt>Backend</dt><dd>{data.status}</dd>
      <dt>Database</dt><dd>{data.database}{data.database === "SQLite" ? " — not persistent on most hosts; set DATABASE_URL (PostgreSQL) in production" : ""}</dd>
      <dt>Live discovery</dt><dd>{live ? "Configured (Apify)" : "Not configured — set APIFY_API_TOKEN on the backend"}</dd>
      <dt>Detection</dt><dd>Static HTTP inspection of up to 5 pages per site; WhatsApp type is inferred from public signals (no test messages are sent).</dd>
    </dl></div></div>
  );
}
