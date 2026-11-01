
function SearchFilters({ filters, onFilterChange, onReset }) {
  const handleChange = (event) => {
    const { name, value } = event.target;

    onFilterChange(name, value);
  };

  const selectClass =
    "w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100";

  return (
    <section className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Search & Filters
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Narrow down businesses using your preferred criteria.
          </p>
        </div>

        <button
          type="button"
          onClick={onReset}
          className="text-sm font-semibold text-blue-600 hover:text-blue-700"
        >
          Reset Filters
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">

        {/* Search */}
        <div className="sm:col-span-2">
          <label className="mb-2 block text-sm font-medium text-slate-700">
            Search Businesses
          </label>

          <input
            type="text"
            name="q"
            value={filters.q}
            onChange={handleChange}
            placeholder="Search name, city, or niche..."
            className={selectClass}
          />
        </div>

        {/* Country */}
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">
            Country
          </label>

          <select
            name="country"
            value={filters.country}
            onChange={handleChange}
            className={selectClass}
          >
            <option value="All">All Countries</option>
            <option value="UAE">UAE</option>
          </select>
        </div>

        {/* City */}
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">
            City
          </label>

          <select
            name="city"
            value={filters.city}
            onChange={handleChange}
            className={selectClass}
          >
            <option value="All">All Cities</option>
            <option value="Dubai">Dubai</option>
            <option value="Abu Dhabi">Abu Dhabi</option>
            <option value="Sharjah">Sharjah</option>
          </select>
        </div>

        {/* Niche */}
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">
            Niche
          </label>

          <select
            name="niche"
            value={filters.niche}
            onChange={handleChange}
            className={selectClass}
          >
            <option value="All">All Niches</option>
            <option value="Real Estate">Real Estate</option>
            <option value="Healthcare">Healthcare</option>
            <option value="Travel">Travel</option>
            <option value="Fitness">Fitness</option>
          </select>
        </div>

        {/* WhatsApp */}
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">
            WhatsApp Status
          </label>

          <select
            name="whatsapp"
            value={filters.whatsapp}
            onChange={handleChange}
            className={selectClass}
          >
            <option value="All">All Statuses</option>
            <option value="Confirmed">Confirmed</option>
            <option value="Probable">Probable</option>
          </select>
        </div>

        {/* Chatbot */}
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">
            Chatbot
          </label>

          <select
            name="chatbot"
            value={filters.chatbot}
            onChange={handleChange}
            className={selectClass}
          >
            <option value="All">All</option>
            <option value="YES">Yes</option>
            <option value="NO">No</option>
            <option value="UNKNOWN">Unknown</option>
          </select>
        </div>

        {/* Automation */}
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">
            Automation
          </label>

          <select
            name="automation"
            value={filters.automation}
            onChange={handleChange}
            className={selectClass}
          >
            <option value="All">All</option>
            <option value="MANUAL">Manual</option>
            <option value="AUTOMATED">Automated</option>
            <option value="UNKNOWN">Unknown</option>
          </select>
        </div>

        {/* Hot Leads */}
        <div className="flex items-end pb-1">
          <label className="flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-700">
            <input
              type="checkbox"
              name="hot_only"
              checked={filters.hot_only}
              onChange={(event) =>
                onFilterChange("hot_only", event.target.checked)
              }
              className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            Hot Leads Only
          </label>
        </div>

      </div>
    </section>
  );
}

export default SearchFilters;
