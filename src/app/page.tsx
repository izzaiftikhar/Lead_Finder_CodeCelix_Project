"use client";

import { useEffect, useMemo, useState } from "react";
import SearchForm from "@/components/SearchForm";
import ResultsTable from "@/components/ResultsTable";
import { getIndustries, searchLeads } from "@/lib/api";
import { downloadCsv } from "@/lib/csv";
import type { Filters, Lead, SearchParams } from "@/lib/types";

type FilterBarProps = {
  filters: Filters;
  count: number;
  onChange: (filters: Filters) => void;
  onExport: () => void;
};

function FilterBar({ filters, count, onChange, onExport }: FilterBarProps) {
  return (
    <section aria-label="Lead filters">
      <label>
        <input type="checkbox" checked={filters.bestOnly} onChange={(event) => onChange({ ...filters, bestOnly: event.target.checked })} />
        Best leads only
      </label>
      <label>
        <input type="checkbox" checked={filters.whatsappOnly} onChange={(event) => onChange({ ...filters, whatsappOnly: event.target.checked })} />
        WhatsApp only
      </label>
      <label>
        Sort by
        <select value={filters.sort} onChange={(event) => onChange({ ...filters, sort: event.target.value as Filters["sort"] })}>
          <option value="score">Score</option>
          <option value="name">Name</option>
        </select>
      </label>
      <span>{count} leads</span>
      <button type="button" onClick={onExport}>Export CSV</button>
    </section>
  );
}

export default function Home() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [industries, setIndustries] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState<Filters>({ bestOnly: false, whatsappOnly: false, sort: "score" });

  useEffect(() => {
    getIndustries().then(setIndustries);
  }, []);

  async function handleSearch(params: SearchParams) {
    setLoading(true);
    setError("");
    try {
      setLeads(await searchLeads(params));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const visible = useMemo(() => {
    const list = leads.filter(
      (lead) =>
        (!filters.bestOnly || (lead.website && lead.chatbot === "no")) &&
        (!filters.whatsappOnly || lead.whatsapp === "yes")
    );
    return [...list].sort((a, b) =>
      filters.sort === "score" ? b.score - a.score : a.name.localeCompare(b.name)
    );
  }, [leads, filters]);

  return (
    <main>
      <h1>Lead Finder</h1>

      <SearchForm loading={loading} onSearch={handleSearch} />
      
      {loading && <p className="muted">Searching and checking websites. This can take up to a minute.</p>}
      {error && <p className="error">{error}</p>}
      <FilterBar filters={filters} count={visible.length} onChange={setFilters} onExport={() => downloadCsv(visible)} />
      <ResultsTable leads={visible} />
    </main>
  );
}
