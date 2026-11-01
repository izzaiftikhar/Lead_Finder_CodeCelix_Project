"use client";
import { useEffect, useMemo, useState } from "react";
import type { Lead } from "@/lib/types";
import { saveLead, sendFeedback, unsaveLead } from "@/lib/api";
import { Badge, ChatbotBadge, Empty, HotBadge, Score, WaBadges, fmtDate } from "./ui";

const FEEDBACK: [string, string][] = [["CORRECT", "Correct"], ["WRONG_WHATSAPP", "Wrong WhatsApp"], ["WRONG_CHATBOT", "Wrong chatbot status"], ["NOT_RELEVANT", "Not relevant"]];

function Drawer({ lead, onClose, onChange }: { lead: Lead; onClose: () => void; onChange: (l: Lead) => void }) {
  const [err, setErr] = useState("");
  useEffect(() => { const k = (e: KeyboardEvent) => e.key === "Escape" && onClose(); window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k); }, [onClose]);
  const s = lead.signals;
  async function fb(v: string) { try { await sendFeedback(lead.id, v); onChange({ ...lead, feedback: v }); } catch (e) { setErr(e instanceof Error ? e.message : "Failed"); } }
  async function toggle() { try { await (lead.saved ? unsaveLead : saveLead)(lead.id); onChange({ ...lead, saved: !lead.saved }); } catch (e) { setErr(e instanceof Error ? e.message : "Failed"); } }
  return (
    <div className="overlay" onClick={onClose}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-label={lead.business_name} onClick={(e) => e.stopPropagation()}>
        <button className="btn ghost close" onClick={onClose} aria-label="Close">✕</button>
        <h2>{lead.business_name}</h2>
        <div className="badges">{lead.hot_lead && <HotBadge />}<WaBadges l={lead} /><ChatbotBadge l={lead} />{lead.is_demo && <Badge>Demo data</Badge>}</div>
        <p className="meta">{[lead.city, lead.country, lead.niche].filter(Boolean).join(" · ")}{lead.address ? ` — ${lead.address}` : ""}</p>
        <dl>
          <dt>WhatsApp</dt><dd>{lead.whatsapp.number} ({lead.whatsapp.status}{lead.whatsapp.type ? `, ${lead.whatsapp.type}` : ""})</dd>
          <dt>Website</dt><dd>{lead.website.url ?? "No website"}</dd>
          <dt>Phone / email</dt><dd>{lead.phone ?? "—"} / {lead.email ?? "—"}</dd>
          <dt>Chatbot</dt><dd>{lead.chatbot.value}{lead.chatbot.vendor ? ` — ${lead.chatbot.vendor}` : ""}{lead.chatbot.kind ? ` (${lead.chatbot.kind})` : ""}</dd>
          <dt>Confidence</dt><dd><Score n={lead.confidence} /></dd>
          <dt>Checked</dt><dd>{fmtDate(lead.checked_at)} · {lead.inspection_status}</dd>
        </dl>
        <h3>Evidence</h3>
        {s.whatsapp_evidence && <div className="ev"><h4>WhatsApp number source ({s.whatsapp_evidence.rule})</h4><p className="meta">Found on: {s.whatsapp_evidence.source_url}</p><p><code>{s.whatsapp_evidence.matched}</code></p></div>}
        {s.wa_type_evidence && <div className="ev"><h4>WhatsApp type</h4><p>{s.wa_type_evidence}</p></div>}
        {s.chatbot_evidence && <div className="ev"><h4>Chatbot signature</h4><p><code>{s.chatbot_evidence}</code></p></div>}
        {lead.chatbot.value === "NO" && <p className="meta">“No chatbot” means no known signature was found in the static HTML of up to 5 pages. Widgets injected only by late JavaScript can be missed.</p>}
        {s.pages && s.pages.length > 0 && <div className="ev"><h4>Pages checked</h4>{s.pages.map((p) => <p key={p.url} className="meta">{p.status} — {p.url}</p>)}</div>}
        {s.notes && s.notes.length > 0 && <div className="ev"><h4>Notes</h4>{s.notes.map((n) => <p key={n} className="meta">{n}</p>)}</div>}
        {lead.maps_url && <p className="meta"><a href={lead.maps_url} target="_blank" rel="noopener noreferrer">Google Maps ↗</a></p>}
        <h3>Is this correct?</h3>
        <div className="badges">{FEEDBACK.map(([v, label]) => <button key={v} className={`btn ${lead.feedback === v ? "solid" : "ghost"}`} onClick={() => fb(v)}>{label}</button>)}</div>
        <p><button className="btn ghost" onClick={toggle}>{lead.saved ? "★ Saved — remove" : "☆ Save lead"}</button></p>
        {err && <p className="err" role="alert">{err}</p>}
      </aside>
    </div>
  );
}

