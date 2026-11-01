export type WaStatus = "CONFIRMED" | "PROBABLE" | null;
export type WaType = "MANUAL" | "AUTOMATED" | "UNKNOWN" | null;
export type Tri = "YES" | "NO" | "UNKNOWN";
export type JobStatus = "QUEUED" | "RUNNING" | "COMPLETED" | "PARTIAL" | "FAILED" | "CANCELLED";

export const COUNTRY: Record<string, string> = { AE: "UAE", SA: "Saudi Arabia", QA: "Qatar", KW: "Kuwait", BH: "Bahrain", GB: "UK", US: "USA" };
export const NICHE: Record<string, string> = { REAL_ESTATE: "Real Estate", CLINICS: "Clinics", B2B_AGENCIES: "B2B Agencies", SAAS: "SaaS" };

export type User = { id: string; email: string; role: "admin" | "user" };
export type Me = { user: User; live_available: boolean };

export type Market = { code: string; name: string; niches: { code: string; name: string }[] };
export type Markets = { countries: Market[]; live_available: boolean; limits: { min: number; max: number } };
export type City = { id: number; name: string; admin1: string | null };
export type Estimate = { minutes_p50: number; minutes_p90: number; expected_yield: number; basis: string };

export type Filters = {
  whatsapp_confirmed_only: boolean; no_chatbot_only: boolean; manual_whatsapp_only: boolean;
  website_required: boolean; exclude_previously_exported: boolean;
};
export type JobCreate = { country: string; niche: string; city_ids: number[]; all_cities: boolean; lead_count: number; mode: "live" | "demo"; filters: Filters };

export type Job = {
  id: string; country: string; niche: string; city_ids: number[]; lead_count: number; filters: Filters; mode: "live" | "demo";
  status: JobStatus; accepted_count: number; candidates_seen: number; inspected_count: number;
  shortfall: { breakdown?: Record<string, number>; reason?: string | null } | null;
  message: string | null; cost_usd: number; created_at: string; started_at: string | null; finished_at: string | null;
};

export type Lead = {
  id: string; job_id: string; business_name: string; niche: string; country: string; city: string | null;
  website: { url: string | null; has_website: boolean };
  whatsapp: { number: string | null; status: WaStatus; type: WaType; type_confidence: number | null; source_url: string | null };
  chatbot: { value: Tri | null; vendor: string | null; kind: string | null };
  hot_lead: boolean; phone: string | null; email: string | null; address: string | null; maps_url: string | null;
  confidence: number | null; evidence_url: string | null; checked_at: string; inspection_status: string;
  signals: {
    pages?: { url: string; status: string; code: number }[]; notes?: string[]; render?: string;
    whatsapp_evidence?: { rule: string; matched: string; source_url: string }; wa_type_evidence?: string; chatbot_evidence?: string;
  };
  feedback: string | null; saved: boolean; exported_at: string | null; is_demo: boolean; source: string; rating: number | null;
};

export type Stats = {
  total_leads: number; hot_leads: number; whatsapp_confirmed: number; whatsapp_manual: number; whatsapp_automated: number;
  chatbot_yes: number; saved: number; jobs: number; jobs_active: number; by_niche: { label: string; n: number }[]; recent_jobs: Job[];
};

export type AdminConfig = {
  country_niches: { country: string; niche: string; enabled: number }[];
  keywords: { id: number; niche: string; region: string; lang: string; keyword: string; enabled: number }[];
  signatures: { id: number; vendor: string; kind: string; scope: string; pattern: string; enabled: number }[];
  limits: { key: string; value: string }[]; suppressed: number; users: number;
};
export type Cost = { by_day: { day: string; jobs: number; cost_usd: number | null; leads: number | null }[]; total_usd: number; note: string };
