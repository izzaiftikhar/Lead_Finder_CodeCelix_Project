import type { Lead, SearchParams } from "./types";

export async function searchLeads(params: SearchParams): Promise<Lead[]> {
  const res = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data.leads as Lead[];
}

export async function getIndustries(): Promise<string[]> {
  try {
    const res = await fetch("/api/industries");
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}
