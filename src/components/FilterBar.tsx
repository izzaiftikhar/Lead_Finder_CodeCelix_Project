"use client";

import type { Filters } from "@/lib/types";

type Props = {
  filters: Filters;
  count: number;
  onChange: (f: Filters) => void;
  onExport: () => void;
};

export default function FilterBar({ filters, count, onChange, onExport }: Props) {
  return (
    <div className="filters">
      <label>
        <input
          type="checkbox"
          checked={filters.bestOnly}
          onChange={(e) => onChange({ ...filters, bestOnly: e.target.checked })}
        />{" "}
        Best leads (website, no chatbot)
      </label>
      <label>
        <input
          type="checkbox"
          checked={filters.whatsappOnly}
          onChange={(e) => onChange({ ...filters, whatsappOnly: e.target.checked })}
        />{" "}
        Uses WhatsApp
      </label>
      <select
        value={filters.sort}
        onChange={(e) => onChange({ ...filters, sort: e.target.value as Filters["sort"] })}
        aria-label="Sort by"
      >
        <option value="score">Sort: score</option>
        <option value="name">Sort: name</option>
      </select>
      <span className="muted">{count} leads</span>
      <button type="button" className="secondary" onClick={onExport} disabled={count === 0}>
        Export CSV
      </button>
    </div>
  );
}
