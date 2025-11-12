/**
 * MapSearchBar Component
 *
 * Search bar component for the map interface that allows users to filter points on the map.
 * Positioned near the Filter Tags panel on the map page.
 *
 * Features:
 * - Controlled input with local state management
 * - Filters points on the map when form is submitted (Enter or button click)
 * - Clear button to reset search
 * - Accessible with proper ARIA labels
 * - Responsive design (desktop: left of counter, mobile: between counter and filter button)
 */

import { useState } from "react";
import type { FormEvent } from "react";
import "./MapSearchBar.css";

interface MapSearchBarProps {
  /**
   * Callback function called when search is submitted
   * @param query - The search query string (trimmed)
   */
  onSearch: (query: string) => void;
}

/**
 * Search bar component for map interface
 * Allows users to filter points on the map by search query
 */
export function MapSearchBar({ onSearch }: MapSearchBarProps) {
  const [searchQuery, setSearchQuery] = useState("");

  /**
   * Handles form submission
   * Triggers search with trimmed query
   */
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmedQuery = searchQuery.trim();
    onSearch(trimmedQuery);
  };

  /**
   * Handles clear button click
   * Resets search query and triggers empty search
   */
  const handleClear = () => {
    setSearchQuery("");
    onSearch("");
  };

  return (
    <form
      className="map-search-bar"
      role="search"
      aria-label="Search points on map"
      onSubmit={handleSubmit}
    >
      <input
        type="search"
        className="map-search-input"
        placeholder="Search points..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        aria-label="Search query"
      />
      <button
        type="button"
        className="map-search-button"
        aria-label={searchQuery ? "Clear search" : "Submit search"}
        onClick={searchQuery ? handleClear : undefined}
        title={searchQuery ? "Clear search" : "Submit search"}
      >
        {searchQuery ? "✕" : "🔍"}
      </button>
    </form>
  );
}
