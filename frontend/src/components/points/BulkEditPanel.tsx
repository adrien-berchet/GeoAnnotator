/**
 * Bulk Edit Panel Component
 *
 * Slide-in drawer for bulk editing points (type, tags, delete)
 */

import { useState, useEffect } from "react";
import { getPointTypes } from "../../api/types";
import { getTags } from "../../api/points";
import { getErrorMessage } from "../../api/client";
import type { PointType, Tag } from "../../types/point";
import { useLanguage } from "../../contexts/LanguageContext";
import "./BulkEditPanel.css";

interface BulkEditPanelProps {
  isOpen: boolean;
  selectedPointIds: string[];
  onClose: () => void;
  onUpdateType: (typeId: string) => void;
  onAddTags: (tags: string[]) => void;
  onDelete: () => void;
}

export function BulkEditPanel({
  isOpen,
  selectedPointIds,
  onClose,
  onUpdateType,
  onAddTags,
  onDelete,
}: BulkEditPanelProps) {
  const { language } = useLanguage();
  const [availableTypes, setAvailableTypes] = useState<PointType[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [selectedTypeId, setSelectedTypeId] = useState<string>("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [newTagsInput, setNewTagsInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen) {
      loadTypesAndTags();
    }
  }, [isOpen]);

  const loadTypesAndTags = async () => {
    setIsLoading(true);
    setError("");

    try {
      const [types, tags] = await Promise.all([getPointTypes(), getTags()]);
      setAvailableTypes(types);
      setAvailableTags(tags);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleTag = (tagName: string) => {
    setSelectedTags((prev) =>
      prev.includes(tagName)
        ? prev.filter((t) => t !== tagName)
        : [...prev, tagName],
    );
  };

  const handleUpdateType = () => {
    if (!selectedTypeId) {
      setError("Please select a type");
      return;
    }
    onUpdateType(selectedTypeId);
    handleClearAll();
  };

  const handleAddTags = () => {
    // Combine selected tags and manually entered tags
    const existingTags = selectedTags;
    const newTags = newTagsInput
      .split(/[,\n]/)
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    const allTags = [...new Set([...existingTags, ...newTags])];

    if (allTags.length === 0) {
      setError("Please select or enter at least one tag");
      return;
    }

    onAddTags(allTags);
    handleClearAll();
  };

  const handleDelete = () => {
    onDelete();
    handleClearAll();
  };

  const handleClearAll = () => {
    setSelectedTypeId("");
    setSelectedTags([]);
    setNewTagsInput("");
    setError("");
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className={`bulk-edit-backdrop ${isOpen ? "open" : ""}`}
        onClick={onClose}
      />

      {/* Panel */}
      <div className={`bulk-edit-panel ${isOpen ? "open" : ""}`}>
        {/* Header */}
        <div className="bulk-edit-header">
          <h2>Bulk Edit Points</h2>
          <button
            className="bulk-edit-close"
            onClick={onClose}
            aria-label="Close bulk edit panel"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="bulk-edit-content">
          {/* Selected Points Info */}
          <div className="bulk-edit-info">
            <p>
              <strong>{selectedPointIds.length}</strong> point
              {selectedPointIds.length !== 1 ? "s" : ""} selected
            </p>
          </div>

          {/* Update Type Section */}
          <div className="bulk-edit-section">
            <h3>Update Type</h3>
            <p className="section-description">
              Set a new type for all selected points
            </p>
            {isLoading ? (
              <div className="loading-message">Loading types...</div>
            ) : availableTypes.length === 0 ? (
              <div className="empty-message">No types available</div>
            ) : (
              <div className="type-selector">
                <select
                  className="type-select"
                  value={selectedTypeId}
                  onChange={(e) => setSelectedTypeId(e.target.value)}
                >
                  <option value="">Select a type...</option>
                  {availableTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.icon}{" "}
                      {type.names[language] ||
                        type.names[type.creation_language]}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleUpdateType}
                  className="btn-action"
                  disabled={!selectedTypeId}
                >
                  Update Type
                </button>
              </div>
            )}
          </div>

          {/* Add Tags Section */}
          <div className="bulk-edit-section">
            <h3>Add Tags</h3>
            <p className="section-description">
              Add tags to all selected points (existing tags will be kept)
            </p>

            {/* Existing Tags */}
            {isLoading ? (
              <div className="loading-message">Loading tags...</div>
            ) : availableTags.length === 0 ? (
              <div className="empty-message">
                No existing tags. Enter new tags below.
              </div>
            ) : (
              <div className="tags-list">
                {availableTags.map((tag) => (
                  <label key={tag.id} className="tag-option">
                    <input
                      type="checkbox"
                      checked={selectedTags.includes(tag.name)}
                      onChange={() => handleToggleTag(tag.name)}
                    />
                    <span className="tag-name">{tag.name}</span>
                  </label>
                ))}
              </div>
            )}

            {/* New Tags Input */}
            <div className="new-tags-section">
              <h4>Add New Tags</h4>
              <p className="section-description">
                Enter tag names separated by commas or new lines
              </p>
              <textarea
                className="tags-textarea"
                placeholder="tag1, tag2&#10;tag3"
                value={newTagsInput}
                onChange={(e) => setNewTagsInput(e.target.value)}
                rows={3}
              />
            </div>

            <button
              onClick={handleAddTags}
              className="btn-action"
              disabled={selectedTags.length === 0 && !newTagsInput.trim()}
            >
              Add Tags
            </button>
          </div>

          {/* Delete Section */}
          <div className="bulk-edit-section bulk-edit-danger">
            <h3>Delete Points</h3>
            <p className="section-description">
              Permanently delete all selected points (they will be moved to
              trash)
            </p>
            <button onClick={handleDelete} className="btn-danger">
              Delete {selectedPointIds.length} Point
              {selectedPointIds.length !== 1 ? "s" : ""}
            </button>
          </div>

          {/* Error Message */}
          {error && <div className="error-message">{error}</div>}
        </div>

        {/* Footer */}
        <div className="bulk-edit-footer">
          <button onClick={handleClearAll} className="btn-secondary">
            Clear All
          </button>
          <button onClick={onClose} className="btn-secondary">
            Close
          </button>
        </div>
      </div>
    </>
  );
}