export default function LeadTable({ leads, onChange }: { leads: Lead[]; onChange: (l: Lead) => void }) {
  const [q, setQ] = useState(""); const [hot, setHot] = useState(false); const [cb, setCb] = useState(""); const [wt, setWt] = useState("");
  const [sort, setSort] = useState("hot"); const [open, setOpen] = useState<string | null>(null);
  const view = useMemo(() => leads.filter((l) => (!hot || l.hot_lead) && (!cb || l.chatbot.value === cb) && (!wt || l.whatsapp.type === wt) && (!q || l.business_name.toLowerCase().includes(q.toLowerCase())))
    .sort((a, b) => sort === "name" ? a.business_name.localeCompare(b.business_name) : sort === "confidence" ? (b.confidence ?? 0) - (a.confidence ?? 0) : Number(b.hot_lead) - Number(a.hot_lead) || (b.confidence ?? 0) - (a.confidence ?? 0)), [leads, q, hot, cb, wt, sort]);
  const cur = leads.find((l) => l.id === open) ?? null;
  return (
    <section>
      <div className="toolbar">
        <input aria-label="Filter by name" placeholder="Filter by name…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select aria-label="Chatbot" value={cb} onChange={(e) => setCb(e.target.value)}><option value="">Any chatbot status</option><option value="NO">No chatbot found</option><option value="YES">Chatbot detected</option><option value="UNKNOWN">Unknown</option></select>
        <select aria-label="WhatsApp type" value={wt} onChange={(e) => setWt(e.target.value)}><option value="">Any WhatsApp type</option><option value="MANUAL">Manual</option><option value="AUTOMATED">Automated</option><option value="UNKNOWN">Unknown</option></select>
        <select aria-label="Sort" value={sort} onChange={(e) => setSort(e.target.value)}><option value="hot">Sort: hot first</option><option value="confidence">Sort: confidence</option><option value="name">Sort: name</option></select>
        <label className="chk"><input type="checkbox" checked={hot} onChange={(e) => setHot(e.target.checked)} /> Hot only</label>
        <b className="counter">{view.length} / {leads.length}</b>
      </div>
      {view.length === 0 ? <Empty title={leads.length ? "No leads match these filters" : "No leads yet"} /> : (
        <div className="card tablewrap"><table>
          <thead><tr><th>Business</th><th>City</th><th>Website</th><th>WhatsApp</th><th>Chatbot</th><th>Confidence</th></tr></thead>
          <tbody>{view.map((l) => (
            <tr key={l.id} className={`row ${l.hot_lead ? "is-hot" : ""}`} tabIndex={0} onClick={() => setOpen(l.id)} onKeyDown={(e) => e.key === "Enter" && setOpen(l.id)}>
              <td><b>{l.business_name}</b> {l.hot_lead && <HotBadge />} {l.saved && "★"}</td>
              <td>{l.city}</td>
              <td>{l.website.has_website ? "Yes" : <span className="meta">No website</span>}</td>
              <td><div>{l.whatsapp.number}</div><div className="badges"><WaBadges l={l} /></div></td>
              <td><ChatbotBadge l={l} /></td>
              <td><Score n={l.confidence} /></td>
            </tr>))}</tbody>
        </table></div>
      )}
      {cur && <Drawer lead={cur} onClose={() => setOpen(null)} onChange={onChange} />}
    </section>
  );
}
