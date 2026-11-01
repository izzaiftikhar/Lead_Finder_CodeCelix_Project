"use client";

import { useState } from "react";
import type {
  ChatbotStatus,
  EvidenceSource,
  LeadEvidence,
  WhatsappStatus,
} from "./types";

type Tone = "good" | "warn" | "bad" | "unknown";

const TONE: Record<Tone, string> = {
  good: "bg-green-50 text-green-800 border-green-300",
  warn: "bg-amber-50 text-amber-800 border-amber-300",
  bad: "bg-gray-100 text-gray-700 border-gray-300",
  unknown: "bg-gray-50 text-gray-600 border-dashed border-gray-400",
};

// Text labels always accompany colour so status is not colour-only.
const WHATSAPP_VIEW: Record<WhatsappStatus, { label: string; tone: Tone }> = {
  CONFIRMED: { label: "Confirmed", tone: "good" },
  PROBABLE: { label: "Probable (not confirmed)", tone: "warn" },
  NO: { label: "Not found", tone: "bad" },
  UNKNOWN: { label: "Unverified", tone: "unknown" },
};

const CHATBOT_VIEW: Record<ChatbotStatus, { label: string; tone: Tone }> = {
  YES: { label: "Chatbot detected", tone: "good" },
  NO: { label: "No chatbot detected", tone: "bad" },
  UNKNOWN: { label: "Unknown (not inspected)", tone: "unknown" },
};

function Badge({ label, tone }: { label: string; tone: Tone }) {
  return (
    <span className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${TONE[tone]}`}>
      {label}
    </span>
  );
}

function isHttpUrl(url: string): boolean {
  try {
    const p = new URL(url).protocol;
    return p === "http:" || p === "https:";
  } catch {
    return false;
  }
}

function SourceUrl({ url }: { url: string | null }) {
  const [copied, setCopied] = useState(false);

  if (!url) {
    return <p className="text-sm italic text-gray-500">No source URL returned.</p>;
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(url as string);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="flex min-w-0 items-center gap-2">
      {isHttpUrl(url) ? (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          title={url}
          className="min-w-0 flex-1 truncate text-sm text-blue-700 underline"
        >
          {url}
        </a>
      ) : (
        <span title={url} className="min-w-0 flex-1 truncate text-sm text-gray-700">
          {url} <em className="text-xs text-amber-700">(not a valid link)</em>
        </span>
      )}
      <button
        type="button"
        onClick={copy}
        className="shrink-0 rounded border border-gray-300 px-2 py-0.5 text-xs text-gray-700 hover:bg-gray-50"
      >
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  );
}

function SourceCard({ src }: { src: EvidenceSource }) {
  const wa = WHATSAPP_VIEW[src.whatsapp_status] ?? WHATSAPP_VIEW.UNKNOWN;
  const cb = CHATBOT_VIEW[src.chatbot_status] ?? CHATBOT_VIEW.UNKNOWN;

  return (
    <li className="rounded-lg border border-gray-200 bg-white p-3 sm:p-4">
      <SourceUrl url={src.source_url} />

      <dl className="mt-3 grid grid-cols-1 gap-2 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-xs text-gray-500">WhatsApp</dt>
          <dd><Badge {...wa} /></dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Chatbot</dt>
          <dd><Badge {...cb} /></dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Hot lead</dt>
          <dd>
            <Badge
              label={src.is_hot_lead ? "Hot lead" : "Not flagged"}
              tone={src.is_hot_lead ? "good" : "bad"}
            />
          </dd>
        </div>
      </dl>

      <p className="mt-3 break-words text-sm text-gray-800">
        {src.snippet ? (
          src.snippet
        ) : (
          <span className="italic text-gray-500">No evidence snippet available.</span>
        )}
      </p>
    </li>
  );
}

function formatInspected(value?: string | null): string | null {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d.toLocaleString();
}

export function EvidencePanel({
  evidence,
  isMock = false,
}: {
  evidence: LeadEvidence;
  isMock?: boolean;
}) {
  const inspected = formatInspected(evidence.last_inspected_at);
  const sources = evidence.sources ?? [];

  return (
    <section className="w-full max-w-full rounded-xl border border-gray-200 bg-gray-50 p-3 sm:p-5">
      {isMock && (
        <p className="mb-3 rounded border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-800">
          MOCK DATA - not returned by the backend.
        </p>
      )}

      <header className="mb-3">
        <h2 className="break-words text-lg font-semibold text-gray-900">
          Evidence{evidence.lead_name ? ` for ${evidence.lead_name}` : ""}
        </h2>
        <p className="text-sm text-gray-600">
          {inspected ? `Last inspected: ${inspected}` : "Not inspected yet - evidence is unverified."}
        </p>
      </header>

      {sources.length === 0 ? (
        <p className="rounded border border-dashed border-gray-400 p-4 text-sm text-gray-600">
          No evidence returned. Nothing about this lead has been verified.
        </p>
      ) : (
        <ul className="flex flex-col gap-3">
          {sources.map((src) => (
            <SourceCard key={src.id} src={src} />
          ))}
        </ul>
      )}
    </section>
  );
}

export default EvidencePanel;
