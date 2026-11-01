"use client";

import { FormEvent, useState } from "react";
import type { SearchParams } from "@/lib/types";

const CITIES_BY_COUNTRY: Record<string, string[]> = {
  UAE: ["Dubai", "Abu Dhabi", "Sharjah"],
  UK: ["London", "Manchester", "Birmingham"],
  US: ["New York", "Los Angeles", "Chicago"],
};

const COUNTRIES = Object.keys(CITIES_BY_COUNTRY);
const INDUSTRIES = ["Real Estate", "Clinic"];

type Props = {
  loading: boolean;
  onSearch: (params: SearchParams) => void;
};

export default function SearchForm({ loading, onSearch }: Props) {
  const [country, setCountry] = useState("");
  const [city, setCity] = useState("");
  const [industry, setIndustry] = useState("");
  const [limit, setLimit] = useState(30);

  const cities = country ? CITIES_BY_COUNTRY[country] ?? [] : [];

  function handleCountryChange(value: string) {
    setCountry(value);
    setCity(""); // reset city when country changes
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    onSearch({
      country,
      city,
      industry,
      limit,
      only_with_website: true,
    });
  }

  return (
    <form onSubmit={submit} className="form">
      <select
        value={country}
        onChange={(e) => handleCountryChange(e.target.value)}
        required
        aria-label="Country"
      >
        <option value="" disabled>
          Select country
        </option>
        {COUNTRIES.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>

      <select
        value={city}
        onChange={(e) => setCity(e.target.value)}
        required
        disabled={!country}
        aria-label="City"
      >
        <option value="" disabled>
          {country ? "Select city" : "Select country first"}
        </option>
        {cities.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>

      <select
        value={industry}
        onChange={(e) => setIndustry(e.target.value)}
        required
        aria-label="Industry"
      >
        <option value="" disabled>
          Select industry
        </option>
        {INDUSTRIES.map((i) => (
          <option key={i} value={i}>
            {i}
          </option>
        ))}
      </select>

      <input
        type="number"
        min={1}
        max={100}
        value={limit}
        onChange={(e) => setLimit(Number(e.target.value))}
        style={{ width: 80 }}
        aria-label="Result limit"
      />
      <button type="submit" disabled={loading}>
        {loading ? "Searching..." : "Search"}
      </button>
    </form>
  );
}