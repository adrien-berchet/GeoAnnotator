/**
 * Tag Filter Panel Component
 *
 * Reusable drawer panel for filtering by tags
 */

import type { Tag } from "../../types/point";
import "./TagFilterPanel.css";

interface TagFilterPanelProps {
  isOpen: boolean;
  availableTags: Tag[];
  selectedTags: string[];
  onClose: () => void;
  onToggleTag: (tagName: string) => void;
  onClearAll: () => void;
}

export function TagFilterPanel({
  isOpen,
  availableTags,
  selectedTags,
  onClose,
  onToggleTag,
  onClearAll,
}: TagFilterPanelProps) {
  return (
    <>
      {/* Backdrop */}
      <div
        className={`tag-filter-backdrop ${isOpen ? "open" : ""}`}
        onClick={onClose}
      />

      {/* Panel */}
      <div className={`tag-filter-panel ${isOpen ? "open" : ""}`}>
        {/* Header */}
        <div className="tag-filter-header">
          <h2>Filter by Tags</h2>
          <button
            className="tag-filter-close"
            onClick={onClose}
            aria-label="Close filter panel"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="tag-filter-content">
          {availableTags.length === 0 ? (
            <div className="tag-filter-empty">No tags available</div>
          ) : (
            <div className="tag-filter-list">
              {availableTags.map((tag) => (
                <button
                  key={tag.id}
                  type="button"
                  className={`tag-filter-option ${selectedTags.includes(tag.name) ? "selected" : ""}`}
                  onClick={() => onToggleTag(tag.name)}
                >
                  <span className="tag-filter-checkbox">
                    {selectedTags.includes(tag.name) ? "✓" : ""}
                  </span>
                  <span className="tag-filter-name">{tag.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="tag-filter-footer">
          <button className="tag-filter-clear" onClick={onClearAll}>
            Clear All
          </button>
        </div>
      </div>
    </>
  );
}
