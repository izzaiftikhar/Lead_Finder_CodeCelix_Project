"use client";
import { useEffect, useRef, useState } from "react";
import { cities as getCities, createJob, estimate as getEstimate, markets as getMarkets } from "@/lib/api";
import type { City, Estimate, Filters, Markets } from "@/lib/types";
import CitySelect from "./CitySelect";
import { ErrorBox, Skeleton } from "./ui";

const TOGGLES: [keyof Filters, string][] = [
  ["whatsapp_confirmed_only", "WhatsApp confirmed only"], ["no_chatbot_only", "Only websites without chatbot"],
  ["manual_whatsapp_only", "Only manual WhatsApp"], ["website_required", "Website required"], ["exclude_previously_exported", "Exclude leads I already exported"],
];

export default function NewSearch({ onStarted }: { onStarted: (id: string) => void }) {
  const [mk, setMk] = useState<Markets | null>(null);
  const [error, setError] = useState("");
  const [country, setCountry] = useState("AE");
  const [niche, setNiche] = useState("");
  const [cityList, setCityList] = useState<City[]>([]);
  const [admin1, setAdmin1] = useState<string[]>([]);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const [count, setCount] = useState(50);
  const [mode, setMode] = useState<"live" | "demo">("demo");
  const [filters, setFilters] = useState<Filters>({ whatsapp_confirmed_only: true, no_chatbot_only: false, manual_whatsapp_only: false, website_required: false, exclude_previously_exported: true });
  const [est, setEst] = useState<Estimate | null>(null);
  const [busy, setBusy] = useState(false);
  const key = useRef(crypto.randomUUID());

  useEffect(() => { getMarkets().then((m) => { setMk(m); if (m.live_available) setMode("live"); }).catch((e: Error) => setError(e.message)); }, []);
  const niches = mk?.countries.find((c) => c.code === country)?.niches ?? [];
  useEffect(() => { if (!niches.some((n) => n.code === niche)) setNiche(niches[0]?.code ?? ""); }, [niches, niche]);
  useEffect(() => { setSel(new Set()); getCities(country).then((r) => { setCityList(r.items); setAdmin1(r.admin1.filter(Boolean)); }).catch((e: Error) => setError(e.message)); }, [country]);
  useEffect(() => {
    if (!niche) return;
    const t = setTimeout(() => getEstimate(country, niche, count).then(setEst).catch(() => setEst(null)), 300);
    return () => clearTimeout(t);
  }, [country, niche, count]);

  async function start() {
    setBusy(true); setError("");
    try {
      const all = sel.size > 0 && sel.size === cityList.length;
      const r = await createJob({ country, niche, city_ids: [...sel], all_cities: all, lead_count: count, mode, filters }, key.current);
      key.current = crypto.randomUUID();
      onStarted(r.id);
    } catch (e) { setError(e instanceof Error ? e.message : "Could not start the search"); }
    finally { setBusy(false); }
  }

  if (!mk && !error) return <Skeleton rows={6} />;
  if (!mk) return <ErrorBox msg={error} />;
  const lim = mk.limits;
  return (
    <div>
      <h1>New search</h1>
      <form className="card stack" onSubmit={(e) => { e.preventDefault(); start(); }}>
        <div className="form">
          <label>Country<select value={country} onChange={(e) => setCountry(e.target.value)}>{mk.countries.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}</select></label>
          <label>Niche<select value={niche} onChange={(e) => setNiche(e.target.value)}>{niches.map((n) => <option key={n.code} value={n.code}>{n.name}</option>)}</select></label>
          <label>Leads with WhatsApp ({lim.min > 10 ? lim.min : 10}–{lim.max})
            <input type="number" min={Math.max(lim.min, 10)} max={lim.max} value={count} onChange={(e) => setCount(Math.max(1, Math.min(lim.max, Number(e.target.value) || 1)))} /></label>
          <fieldset className="modes"><legend>Data source</legend>
            <label className="chk"><input type="radio" checked={mode === "live"} disabled={!mk.live_available} onChange={() => setMode("live")} /> Live (Apify)</label>
            <label className="chk"><input type="radio" checked={mode === "demo"} onChange={() => setMode("demo")} /> Demo (fictional)</label>
          </fieldset>
        </div>
        {!mk.live_available && <p className="notice" role="status">Live discovery is not configured: set <code>APIFY_API_TOKEN</code> on the backend. Demo mode generates clearly marked fictional businesses.</p>}
        <div><h3>Cities</h3><CitySelect cities={cityList} admin1={admin1} selected={sel} onChange={setSel} /></div>
        <div className="toggles">{TOGGLES.map(([k, label]) => (
          <label key={k} className="chk"><input type="checkbox" checked={filters[k]} onChange={(e) => setFilters({ ...filters, [k]: e.target.checked })} /> {label}</label>))}</div>
        {est && <div className="estimate" role="status">Estimated time: roughly <b>{est.minutes_p50}–{est.minutes_p90} minutes</b> (expected WhatsApp yield ≈ {Math.round(est.expected_yield * 100)}%, from {est.basis}). You can leave the page; the job keeps running.</div>}
        {error && <p className="err" role="alert">{error}</p>}
        <div><button className="btn solid" disabled={busy || sel.size === 0 || !niche}>{busy ? "Starting…" : `Start search (${sel.size} ${sel.size === 1 ? "city" : "cities"})`}</button></div>
      </form>
    </div>
  );
}
