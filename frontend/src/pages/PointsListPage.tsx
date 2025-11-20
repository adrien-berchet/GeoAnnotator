/**
 * Points list page.
 *
 * Displays all user's points in a list/grid view with search and filters.
 */

import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getPoints, searchPointsByTags, getTags } from "../api/points";
import { getPointTypes } from "../api/types";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { FilterPanel } from "../components/common/FilterPanel";
import { SharePanel } from "../components/sharing/SharePanel";
import { useLanguage } from "../contexts/LanguageContext";
import type { GPSPoint, Tag, PointType } from "../types/point";
import { batchSharePoints } from "../api/friends";
import "./PointsListPage.css";

export function PointsListPage() {
  const { t, language } = useLanguage();
  const [points, setPoints] = useState<GPSPoint[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [availableTypes, setAvailableTypes] = useState<PointType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [error, setError] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState("");
  const [selectedTagNames, setSelectedTagNames] = useState<string[]>([]);
  const [selectedTypeIds, setSelectedTypeIds] = useState<string[]>([]);
  const [selectedPointIds, setSelectedPointIds] = useState<string[]>([]);
  const [isSharePanelOpen, setIsSharePanelOpen] = useState(false);
  const [sharingModeActive, setSharingModeActive] = useState(false);
  const [lastClickedIndex, setLastClickedIndex] = useState<number | null>(null);
  const navigate = useNavigate();

  const searchQuery = searchParams.get("search") || "";
  const tagsFilter = searchParams.get("tags") || "";
  const typesFilter = searchParams.get("types") || "";
  const isFilterPanelOpen = searchParams.get("filterOpen") === "true";

  const loadTags = async () => {
    try {
      const data = await getTags();
      setAvailableTags(data);
    } catch (err) {
      console.error("Error loading tags:", err);
    }
  };

  const loadTypes = async () => {
    try {
      const data = await getPointTypes();
      setAvailableTypes(data);
    } catch (err) {
      console.error("Error loading types:", err);
    }
  };

  const loadPoints = async () => {
    setIsLoading(true);
    setError("");

    try {
      let results: GPSPoint[];

      if (tagsFilter) {
        const tags = tagsFilter.split(",").map((t) => t.trim());
        results = await searchPointsByTags(tags);
      } else {
        results = await getPoints();
      }

      // Client-side search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        results = results.filter(
          (p) =>
            p.title.toLowerCase().includes(query) ||
            p.description?.toLowerCase().includes(query) ||
            p.tags.some((t) => t.name.toLowerCase().includes(query)),
        );
      }

      // Client-side type filter
      if (typesFilter) {
        const typeIds = typesFilter.split(",").map((t) => t.trim());
        results = results.filter((p) => p.type && typeIds.includes(p.type.id));
      }

      setPoints(results);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
      setIsInitialLoad(false);
    }
  };

  useEffect(() => {
    loadTags();
    loadTypes();
  }, []);

  useEffect(() => {
    loadPoints();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, tagsFilter, typesFilter]);

  useEffect(() => {
    // Sync searchInput with URL params
    setSearchInput(searchQuery);
  }, [searchQuery]);

  useEffect(() => {
    // Sync filters with URL params
    setSelectedTagNames(tagsFilter ? tagsFilter.split(",") : []);
    setSelectedTypeIds(typesFilter ? typesFilter.split(",") : []);
  }, [tagsFilter, typesFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSearchParams({ search: searchInput.trim() });
    } else {
      // Si la recherche est vide, enlever le paramètre
      const newParams = new URLSearchParams(searchParams);
      newParams.delete("search");
      setSearchParams(newParams);
    }
  };

  const handleOpenFilterPanel = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("filterOpen", "true");
    setSearchParams(newParams);
  };

  const handleClearFilters = () => {
    setSearchParams({});
  };

  const handleCloseFilterPanel = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete("filterOpen");
    setSearchParams(newParams);
  };

  const handleToggleTag = (tagName: string) => {
    const newSelectedTags = selectedTagNames.includes(tagName)
      ? selectedTagNames.filter((t) => t !== tagName)
      : [...selectedTagNames, tagName];

    const newParams = new URLSearchParams(searchParams);

    if (newSelectedTags.length > 0) {
      newParams.set("tags", newSelectedTags.join(","));
    } else {
      newParams.delete("tags");
    }

    // Keep types filter if present
    if (selectedTypeIds.length > 0) {
      newParams.set("types", selectedTypeIds.join(","));
    }

    // Garder le panneau ouvert
    newParams.set("filterOpen", "true");

    setSearchParams(newParams);
  };

  const handleToggleType = (typeId: string) => {
    const newSelectedTypes = selectedTypeIds.includes(typeId)
      ? selectedTypeIds.filter((t) => t !== typeId)
      : [...selectedTypeIds, typeId];

    const newParams = new URLSearchParams(searchParams);

    if (newSelectedTypes.length > 0) {
      newParams.set("types", newSelectedTypes.join(","));
    } else {
      newParams.delete("types");
    }

    // Keep tags filter if present
    if (selectedTagNames.length > 0) {
      newParams.set("tags", selectedTagNames.join(","));
    }

    // Garder le panneau ouvert
    newParams.set("filterOpen", "true");

    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setSearchParams({});
    setSearchInput("");
  };

  // Point selection handlers
  const handleTogglePoint = (pointIndex: number, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click navigation

    const pointId = points[pointIndex].id;
    const isSelected = selectedPointIds.includes(pointId);

    // Shift-click: select/deselect range
    if (e.shiftKey && lastClickedIndex !== null) {
      const start = Math.min(lastClickedIndex, pointIndex);
      const end = Math.max(lastClickedIndex, pointIndex);
      const rangeIds = points.slice(start, end + 1).map((p) => p.id);

      setSelectedPointIds((prev) => {
        if (isSelected) {
          // Deselect range
          return prev.filter((id) => !rangeIds.includes(id));
        } else {
          // Select range
          const newSelection = new Set([...prev, ...rangeIds]);
          return Array.from(newSelection);
        }
      });
    } else {
      // Normal click: toggle single point
      setSelectedPointIds((prev) =>
        isSelected ? prev.filter((id) => id !== pointId) : [...prev, pointId],
      );
    }

    setLastClickedIndex(pointIndex);
  };

  const handleSelectAll = () => {
    const allPointIds = points.map((p) => p.id);
    setSelectedPointIds(allPointIds);
  };

  const handleDeselectAll = () => {
    setSelectedPointIds([]);
  };

  const handleEnterSharingMode = () => {
    setSharingModeActive(true);
  };

  const handleExitSharingMode = () => {
    setSharingModeActive(false);
    setSelectedPointIds([]);
    setLastClickedIndex(null);
  };

  const handleShareSelected = () => {
    setIsSharePanelOpen(true);
  };

  const handleShare = async (usernames: string[], permissionLevel: string) => {
    setError("");

    try {
      const result = await batchSharePoints({
        point_ids: selectedPointIds,
        usernames,
        permission_level: permissionLevel as "view" | "edit" | "manage",
      });

      // Show success/error summary
      const messages = [];

      if (result.success_count > 0) {
        messages.push(`${result.success_count} shared successfully`);
      }

      if (result.already_shared_count > 0) {
        messages.push(`${result.already_shared_count} already shared`);
      }

      if (result.error_count > 0) {
        messages.push(`${result.error_count} failed`);
      }

      if (messages.length > 0) {
        alert(messages.join(", "));
      } else {
        alert("No changes made");
      }

      // Close panel, clear selection, and exit sharing mode
      setIsSharePanelOpen(false);
      setSelectedPointIds([]);
      setSharingModeActive(false);
      setLastClickedIndex(null);
    } catch (err: unknown) {
      // Check if this is a batch share response with detailed results
      type BatchShareErrorResult = { status?: string; error?: string };
      type BatchShareErrorShape = {
        response?: { data?: { results?: BatchShareErrorResult[] } };
      };

      const maybe = err as BatchShareErrorShape;
      const results = maybe?.response?.data?.results;

      if (results && Array.isArray(results)) {
        const errorResults = results.filter(
          (r: BatchShareErrorResult) => r.status === "error",
        );

        if (errorResults.length > 0) {
          // Get unique error messages
          const errorMessages = new Set<string>();
          errorResults.forEach((r: BatchShareErrorResult) => {
            if (r.error) errorMessages.add(r.error);
          });

          const errorText = Array.from(errorMessages).join("; ");
          alert(`Error sharing points: ${errorText}`);
        } else {
          alert("Error sharing points: Failed to share points");
        }
      } else {
        const errorMsg = getErrorMessage(err);
        alert(`Error sharing points: ${errorMsg}`);
      }
    }
  };

  const formatDate = (dateString: string) => {
    const locale = t("common.locale", "en-US");
    return new Date(dateString).toLocaleDateString(locale, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (isInitialLoad) {
    return (
      <LoadingSpinner
        size="large"
        message={t("points.loadingPoints", "Loading points...")}
      />
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>{t("points.errorLoading", "Error loading points")}</h2>
        <p>{error}</p>
        <button onClick={loadPoints} className="btn-primary">
          {t("common.retry", "Retry")}
        </button>
      </div>
    );
  }

  return (
    <div className="points-list-page">
      <div className="points-list-header">
        <h1>{t("nav.points", "Points")}</h1>

        {/* Search and Filters */}
        <div className="filters-container">
          {/* Search Bar */}
          <form onSubmit={handleSearchSubmit} className="search-form">
            <input
              type="text"
              className="search-input"
              placeholder={t(
                "points.searchPlaceholder",
                "Search points by title or description...",
              )}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
            <button type="submit" className="search-button">
              🔍 {t("common.search", "Search")}
            </button>
            {searchQuery && (
              <button
                type="button"
                onClick={clearFilters}
                className="clear-button"
              >
                ✕
              </button>
            )}
          </form>

          {/* Filter Button */}
          {(availableTags.length > 0 || availableTypes.length > 0) && (
            <button
              type="button"
              className={`filter-toggle-button ${isFilterPanelOpen ? "active" : ""}`}
              onClick={handleOpenFilterPanel}
              title={t("points.filterByTagsTypes", "Filter by tags and types")}
            >
              🔍 {t("common.filter", "Filters")}{" "}
              {selectedTagNames.length + selectedTypeIds.length > 0 &&
                `(${selectedTagNames.length + selectedTypeIds.length})`}
              {isLoading && <span className="loading-indicator">⟳</span>}
            </button>
          )}
        </div>

        {/* Filter Panel (Drawer) */}
        <FilterPanel
          isOpen={isFilterPanelOpen}
          availableTags={availableTags}
          availableTypes={availableTypes}
          selectedTags={selectedTagNames}
          selectedTypes={selectedTypeIds}
          onClose={handleCloseFilterPanel}
          onToggleTag={handleToggleTag}
          onToggleType={handleToggleType}
          onClearAll={handleClearFilters}
        />

        {/* Results Info */}
        {(searchQuery || tagsFilter || typesFilter) && (
          <div className="results-info">
            {searchQuery && (
              <span>
                {t("common.search", "Search")}: <strong>"{searchQuery}"</strong>
              </span>
            )}
            {tagsFilter && (
              <span>
                {t("nav.tags", "Tags")}: <strong>{tagsFilter}</strong>
              </span>
            )}
            {typesFilter && (
              <span>
                {t("points.typeFilter", "Type Filter")}:{" "}
                <strong>{t("points.active", "Active")}</strong>
              </span>
            )}
            <span className="results-count">
              {points.length}{" "}
              {points.length === 1
                ? t("points.result", "result")
                : t("points.results", "results")}
            </span>
            <button onClick={clearFilters} className="clear-filters-link">
              {t("points.clearAllFilters", "Clear all filters")}
            </button>
          </div>
        )}

        <div className="points-list-stats">
          <span>
            {points.length}{" "}
            {points.length !== 1
              ? t("map.points", "points")
              : t("map.point", "point")}
          </span>
          {!sharingModeActive && points.length > 0 && (
            <button
              onClick={handleEnterSharingMode}
              className="btn-primary btn-share-mode"
            >
              Share Points
            </button>
          )}
        </div>

        {/* Selection Toolbar */}
        {points.length > 0 && sharingModeActive && (
          <div className="selection-toolbar">
            <div className="selection-actions">
              <button onClick={handleSelectAll} className="btn-select">
                Select All
              </button>
              <button onClick={handleDeselectAll} className="btn-select">
                Deselect All
              </button>
              {selectedPointIds.length > 0 && (
                <span className="selection-count">
                  {selectedPointIds.length} selected
                </span>
              )}
              <button
                onClick={handleShareSelected}
                className="btn-toolbar btn-toolbar-primary"
                disabled={selectedPointIds.length === 0}
              >
                Share Selected
              </button>
              <button
                onClick={handleExitSharingMode}
                className="btn-toolbar btn-toolbar-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {points.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📍</div>
          <h2>{t("points.noPoints", "No points yet")}</h2>
          <p>
            {t(
              "points.noPointsDesc",
              "Click on the map to create your first GPS point",
            )}
          </p>
          <button onClick={() => navigate("/")} className="btn-primary">
            {t("points.goToMap", "Go to Map")}
          </button>
        </div>
      ) : (
        <div className="points-grid">
          {points.map((point, index) => (
            <div
              key={point.id}
              className={`point-card ${selectedPointIds.includes(point.id) ? "selected" : ""} ${sharingModeActive ? "sharing-mode" : ""}`}
              onClick={(e) => {
                if (sharingModeActive) {
                  handleTogglePoint(index, e);
                } else {
                  navigate(`/points/${point.id}`);
                }
              }}
            >
              <div className="point-card-header">
                <h3 className="point-card-title">
                  {point.title || "Untitled Point"}
                </h3>
                <div className="point-badges">
                  {point.is_public && (
                    <span className="point-badge public">🌐 Public</span>
                  )}
                  {!point.shared_by && point.share_count > 0 && (
                    <span
                      className="point-badge shared"
                      title={`Shared with ${point.share_count} user${point.share_count !== 1 ? "s" : ""}`}
                    >
                      🤝 {point.share_count}
                    </span>
                  )}
                </div>
              </div>

              <div className="point-card-location">
                📍 {point.latitude.toFixed(6)}, {point.longitude.toFixed(6)}
              </div>

              {point.type && (
                <div className="point-card-type">
                  🏷️{" "}
                  {point.type.names[language] ||
                    point.type.names[point.type.creation_language]}
                </div>
              )}

              {point.description && (
                <p className="point-card-description">
                  {point.description.length > 100
                    ? `${point.description.substring(0, 100)}...`
                    : point.description}
                </p>
              )}

              {point.tags && point.tags.length > 0 && (
                <div className="point-card-tags">
                  {point.tags.slice(0, 3).map((tag) => (
                    <span key={tag.id} className="tag">
                      {tag.name}
                    </span>
                  ))}
                  {point.tags.length > 3 && (
                    <span className="tag-more">+{point.tags.length - 3}</span>
                  )}
                </div>
              )}

              <div className="point-card-footer">
                <span className="point-card-date">
                  📅 {formatDate(point.created_at)}
                </span>
                {point.annotation_count !== undefined && (
                  <span className="point-card-annotations">
                    📝 {point.annotation_count} annotation
                    {point.annotation_count !== 1 ? "s" : ""}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Share Panel */}
      <SharePanel
        isOpen={isSharePanelOpen}
        selectedPointIds={selectedPointIds}
        onClose={() => setIsSharePanelOpen(false)}
        onShare={handleShare}
      />
    </div>
  );
}
