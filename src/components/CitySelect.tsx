"use client";
import { useMemo, useState } from "react";
import type { City } from "@/lib/types";

export default function CitySelect({ cities, admin1, selected, onChange }: { cities: City[]; admin1: string[]; selected: Set<number>; onChange: (s: Set<number>) => void }) {
  const [q, setQ] = useState("");
  const [region, setRegion] = useState("");
  const visible = useMemo(() => cities.filter((c) => (!region || c.admin1 === region) && c.name.toLowerCase().includes(q.trim().toLowerCase())), [cities, q, region]);
  const groups = useMemo(() => {
    const m = new Map<string, City[]>();
    for (const c of visible) { const k = c.admin1 ?? "Other"; m.set(k, [...(m.get(k) ?? []), c]); }
    return [...m.entries()];
  }, [visible]);
  const toggle = (id: number) => { const n = new Set(selected); if (n.has(id)) n.delete(id); else n.add(id); onChange(n); };
  return (
    <div className="citysel">
      <div className="toolbar tight">
        <input aria-label="Search cities" placeholder="Search cities…" value={q} onChange={(e) => setQ(e.target.value)} />
        {admin1.length > 1 && (
          <select aria-label="Filter by state or region" value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="">All regions</option>{admin1.map((a) => <option key={a}>{a}</option>)}
          </select>
        )}
        <button type="button" className="btn ghost" onClick={() => onChange(new Set(cities.map((c) => c.id)))}>Select all cities</button>
        <button type="button" className="btn ghost" onClick={() => onChange(new Set())}>Clear</button>
        <b className="counter">{selected.size} selected</b>
      </div>
      {selected.size > 100 && <p className="notice">Selecting 100+ cities makes the job long and costly.</p>}
      <div className="citybox">
        {groups.length === 0 && <p className="meta">No cities match.</p>}
        {groups.map(([g, list]) => (
          <fieldset key={g}><legend>{g}</legend>
            {list.map((c) => (
              <label key={c.id} className="chk"><input type="checkbox" checked={selected.has(c.id)} onChange={() => toggle(c.id)} /> {c.name}</label>
            ))}
          </fieldset>
        ))}
      </div>
    </div>
  );
}
