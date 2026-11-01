import type { Lead } from "./types";

const COLUMNS: (keyof Lead)[] = [
  "name", "address", "country", "industry", "phone", "website",
  "whatsapp", "whatsapp_number", "chatbot", "chatbot_vendors", "score",
];

const quote = (v: unknown) =>
  `"${String(Array.isArray(v) ? v.join("; ") : v ?? "").replace(/"/g, '""')}"`;

export function downloadCsv(leads: Lead[], filename = "leads.csv") {
  const rows = [COLUMNS.join(","), ...leads.map((l) => COLUMNS.map((c) => quote(l[c])).join(","))];
  const url = URL.createObjectURL(new Blob([rows.join("\n")], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
