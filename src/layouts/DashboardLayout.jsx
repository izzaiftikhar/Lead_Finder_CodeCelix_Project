
import React, { useState } from "react";

const navigationItems = [
  { name: "Dashboard", icon: "▦" },
  { name: "Search Leads", icon: "⌕" },
  { name: "Results", icon: "☷" },
  { name: "Saved Leads", icon: "☆" },
  { name: "Settings", icon: "⚙" },
];

const DashboardLayout = ({ children, activePage, onNavigate }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleNavigation = (page) => {
    onNavigate(page);
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <button
          aria-label="Close sidebar"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0`}
      >
        <div className="flex h-20 items-center border-b border-slate-200 px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-xl font-bold text-white">
            L
          </div>

          <div className="ml-3">
            <h1 className="text-lg font-bold text-slate-900">
              LeadFinder
            </h1>
            <p className="text-xs text-slate-500">
              Business Intelligence
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-2 px-4 py-6">
          <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Workspace
          </p>

          {navigationItems.map((item) => (
            <button
              key={item.name}
              onClick={() => handleNavigation(item.name)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition ${
                activePage === item.name
                  ? "bg-blue-50 text-blue-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              {item.name}
            </button>
          ))}
        </nav>

        <div className="border-t border-slate-200 p-4">
          <div className="rounded-xl bg-slate-50 p-3">
            <p className="text-sm font-semibold text-slate-800">
              Demo Workspace
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Illustrative data only
            </p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="min-h-screen md:ml-64">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            {/* Mobile menu button */}
            <button
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden"
            >
              ☰
            </button>

            <div>
              <h2 className="text-base font-semibold text-slate-900 sm:text-lg">
                {activePage}
              </h2>
              <p className="hidden text-xs text-slate-500 sm:block">
                Manage and review business leads
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <span className="rounded-full bg-amber-50 px-2 py-1.5 text-xs font-medium text-amber-700 sm:px-3">
              Demo Mode
            </span>

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 font-semibold text-blue-700">
              S
            </div>
          </div>
        </header>

        <main className="p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
