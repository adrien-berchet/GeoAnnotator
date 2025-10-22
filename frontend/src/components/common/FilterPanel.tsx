/**
 * Filter Panel Component
 *
 * Unified drawer panel for filtering by tags and types
 */

import type { Tag, PointType } from '../../types/point';
import { getPointTypeName } from '../../utils/pointTypeUtils';
import { useLanguage } from '../../contexts/LanguageContext';
import './FilterPanel.css';

interface FilterPanelProps {
  isOpen: boolean;
  availableTags: Tag[];
  availableTypes: PointType[];
  selectedTags: string[];
  selectedTypes: string[];
  onClose: () => void;
  onToggleTag: (tagName: string) => void;
  onToggleType: (typeId: string) => void;
  onClearAll: () => void;
}

export function FilterPanel({
  isOpen,
  availableTags,
  availableTypes,
  selectedTags,
  selectedTypes,
  onClose,
  onToggleTag,
  onToggleType,
  onClearAll,
}: FilterPanelProps) {
  const { language } = useLanguage();
  const hasActiveFilters = selectedTags.length > 0 || selectedTypes.length > 0;

  return (
    <>
      {/* Backdrop */}
      <div
        className={`filter-backdrop ${isOpen ? 'open' : ''}`}
        onClick={onClose}
      />

      {/* Panel */}
      <div className={`filter-panel ${isOpen ? 'open' : ''}`}>
        {/* Header */}
        <div className="filter-header">
          <h2>Filters</h2>
          <button
            className="filter-close"
            onClick={onClose}
            aria-label="Close filter panel"
          >
            ✕
          </button>
        </div>

        {/* Content - Split into two independently scrollable sections */}
        <div className="filter-content">
          {/* Types Section */}
          <div className="filter-section-container">
            <h3 className="filter-section-title">Point Types</h3>
            <div className="filter-section-scroll">
              {availableTypes.length === 0 ? (
                <div className="filter-empty">No types available</div>
              ) : (
                <div className="filter-list">
                  {availableTypes.map((type) => (
                    <button
                      key={type.id}
                      type="button"
                      className={`filter-option ${selectedTypes.includes(type.id) ? 'selected' : ''}`}
                      onClick={() => onToggleType(type.id)}
                    >
                      <span className="filter-checkbox">
                        {selectedTypes.includes(type.id) ? '✓' : ''}
                      </span>
                      {type.icon && type.icon !== '/icons/default.svg' && (
                        type.icon.startsWith('http') || type.icon.startsWith('/') || type.icon.startsWith('data:') ? (
                          <img src={type.icon} alt="" className="filter-type-icon" />
                        ) : (
                          <span className="filter-type-icon-emoji">{type.icon}</span>
                        )
                      )}
                      <span className="filter-name">{getPointTypeName(type, language)}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Tags Section */}
          <div className="filter-section-container">
            <h3 className="filter-section-title">Tags</h3>
            <div className="filter-section-scroll">
              {availableTags.length === 0 ? (
                <div className="filter-empty">No tags available</div>
              ) : (
                <div className="filter-list">
                  {availableTags.map((tag) => (
                    <button
                      key={tag.id}
                      type="button"
                      className={`filter-option ${selectedTags.includes(tag.name) ? 'selected' : ''}`}
                      onClick={() => onToggleTag(tag.name)}
                    >
                      <span className="filter-checkbox">
                        {selectedTags.includes(tag.name) ? '✓' : ''}
                      </span>
                      <span className="filter-name">{tag.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="filter-footer">
          <button
            className="filter-clear"
            onClick={onClearAll}
            disabled={!hasActiveFilters}
          >
            Clear All {hasActiveFilters && `(${selectedTags.length + selectedTypes.length})`}
          </button>
        </div>
      </div>
    </>
  );
}
