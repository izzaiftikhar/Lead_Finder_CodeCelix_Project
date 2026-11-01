
import { useCallback, useEffect, useMemo, useState } from "react";
import ResultsTable from "../components/ResultsTable";
import SearchFilters from "../components/SearchFilters";
import demoLeads from "../data/demoLeads";

// Default filter values
const initialFilters = {
  q: "",
  country: "All",
  city: "All",
  niche: "All",
  whatsapp: "All",
  chatbot: "All",
  automation: "All",
  hot_only: false,
};

// CSV helper
const exportToCSV = (leads) => {
  if (leads.length === 0) return;

  const columns = [
    "business_name",
    "country",
    "city",
    "niche",
    "website",
    "whatsapp_number",
    "whatsapp_status",
    "chatbot_status",
    "automation_status",
    "lead_score",
  ];

  const escapeCSV = (value) => {
    const text = String(value ?? "");
    return `"${text.replace(/"/g, '""')}"`;
  };

  const csvContent = [
    columns.join(","),
    ...leads.map((lead) =>
      columns.map((column) => escapeCSV(lead[column])).join(",")
    ),
  ].join("\n");

  const blob = new Blob(["\uFEFF" + csvContent], {
    type: "text/csv;charset=utf-8;",
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = "lead-results.csv";
  link.click();

  URL.revokeObjectURL(url);
};

function ResultsPage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loadAttempt, setLoadAttempt] = useState(0);

  const [filters, setFilters] = useState(initialFilters);

  const [sortConfig, setSortConfig] = useState({
    key: "lead_score",
    direction: "desc",
  });

  // Demo result metadata.
  // The real API will provide these values later.
  const [resultMeta, setResultMeta] = useState({
    requested: demoLeads.length,
    returned: 0,
  });

  // Load demo data
  useEffect(() => {
    setLoading(true);
    setError("");

    const timer = setTimeout(() => {
      try {
        setLeads(demoLeads);

        setResultMeta({
          requested: demoLeads.length,
          returned: demoLeads.length,
        });

        setLoading(false);
      } catch (err) {
        setError("Unable to load lead results. Please try again.");
        setLoading(false);
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [loadAttempt]);

  // Retry loading
  const handleRetry = () => {
    setLoadAttempt((current) => current + 1);
  };

  // Handle filter changes
  const handleFilterChange = (name, value) => {
    setFilters((currentFilters) => ({
      ...currentFilters,
      [name]: value,
    }));
  };

  // Reset filters
  const handleResetFilters = () => {
    setFilters({ ...initialFilters });
  };

  // Handle sorting
  const handleSort = (key) => {
    setSortConfig((current) => ({
      key,
      direction:
        current.key === key && current.direction === "asc"
          ? "desc"
          : "asc",
    }));
  };

  // Filter leads
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      const searchTerm = filters.q.trim().toLowerCase();

      const matchesSearch =
        !searchTerm ||
        lead.business_name.toLowerCase().includes(searchTerm) ||
        lead.city.toLowerCase().includes(searchTerm) ||
        lead.niche.toLowerCase().includes(searchTerm);

      const matchesCountry =
        filters.country === "All" ||
        lead.country === filters.country;

      const matchesCity =
        filters.city === "All" ||
        lead.city === filters.city;

      const matchesNiche =
        filters.niche === "All" ||
        lead.niche === filters.niche;

      const matchesWhatsApp =
        filters.whatsapp === "All" ||
        lead.whatsapp_status.startsWith(filters.whatsapp);

      const matchesChatbot =
        filters.chatbot === "All" ||
        lead.chatbot_status === filters.chatbot;

      const matchesAutomation =
        filters.automation === "All" ||
        lead.automation_status === filters.automation;

      const matchesHotLead =
        !filters.hot_only ||
        (lead.automation_status === "MANUAL" &&
          lead.chatbot_status === "NO");

      return (
        matchesSearch &&
        matchesCountry &&
        matchesCity &&
        matchesNiche &&
        matchesWhatsApp &&
        matchesChatbot &&
        matchesAutomation &&
        matchesHotLead
      );
    });
  }, [leads, filters]);

  // Sort filtered leads
  const sortedLeads = useMemo(() => {
    return [...filteredLeads].sort((a, b) => {
      const first = a[sortConfig.key] ?? "";
      const second = b[sortConfig.key] ?? "";

      if (typeof first === "number" && typeof second === "number") {
        return sortConfig.direction === "asc"
          ? first - second
          : second - first;
      }

      return sortConfig.direction === "asc"
        ? String(first).localeCompare(String(second))
        : String(second).localeCompare(String(first));
    });
  }, [filteredLeads, sortConfig]);

  // Summary values
  const confirmedWhatsApp = filteredLeads.filter((lead) =>
    lead.whatsapp_status.startsWith("Confirmed")
  ).length;

  const detectedChatbots = filteredLeads.filter(
    (lead) => lead.chatbot_status === "YES"
  ).length;

  const hotLeads = filteredLeads.filter(
    (lead) =>
      lead.automation_status === "MANUAL" &&
      lead.chatbot_status === "NO"
  ).length;

  // Partial results condition
  const isPartial =
    resultMeta.returned < resultMeta.requested && !loading && !error;

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 lg:px-10">
      <div className="mx-auto max-w-7xl">

        {/* Page Header */}
        <header className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
              Lead Results
            </h1>
            <p className="mt-2 text-sm text-slate-500">
              Explore, filter, and manage discovered business leads.
            </p>
          </div>

          <button
            type="button"
            onClick={() => exportToCSV(filteredLeads)}
            disabled={loading || filteredLeads.length === 0}
            className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Export CSV
          </button>
        </header>

        {/* Summary Cards */}
        <section className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Total Leads</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">
              {loading ? "—" : filteredLeads.length}
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">WhatsApp Confirmed</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">
              {loading ? "—" : confirmedWhatsApp}
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Chatbot Detected</p>
            <p className="mt-3 text-3xl font-bold text-slate-900">
              {loading ? "—" : detectedChatbots}
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Hot Leads</p>
            <p className="mt-3 text-3xl font-bold text-red-600">
              {loading ? "—" : hotLeads}
            </p>
          </div>
        </section>

        {/* Search and Filters */}
        <section className="mb-8">
          <SearchFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            onReset={handleResetFilters}
          />
        </section>

        {/* Results Section */}
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">

          {/* Results Header */}
          <div className="border-b border-slate-200 px-6 py-5">
            <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  Business Results
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  {loading
                    ? "Loading business results..."
                    : `Showing ${filteredLeads.length} of ${leads.length} illustrative demo businesses.`}
                </p>
              </div>

              <span className="w-fit rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
                Demo Data
              </span>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center px-6 py-16">
              <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

              <p className="mt-4 font-medium text-slate-700">
                Loading lead results...
              </p>

              <p className="mt-1 text-sm text-slate-500">
                Please wait while we prepare your data.
              </p>
            </div>
          )}

          {/* Error State */}
          {!loading && error && (
            <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-600">
                !
              </div>

              <h3 className="text-lg font-semibold text-slate-900">
                Something went wrong
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                {error}
              </p>

              <button
                type="button"
                onClick={handleRetry}
                className="mt-5 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
              >
                Try Again
              </button>
            </div>
          )}

          {/* Partial Results State */}
          {!loading && !error && isPartial && (
            <div className="border-b border-amber-200 bg-amber-50 px-6 py-4">
              <p className="text-sm font-medium text-amber-800">
                Partial results: {resultMeta.returned} of {resultMeta.requested} requested leads were returned.
              </p>
              <p className="mt-1 text-sm text-amber-700">
                Some results may be missing. You can continue using the available leads.
              </p>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && filteredLeads.length === 0 && (
            <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-500">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-7 w-7"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="1.7"
                >
                  <circle cx="11" cy="11" r="7" />
                  <path strokeLinecap="round" d="m16 16 4 4" />
                </svg>
              </div>

              <h3 className="text-lg font-semibold text-slate-900">
                No leads found
              </h3>

              <p className="mt-2 max-w-md text-sm text-slate-500">
                No businesses match your current search or filters. Try changing your filters or search term.
              </p>

              <button
                type="button"
                onClick={handleResetFilters}
                className="mt-5 rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                Clear Filters
              </button>
            </div>
          )}

          {/* Results Table */}
          {!loading && !error && filteredLeads.length > 0 && (
            <ResultsTable
              leads={sortedLeads}
              onSort={handleSort}
              sortConfig={sortConfig}
            />
          )}
        </section>
      </div>
    </div>
  );
}

export default ResultsPage;
