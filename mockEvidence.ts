// MOCK DATA ONLY. Delete once GET /api/leads/:id/evidence is live.
// Covers the edge cases: UNKNOWN chatbot, null snippet, very long URL, missing URL.

import type { LeadEvidence } from "./types";

export const MOCK_LEAD_EVIDENCE: LeadEvidence = {
  lead_id: "lead_mock_001",
  lead_name: "Ayesha Khan",
  last_inspected_at: "2026-10-30T10:15:00Z",
  sources: [
    {
      id: "src_website",
      source_url: "https://www.sukkurtextiles.example.com/about-us",
      whatsapp_status: "CONFIRMED",
      chatbot_status: "YES",
      is_hot_lead: true,
      snippet: "Company name and city match the lead record.",
    },
    {
      id: "src_linkedin",
      source_url:
        "https://www.linkedin.com/in/ayesha-khan-example-profile/details/experience/?very=long&query=string&that=keeps-going-and-going&utm_source=mock",
      whatsapp_status: "PROBABLE",
      chatbot_status: "UNKNOWN",
      is_hot_lead: false,
      snippet: "Profile exists, but job title could not be confirmed.",
    },
    {
      id: "src_directory",
      source_url: "https://directory.example.com/listing/12345",
      whatsapp_status: "NO",
      chatbot_status: "NO",
      is_hot_lead: false,
      snippet: null,
    },
    {
      id: "src_missing_url",
      source_url: null,
      whatsapp_status: "UNKNOWN",
      chatbot_status: "UNKNOWN",
      is_hot_lead: false,
      snippet: null,
    },
  ],
};
