import type { ReactNode } from "react";
import type { JobStatus, Lead } from "@/lib/types";

export function Badge({ tone = "mute", children, title }: { tone?: "ok" | "bad" | "warn" | "info" | "mute" | "hot"; children: ReactNode; title?: string }) {
  return <span className={`badge ${tone}`} title={title}>{children}</span>;
}
export const HotBadge = () => <Badge tone="hot">★ Hot lead</Badge>;

export function WaBadges({ l }: { l: Lead }) {
  const s = l.whatsapp.status, t = l.whatsapp.type;
  return (
    <>
      <Badge tone={s === "CONFIRMED" ? "ok" : "info"} title="CONFIRMED = published by the business itself">{s === "CONFIRMED" ? "WA confirmed" : "WA probable"}</Badge>
      {t && t !== "UNKNOWN" && <Badge tone={t === "MANUAL" ? "ok" : "warn"} title="Inferred from public signals, not a live test">{t === "MANUAL" ? "Manual" : "Automated"}</Badge>}
    </>
  );
}
export function ChatbotBadge({ l }: { l: Lead }) {
  const v = l.chatbot.value;
  if (v === "YES") return <Badge tone="bad">Chatbot: {l.chatbot.vendor ?? "widget"}</Badge>;
  if (v === "NO") return <Badge tone="ok" title="No signature found in the static page HTML">Chatbot: none found</Badge>;
  return <Badge tone="warn" title="Site could not be fully inspected">Chatbot: unknown</Badge>;
}
const JS: Record<JobStatus, "ok" | "info" | "warn" | "bad" | "mute"> = { COMPLETED: "ok", RUNNING: "info", QUEUED: "mute", PARTIAL: "warn", FAILED: "bad", CANCELLED: "mute" };
export const StatusBadge = ({ s }: { s: JobStatus }) => <Badge tone={JS[s]}>{s}</Badge>;

export function Score({ n }: { n: number | null }) {
  const v = Math.round((n ?? 0) * 100);
  return <span className="score" title={`Detection confidence ${v}%`}><span className="score-bar"><i style={{ width: `${v}%` }} /></span><b>{(n ?? 0).toFixed(2)}</b></span>;
}
export function Skeleton({ rows = 5 }: { rows?: number }) {
  return <div className="card" aria-busy="true" aria-label="Loading">{Array.from({ length: rows }, (_, i) => <div key={i} className="skel" />)}</div>;
}
export const Empty = ({ title, hint }: { title: string; hint?: string }) => <div className="card empty"><h3>{title}</h3>{hint && <p>{hint}</p>}</div>;
export function ErrorBox({ msg, onRetry }: { msg: string; onRetry?: () => void }) {
  return <div className="card errbox" role="alert"><strong>Something went wrong</strong><p>{msg}</p>{onRetry && <button className="btn ghost" onClick={onRetry}>Retry</button>}</div>;
}
export const fmtDate = (s: string | null) => (s ? new Date(s).toLocaleString() : "—");
