import type {
  ChatbotStatus,
  EvidenceSource,
  LeadEvidence,
  WhatsappStatus,
} from "./types";

// Single source of truth for API paths used by the evidence UI.
// (Pagination such as GET /api/leads?page=1 belongs to the results table, not here.)
export const API = {
  leadEvidence: (leadId: string) =>
    `/api/leads/${encodeURIComponent(leadId)}/evidence`,
} as const;

const WHATSAPP: readonly WhatsappStatus[] = ["CONFIRMED", "PROBABLE", "NO", "UNKNOWN"];
const CHATBOT: readonly ChatbotStatus[] = ["YES", "NO", "UNKNOWN"];

const str = (v: unknown): string | null =>
  typeof v === "string" && v.trim() !== "" ? v : null;

/**
 * Turns whatever the backend returned into a safe LeadEvidence.
 * Missing or unexpected values never crash the UI and never become
 * "confirmed" - they fall back to UNKNOWN / null / [].
 */
export function normalizeEvidence(raw: unknown, fallbackLeadId = ""): LeadEvidence {
  const r = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
  const rawSources = Array.isArray(r.sources) ? r.sources : [];

  const sources: EvidenceSource[] = rawSources.map((item, i) => {
    const s = (item && typeof item === "object" ? item : {}) as Record<string, unknown>;
    const wa = String(s.whatsapp_status ?? "").toUpperCase();
    const cb = String(s.chatbot_status ?? "").toUpperCase();
    return {
      id: str(s.id) ?? `source_${i}`,
      source_url: str(s.source_url),
      whatsapp_status: (WHATSAPP as readonly string[]).includes(wa)
        ? (wa as WhatsappStatus)
        : "UNKNOWN",
      chatbot_status: (CHATBOT as readonly string[]).includes(cb)
        ? (cb as ChatbotStatus)
        : "UNKNOWN",
      is_hot_lead: s.is_hot_lead === true,
      snippet: str(s.snippet),
    };
  });

  return {
    lead_id: str(r.lead_id) ?? fallbackLeadId,
    lead_name: str(r.lead_name) ?? "",
    last_inspected_at: str(r.last_inspected_at),
    sources,
  };
}

export async function fetchLeadEvidence(
  leadId: string,
  signal?: AbortSignal,
): Promise<LeadEvidence> {
  const res = await fetch(API.leadEvidence(leadId), { signal });
  if (!res.ok) {
    throw new Error(`Evidence request failed (${res.status})`);
  }
  return normalizeEvidence(await res.json(), leadId);
}
