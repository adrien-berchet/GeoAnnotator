/**
 * Auto-Share Rule Form Component
 *
 * Form for creating new auto-share rules with a friend
 */

import { useState, useEffect } from "react";
import { getPointTypes } from "../../api/types";
import { getTags } from "../../api/points";
import type { PointType, Tag } from "../../types/point";
import type { CreateAutoShareRuleRequest } from "../../api/friends";
import { getErrorMessage } from "../../api/client";
import "./AutoShareRuleForm.css";

interface AutoShareRuleFormProps {
  onSubmit: (request: CreateAutoShareRuleRequest) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function AutoShareRuleForm({
  onSubmit,
  onCancel,
  isSubmitting = false,
}: AutoShareRuleFormProps) {
  const [permissionLevel, setPermissionLevel] = useState<
    "view" | "edit" | "manage"
  >("view");
  const [shareAll, setShareAll] = useState(false);
  const [selectedTypeIds, setSelectedTypeIds] = useState<string[]>([]);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);

  const [pointTypes, setPointTypes] = useState<PointType[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);

  const [isLoadingTypes, setIsLoadingTypes] = useState(true);
  const [isLoadingTags, setIsLoadingTags] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadPointTypes();
    loadTags();
  }, []);

  const loadPointTypes = async () => {
    setIsLoadingTypes(true);
    try {
      const data = await getPointTypes();
      setPointTypes(data);
    } catch (err) {
      console.error("Failed to load point types:", err);
    } finally {
      setIsLoadingTypes(false);
    }
  };

  const loadTags = async () => {
    setIsLoadingTags(true);
    try {
      const data = await getTags();
      setTags(data);
    } catch (err) {
      console.error("Failed to load tags:", err);
    } finally {
      setIsLoadingTags(false);
    }
  };

  const handleToggleType = (typeId: string) => {
    setSelectedTypeIds((prev) =>
      prev.includes(typeId)
        ? prev.filter((id) => id !== typeId)
        : [...prev, typeId],
    );
  };

  const handleToggleTag = (tagId: string) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId)
        ? prev.filter((id) => id !== tagId)
        : [...prev, tagId],
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (
      !shareAll &&
      selectedTypeIds.length === 0 &&
      selectedTagIds.length === 0
    ) {
      setError(
        "Please select at least one point type or tag, or enable 'Share All'",
      );
      return;
    }

    if (shareAll && (selectedTypeIds.length > 0 || selectedTagIds.length > 0)) {
      setError("Cannot specify filters when 'Share All' is enabled");
      return;
    }

    const request: CreateAutoShareRuleRequest = {
      permission_level: permissionLevel,
      share_all: shareAll,
      ...(selectedTypeIds.length > 0 && { point_type_ids: selectedTypeIds }),
      ...(selectedTagIds.length > 0 && { tag_ids: selectedTagIds }),
      match_all_tags: true, // Always use AND logic as per requirements
      is_active: true,
    };

    try {
      await onSubmit(request);
      // Reset form on success
      setShareAll(false);
      setSelectedTypeIds([]);
      setSelectedTagIds([]);
      setPermissionLevel("view");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleShareAllChange = (checked: boolean) => {
    setShareAll(checked);
    // Clear selections when enabling share all
    if (checked) {
      setSelectedTypeIds([]);
      setSelectedTagIds([]);
    }
  };

  const isLoading = isLoadingTypes || isLoadingTags;

  return (
    <form className="auto-share-rule-form" onSubmit={handleSubmit}>
      {/* Permission Level */}
      <div className="form-section">
        <label className="form-label">Permission Level</label>
        <div className="permission-options">
          <label className="permission-option">
            <input
              type="radio"
              name="permission"
              value="view"
              checked={permissionLevel === "view"}
              onChange={() => setPermissionLevel("view")}
              disabled={isSubmitting}
            />
            <div className="permission-details">
              <strong>View</strong>
              <span>Can view point</span>
            </div>
          </label>
          <label className="permission-option">
            <input
              type="radio"
              name="permission"
              value="edit"
              checked={permissionLevel === "edit"}
              onChange={() => setPermissionLevel("edit")}
              disabled={isSubmitting}
            />
            <div className="permission-details">
              <strong>Edit</strong>
              <span>Can view and edit point</span>
            </div>
          </label>
          <label className="permission-option">
            <input
              type="radio"
              name="permission"
              value="manage"
              checked={permissionLevel === "manage"}
              onChange={() => setPermissionLevel("manage")}
              disabled={isSubmitting}
            />
            <div className="permission-details">
              <strong>Manage</strong>
              <span>Can manage and share point</span>
            </div>
          </label>
        </div>
      </div>

      {/* Share All Checkbox */}
      <div className="form-section">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={shareAll}
            onChange={(e) => handleShareAllChange(e.target.checked)}
            disabled={isSubmitting}
          />
          <span>Share all new points</span>
        </label>
        <p className="form-help">
          When enabled, all newly created points will be automatically shared
          with this friend
        </p>
      </div>

      {/* Point Types Selection */}
      {!shareAll && (
        <div className="form-section">
          <label className="form-label">Point Types (optional)</label>
          <p className="form-help">
            Select types to auto-share. If selected, points must match one of
            these types
          </p>
          {isLoadingTypes ? (
            <p className="loading-text">Loading types...</p>
          ) : pointTypes.length === 0 ? (
            <p className="empty-text">No point types available</p>
          ) : (
            <div className="checkbox-grid">
              {pointTypes.map((type) => (
                <label key={type.id} className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={selectedTypeIds.includes(type.id)}
                    onChange={() => handleToggleType(type.id)}
                    disabled={isSubmitting}
                  />
                  <span className="checkbox-label-text">
                    {type.icon} {type.names.en || Object.values(type.names)[0]}
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tags Selection */}
      {!shareAll && (
        <div className="form-section">
          <label className="form-label">Tags (optional)</label>
          <p className="form-help">
            Select tags to auto-share. Points must have ALL selected tags (AND
            logic)
          </p>
          {isLoadingTags ? (
            <p className="loading-text">Loading tags...</p>
          ) : tags.length === 0 ? (
            <p className="empty-text">No tags available</p>
          ) : (
            <div className="checkbox-grid">
              {tags.map((tag) => (
                <label key={tag.id} className="checkbox-item">
                  <input
                    type="checkbox"
                    checked={selectedTagIds.includes(tag.id)}
                    onChange={() => handleToggleTag(tag.id)}
                    disabled={isSubmitting}
                  />
                  <span className="checkbox-label-text">{tag.name}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && <div className="error-message">{error}</div>}

      {/* Actions */}
      <div className="form-actions">
        <button
          type="button"
          className="btn-secondary"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="btn-primary"
          disabled={isSubmitting || isLoading}
        >
          {isSubmitting ? "Creating..." : "Create Rule"}
        </button>
      </div>
    </form>
  );
}
