"use client";

// Example only: shows how EvidencePanel and ExportControls sit beside the
// existing results UI (same lead name, same status words, same layout language).
// In the real app, replace MOCK_LEAD_EVIDENCE with:
//   const evidence = await fetchLeadEvidence(leadId)   // GET /api/leads/:id/evidence (see api.ts)

import EvidencePanel from "./EvidencePanel";
import ExportControls from "./ExportControls";
import { MOCK_LEAD_EVIDENCE } from "./mockEvidence";

export default function LeadDetailsExample() {
  return (
    <main className="mx-auto max-w-5xl px-4 py-6">
      <h1 className="text-xl font-bold text-gray-900">Lead details</h1>
      <p className="mt-1 text-sm text-gray-600">
        Results view above, evidence view below, using the same lead record.
      </p>
      <div className="mt-4 flex flex-col gap-4">
        <ExportControls job_id="job_mock_001" leads={[MOCK_LEAD_EVIDENCE]} />
        <EvidencePanel evidence={MOCK_LEAD_EVIDENCE} isMock />
      </div>
    </main>
  );
}
