
function StatusBadge({ status, type }) {
  const styles = {
    confirmed: "bg-green-100 text-green-700",
    probable: "bg-yellow-100 text-yellow-700",
    unknown: "bg-slate-100 text-slate-600",
    yes: "bg-green-100 text-green-700",
    no: "bg-red-100 text-red-700",
    manual: "bg-orange-100 text-orange-700",
    automated: "bg-blue-100 text-blue-700",
    hot: "bg-red-100 text-red-700",
  };

  const style = styles[status?.toLowerCase()] ||
    "bg-slate-100 text-slate-600";

  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${style}`}>
      {type === "hot" ? "Hot Lead" : status}
    </span>
  );
}

function ResultsTable({ leads, onSort, sortConfig }) {
  const columns = [
    { key: "business_name", label: "Business" },
    { key: "city", label: "Location" },
    { key: "niche", label: "Niche" },
    { key: "whatsapp_status", label: "WhatsApp" },
    { key: "chatbot_status", label: "Chatbot" },
    { key: "automation_status", label: "Automation" },
    { key: "lead_score", label: "Lead Score" },
  ];

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[1050px] text-left">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className="px-5 py-4 text-xs font-semibold uppercase tracking-wider text-slate-500"
              >
                <button
                  onClick={() => onSort(column.key)}
                  className="inline-flex items-center gap-2 hover:text-blue-600"
                >
                  {column.label}
                  <span>
                    {sortConfig.key === column.key
                      ? sortConfig.direction === "asc" ? "↑" : "↓"
                      : "↕"}
                  </span>
                </button>
              </th>
            ))}
            <th className="px-5 py-4 text-xs font-semibold uppercase text-slate-500">
              Lead Type
            </th>
          </tr>
        </thead>

        <tbody className="divide-y divide-slate-100">
          {leads.map((lead) => {
            const isHot =
              lead.automation_status === "MANUAL" &&
              lead.chatbot_status === "NO";

            return (
              <tr key={lead.id} className="transition hover:bg-slate-50">
                <td className="px-5 py-4">
                  <p className="font-semibold text-slate-800">
                    {lead.business_name}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    {lead.website || "No website"}
                  </p>
                </td>

                <td className="px-5 py-4 text-sm text-slate-600">
                  {lead.city}, {lead.country}
                </td>

                <td className="px-5 py-4 text-sm text-slate-600">
                  {lead.niche}
                </td>

                <td className="px-5 py-4">
                  <StatusBadge
                    status={lead.whatsapp_status}
                    type="whatsapp"
                  />
                </td>

                <td className="px-5 py-4">
                  <StatusBadge
                    status={lead.chatbot_status}
                    type="chatbot"
                  />
                </td>

                <td className="px-5 py-4">
                  <StatusBadge
                    status={lead.automation_status}
                    type="automation"
                  />
                </td>

                <td className="px-5 py-4">
                  <span className="font-bold text-slate-800">
                    {lead.lead_score}/100
                  </span>
                </td>

                <td className="px-5 py-4">
                  {isHot ? (
                    <StatusBadge status="Hot Lead" type="hot" />
                  ) : (
                    <span className="text-xs text-slate-400">Regular</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {leads.length === 0 && (
        <div className="px-6 py-16 text-center">
          <h3 className="font-semibold text-slate-800">
            No businesses found
          </h3>
          <p className="mt-2 text-sm text-slate-500">
            Try changing your search or filters.
          </p>
        </div>
      )}
    </div>
  );
}

export default ResultsTable;
