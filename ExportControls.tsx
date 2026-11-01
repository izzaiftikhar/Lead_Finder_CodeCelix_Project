"use client";

import { useState } from "react";
import {
  buildLeadsCsv,
  countExportRows,
  downloadCsv,
  getExportFileName,
} from "./exportCsv";
import type { ExportStatus, LeadEvidence } from "./types";

interface Props {
  job_id: string;
  /** Leads (with their sources) to include in the CSV. */
  leads: LeadEvidence[];
}

export function ExportControls({ job_id, leads }: Props) {
  const [status, setStatus] = useState<ExportStatus>({ state: "idle" });
  const fileName = getExportFileName(job_id);
  const rowCount = countExportRows(leads);

  function handleExport() {
    if (rowCount === 0) {
      setStatus({ state: "empty" });
      return;
    }
    try {
      downloadCsv(fileName, buildLeadsCsv(leads));
      setStatus({ state: "success", fileName, rowCount });
    } catch (err) {
      setStatus({
        state: "error",
        message: err instanceof Error ? err.message : "Unknown error",
      });
    }
  }

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <button
        type="button"
        onClick={handleExport}
        disabled={rowCount === 0}
        className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
      >
        Export CSV
      </button>
      <span className="break-all text-xs text-gray-500">{fileName}</span>

      <div role="status" aria-live="polite" className="text-sm">
        {status.state === "success" && (
          <p className="text-green-700">
            Exported {status.rowCount} rows to {status.fileName}.
          </p>
        )}
        {(status.state === "empty" || (status.state === "idle" && rowCount === 0)) && (
          <p className="text-gray-600">Nothing to export yet.</p>
        )}
        {status.state === "error" && (
          <p className="text-red-700">Export failed: {status.message}</p>
        )}
      </div>
    </div>
  );
}

export default ExportControls;
