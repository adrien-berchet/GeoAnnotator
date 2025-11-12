/**
 * Search filter component.
 *
 * Provides filters for searching points by bounding box, tags, and text.
 */

import { useState } from "react";
import type { FormEvent } from "react";
import type { PointsFilter } from "../../types/point";

interface SearchFilterProps {
  onFilterChange: (filter: PointsFilter) => void;
}

/**
 * Search filter component.
 */
export function SearchFilter({ onFilterChange }: SearchFilterProps) {
  const [searchText, setSearchText] = useState("");
  const [tags, setTags] = useState("");
  const [isPublicOnly, setIsPublicOnly] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Bounding box coordinates
  const [minLat, setMinLat] = useState("");
  const [maxLat, setMaxLat] = useState("");
  const [minLon, setMinLon] = useState("");
  const [maxLon, setMaxLon] = useState("");

  /**
   * Handle form submission.
   */
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    applyFilters();
  };

  /**
   * Apply filters.
   */
  const applyFilters = () => {
    const filter: PointsFilter = {};

    // Text search
    if (searchText.trim()) {
      filter.search = searchText.trim();
    }

    // Tags
    if (tags.trim()) {
      filter.tags = tags
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0);
    }

    // Public only
    if (isPublicOnly) {
      filter.is_public = true;
    }

    // Bounding box
    if (minLat && maxLat && minLon && maxLon) {
      const minLatNum = parseFloat(minLat);
      const maxLatNum = parseFloat(maxLat);
      const minLonNum = parseFloat(minLon);
      const maxLonNum = parseFloat(maxLon);

      if (
        !isNaN(minLatNum) &&
        !isNaN(maxLatNum) &&
        !isNaN(minLonNum) &&
        !isNaN(maxLonNum)
      ) {
        filter.bbox = {
          min_lat: minLatNum,
          max_lat: maxLatNum,
          min_lon: minLonNum,
          max_lon: maxLonNum,
        };
      }
    }

    onFilterChange(filter);
  };

  /**
   * Clear all filters.
   */
  const clearFilters = () => {
    setSearchText("");
    setTags("");
    setIsPublicOnly(false);
    setMinLat("");
    setMaxLat("");
    setMinLon("");
    setMaxLon("");
    onFilterChange({});
  };

  return (
    <div className="search-filter">
      <form onSubmit={handleSubmit} className="search-filter-form">
        {/* Text search */}
        <div className="form-group">
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search in title and description..."
            className="search-input"
          />
        </div>

        {/* Tags */}
        <div className="form-group">
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="Filter by tags (comma-separated)..."
          />
        </div>

        {/* Public only checkbox */}
        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={isPublicOnly}
              onChange={(e) => setIsPublicOnly(e.target.checked)}
            />
            <span>Public points only</span>
          </label>
        </div>

        {/* Advanced filters toggle */}
        <button
          type="button"
          className="btn-link"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? "Hide" : "Show"} advanced filters
        </button>

        {/* Advanced filters */}
        {showAdvanced && (
          <div className="advanced-filters">
            <h4>Bounding Box</h4>
            <div className="bbox-grid">
              <div className="form-group">
                <label htmlFor="minLat">Min Latitude</label>
                <input
                  id="minLat"
                  type="number"
                  step="0.000001"
                  value={minLat}
                  onChange={(e) => setMinLat(e.target.value)}
                  placeholder="-90 to 90"
                  min="-90"
                  max="90"
                />
              </div>
              <div className="form-group">
                <label htmlFor="maxLat">Max Latitude</label>
                <input
                  id="maxLat"
                  type="number"
                  step="0.000001"
                  value={maxLat}
                  onChange={(e) => setMaxLat(e.target.value)}
                  placeholder="-90 to 90"
                  min="-90"
                  max="90"
                />
              </div>
              <div className="form-group">
                <label htmlFor="minLon">Min Longitude</label>
                <input
                  id="minLon"
                  type="number"
                  step="0.000001"
                  value={minLon}
                  onChange={(e) => setMinLon(e.target.value)}
                  placeholder="-180 to 180"
                  min="-180"
                  max="180"
                />
              </div>
              <div className="form-group">
                <label htmlFor="maxLon">Max Longitude</label>
                <input
                  id="maxLon"
                  type="number"
                  step="0.000001"
                  value={maxLon}
                  onChange={(e) => setMaxLon(e.target.value)}
                  placeholder="-180 to 180"
                  min="-180"
                  max="180"
                />
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="filter-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={clearFilters}
          >
            Clear
          </button>
          <button type="submit" className="btn-primary">
            Apply Filters
          </button>
        </div>
      </form>
    </div>
  );
}
