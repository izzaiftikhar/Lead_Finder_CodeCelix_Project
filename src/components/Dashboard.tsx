"use client";
import { useEffect, useState } from "react";
import { logout, me } from "@/lib/api";
import type { Me, User } from "@/lib/types";
import AuthForm from "./AuthForm";
import JobView from "./JobView";
import NewSearch from "./NewSearch";
import { Account, Admin, Jobs, Overview, Saved } from "./Screens";
import { Skeleton } from "./ui";

type View = "overview" | "new" | "jobs" | "saved" | "admin" | "settings" | "job";
const NAV: [View, string, string][] = [["overview", "Overview", "▦"], ["new", "New Search", "⌕"], ["jobs", "Job History", "↺"], ["saved", "Saved Leads", "★"], ["admin", "Admin", "⚒"], ["settings", "Settings", "⚙"]];

export default function Dashboard() {
  const [session, setSession] = useState<Me | null | undefined>(undefined);
  const [view, setView] = useState<View>("overview");
  const [jobId, setJobId] = useState("");
  const [menu, setMenu] = useState(false);
  useEffect(() => { me().then(setSession).catch(() => setSession(null)); }, []);

  if (session === undefined) return <div className="authwrap"><Skeleton rows={3} /></div>;
  if (session === null) return <AuthForm onAuthed={(u: User) => me().then(setSession).catch(() => setSession({ user: u, live_available: false }))} />;

  const open = (id: string) => { setJobId(id); setView("job"); setMenu(false); };
  const go = (v: View) => { setView(v); setMenu(false); };
  const nav = NAV.filter(([id]) => id !== "admin" || session.user.role === "admin");
  return (
    <div className="shell">
      <header className="topbar"><button className="btn ghost" aria-label="Menu" onClick={() => setMenu(!menu)}>☰</button><b>CodeCelix <em>Lead Finder</em></b></header>
      <nav className={`side ${menu ? "open" : ""}`} aria-label="Main">
        <div className="brand">Code<span>Celix</span><small>Lead Finder</small></div>
        {nav.map(([id, label, icon]) => <button key={id} className={view === id ? "active" : ""} aria-current={view === id ? "page" : undefined} onClick={() => go(id)}><span aria-hidden>{icon}</span>{label}</button>)}
        <div className="spacer" />
        <p className="who">{session.user.email}</p>
        <button onClick={async () => { await logout().catch(() => null); setSession(null); }}><span aria-hidden>⎋</span>Sign out</button>
      </nav>
      <main className="content" key={view + jobId}>
        {view === "overview" && <Overview onOpen={open} />}
        {view === "new" && <NewSearch onStarted={open} />}
        {view === "jobs" && <Jobs onOpen={open} />}
        {view === "job" && <JobView id={jobId} onOpen={open} />}
        {view === "saved" && <Saved />}
        {view === "admin" && <Admin />}
        {view === "settings" && <Account email={session.user.email} role={session.user.role} live={session.live_available} />}
      </main>
    </div>
  );
}
