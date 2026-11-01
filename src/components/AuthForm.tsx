"use client";
import { useState } from "react";
import { login, register } from "@/lib/api";
import type { User } from "@/lib/types";

export default function AuthForm({ onAuthed }: { onAuthed: (u: User) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit() {
    setBusy(true); setErr("");
    try { onAuthed((await (mode === "login" ? login : register)(email, password)).user); }
    catch (e) { setErr(e instanceof Error ? e.message : "Failed"); }
    finally { setBusy(false); }
  }
  return (
    <div className="authwrap">
      <form className="card authcard" onSubmit={(e) => { e.preventDefault(); submit(); }}>
        <div className="brand dark">Code<span>Celix</span><small>Lead Finder</small></div>
        <h1>{mode === "login" ? "Sign in" : "Create account"}</h1>
        <label>Email<input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Password<input type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} required minLength={mode === "register" ? 10 : 1} value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {mode === "register" && <p className="meta">At least 10 characters. The first account created becomes the admin.</p>}
        {err && <p className="err" role="alert">{err}</p>}
        <button className="btn solid" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button>
        <button type="button" className="btn ghost" onClick={() => { setMode(mode === "login" ? "register" : "login"); setErr(""); }}>
          {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
        </button>
      </form>
    </div>
  );
}
