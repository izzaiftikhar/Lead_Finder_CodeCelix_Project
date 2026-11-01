// Evidence contract (snake_case, as confirmed with backend).
// Endpoint: GET /api/leads/:id/evidence  (see api.ts - the single source of truth for paths)

export type WhatsappStatus = "CONFIRMED" | "PROBABLE" | "NO" | "UNKNOWN";
// "UNKNOWN" = the chatbot check has not run / could not be completed.
// It must never be shown as "NO" (not detected) or "YES" (detected).
export type ChatbotStatus = "YES" | "NO" | "UNKNOWN";

// Note: UNKNOWN on whatsapp_status is a client-side safety fallback for
// missing/unexpected values; the backend contract lists CONFIRMED/PROBABLE/NO.

export interface EvidenceSource {
  id: string;
  source_url: string | null; // snake_case, not sourceUrl; may be missing
  whatsapp_status: WhatsappStatus;
  chatbot_status: ChatbotStatus;
  is_hot_lead: boolean;
  snippet?: string | null;
}

export interface LeadEvidence {
  lead_id: string;
  lead_name: string;
  sources: EvidenceSource[];
  last_inspected_at?: string | null;
}

export type ExportStatus =
  | { state: "idle" }
  | { state: "success"; fileName: string; rowCount: number }
  | { state: "empty" }
  | { state: "error"; message: string };
