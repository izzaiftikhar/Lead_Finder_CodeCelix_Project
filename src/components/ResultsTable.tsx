import type { Lead } from "@/lib/types";
import StatusBadge from "./StatusBadge";

export default function ResultsTable({ leads }: { leads: Lead[] }) {
  if (leads.length === 0) return <p className="muted">No leads to show yet.</p>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Phone</th>
            <th>Website</th>
            <th>WhatsApp</th>
            <th>Chatbot</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((l, i) => (
            <tr key={`${l.name}-${i}`}>
              <td title={l.address}>{l.name}</td>
              <td>{l.phone || "-"}</td>
              <td>
                {l.website ? (
                  <a href={l.website} target="_blank" rel="noopener noreferrer">
                    {l.website.replace(/^https?:\/\//, "").slice(0, 40)}
                  </a>
                ) : (
                  "-"
                )}
              </td>
              <td>
                <StatusBadge value={l.whatsapp} />
              </td>
              <td>
                <StatusBadge
                  value={l.chatbot}
                  label={l.chatbot === "yes" ? l.chatbot_vendors.join(", ") : undefined}
                />
              </td>
              <td>{l.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
