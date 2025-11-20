/**
 * Auto-Share Rules List Component
 *
 * Displays list of auto-share rules for a friend with edit/delete actions
 */

import { useState } from "react";
import type { AutoShareRule, UpdateAutoShareRuleRequest } from "../../api/friends";
import { getErrorMessage } from "../../api/client";
import "./AutoShareRulesList.css";

interface AutoShareRulesListProps {
  rules: AutoShareRule[];
  onUpdateRule: (ruleId: string, request: UpdateAutoShareRuleRequest) => Promise<void>;
  onDeleteRule: (ruleId: string) => Promise<void>;
}

export function AutoShareRulesList({
  rules,
  onUpdateRule,
  onDeleteRule,
}: AutoShareRulesListProps) {
  const [updatingRuleId, setUpdatingRuleId] = useState<string | null>(null);
  const [deletingRuleId, setDeletingRuleId] = useState<string | null>(null);
  const [error, setError] = useState<string>("");

  const handleToggleActive = async (rule: AutoShareRule) => {
    setUpdatingRuleId(rule.id);
    setError("");

    try {
      await onUpdateRule(rule.id, {
        is_active: !rule.is_active,
      });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUpdatingRuleId(null);
    }
  };

  const handleChangePermission = async (rule: AutoShareRule, newPermission: "view" | "edit" | "manage") => {
    if (newPermission === rule.permission_level) return;

    setUpdatingRuleId(rule.id);
    setError("");

    try {
      await onUpdateRule(rule.id, {
        permission_level: newPermission,
      });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUpdatingRuleId(null);
    }
  };

  const handleDelete = async (ruleId: string) => {
    if (!confirm("Are you sure you want to delete this auto-share rule?")) {
      return;
    }

    setDeletingRuleId(ruleId);
    setError("");

    try {
      await onDeleteRule(ruleId);
    } catch (err) {
      setError(getErrorMessage(err));
      setDeletingRuleId(null);
    }
  };

  const getRuleDescription = (rule: AutoShareRule): string => {
    if (rule.share_all) {
      return "All new points";
    }

    const parts: string[] = [];

    if (rule.point_types.length > 0) {
      const typeNames = rule.point_types
        .map((type) => type.names.en || Object.values(type.names)[0])
        .join(", ");
      parts.push(`Types: ${typeNames}`);
    }

    if (rule.tags.length > 0) {
      const tagNames = rule.tags.map((tag) => tag.name).join(", ");
      parts.push(`Tags: ${tagNames}`);
    }

    return parts.length > 0 ? parts.join(" + ") : "No conditions";
  };

  if (rules.length === 0) {
    return (
      <div className="rules-empty">
        <p>No auto-share rules yet</p>
        <p className="rules-empty-hint">
          Create a rule to automatically share newly created points with this
          friend
        </p>
      </div>
    );
  }

  return (
    <div className="rules-list">
      {error && (
        <div className="rules-error">
          {error}
        </div>
      )}

      {rules.map((rule) => {
        const isUpdating = updatingRuleId === rule.id;
        const isDeleting = deletingRuleId === rule.id;
        const isProcessing = isUpdating || isDeleting;

        return (
          <div
            key={rule.id}
            className={`rule-card ${!rule.is_active ? "inactive" : ""}`}
          >
            <div className="rule-header">
              <div className="rule-status">
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={rule.is_active}
                    onChange={() => handleToggleActive(rule)}
                    disabled={isProcessing}
                  />
                  <span className="toggle-slider"></span>
                </label>
                <span className="rule-status-text">
                  {rule.is_active ? "Active" : "Inactive"}
                </span>
              </div>

              <button
                className="btn-delete"
                onClick={() => handleDelete(rule.id)}
                disabled={isProcessing}
                title="Delete rule"
              >
                {isDeleting ? "..." : "🗑"}
              </button>
            </div>

            <div className="rule-body">
              <div className="rule-description">
                {getRuleDescription(rule)}
              </div>

              <div className="rule-permission">
                <label className="rule-permission-label">Permission:</label>
                <select
                  className={`permission-select ${rule.permission_level}`}
                  value={rule.permission_level}
                  onChange={(e) =>
                    handleChangePermission(
                      rule,
                      e.target.value as "view" | "edit" | "manage"
                    )
                  }
                  disabled={isProcessing}
                >
                  <option value="view">View</option>
                  <option value="edit">Edit</option>
                  <option value="manage">Manage</option>
                </select>
              </div>
            </div>

            {rule.share_all && (
              <div className="rule-badge share-all-badge">
                Share All
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
