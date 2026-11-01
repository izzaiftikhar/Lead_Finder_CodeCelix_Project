import type { EvidenceSource, LeadEvidence } from "./types";

export const CSV_HEADER = [
  "lead_name",
  "lead_id",
  "source_url",
  "whatsapp_status",
  "chatbot_status",
  "is_hot_lead",
  "snippet",
] as const;

/** Quote every cell, escape quotes, and neutralise spreadsheet formulas (CSV injection). */
export function csvCell(value: string | boolean | null | undefined): string {
  let text = String(value ?? "");
  if (/^[=+\-@\t\r]/.test(text)) text = `'${text}`;
  return `"${text.replace(/"/g, '""')}"`;
}

/** codecelix_leads_{job_id}_{YYYY-MM-DD}.csv */
export function getExportFileName(jobId: string, date: Date = new Date()): string {
  const safeId = jobId.trim().replace(/[^A-Za-z0-9_-]/g, "_") || "unknown";
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  return `codecelix_leads_${safeId}_${yyyy}-${mm}-${dd}.csv`;
}

function rowFor(leadName: string, leadId: string, s: EvidenceSource): string {
  return [
    csvCell(leadName),
    csvCell(leadId),
    csvCell(s.source_url),
    csvCell(s.whatsapp_status),
    csvCell(s.chatbot_status),
    csvCell(s.is_hot_lead),
    csvCell(s.snippet),
  ].join(",");
}

/** CSV for one lead's sources. */
export function buildEvidenceCsv(
  leadName: string,
  leadId: string,
  sources: EvidenceSource[],
): string {
  return [CSV_HEADER.join(","), ...sources.map((s) => rowFor(leadName, leadId, s))].join("\r\n");
}

/** CSV for many leads (one row per source). */
export function buildLeadsCsv(leads: LeadEvidence[]): string {
  const rows = leads.flatMap((l) => l.sources.map((s) => rowFor(l.lead_name, l.lead_id, s)));
  return [CSV_HEADER.join(","), ...rows].join("\r\n");
}

export function countExportRows(leads: LeadEvidence[]): number {
  return leads.reduce((n, l) => n + l.sources.length, 0);
}

/** Triggers a browser download. Throws if the browser cannot do it. */
export function downloadCsv(fileName: string, csv: string): void {
  if (typeof document === "undefined") {
    throw new Error("Downloads are only available in the browser.");
  }
  // BOM so Excel opens UTF-8 correctly.
  const blob = new Blob(["﻿", csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  try {
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
  } finally {
    URL.revokeObjectURL(url);
  }
}
