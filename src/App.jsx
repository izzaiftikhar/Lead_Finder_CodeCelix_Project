
import React, { useState } from "react";
import DashboardLayout from "./layouts/DashboardLayout";
import ResultsPage from "./pages/ResultsPage";

const App = () => {
  const [activePage, setActivePage] = useState("Results");

  return (
    <DashboardLayout
      activePage={activePage}
      onNavigate={setActivePage}
    >
      {activePage === "Results" ? (
        <ResultsPage />
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white p-10 text-center">
          <h2 className="text-xl font-semibold text-slate-800">
            {activePage}
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            This section is not implemented in the current assignment.
          </p>

          <button
            onClick={() => setActivePage("Results")}
            className="mt-5 rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Back to Results
          </button>
        </div>
      )}
    </DashboardLayout>
  );
};

export default App;
