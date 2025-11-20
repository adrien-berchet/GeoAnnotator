/**
 * Friend Detail Page
 *
 * Shows details of a specific friend and points shared with them.
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getFriendDetail,
  removeFriend,
  type FriendDetail,
  getAutoShareRules,
  createAutoShareRule,
  updateAutoShareRule,
  deleteAutoShareRule,
  type AutoShareRule,
  type CreateAutoShareRuleRequest,
  type UpdateAutoShareRuleRequest,
} from "../api/friends";
import { updateShare, deleteShare } from "../api/sharing";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { useLanguage } from "../contexts/LanguageContext";
import { getPointTypeName } from "../utils/pointTypeUtils";
import { AutoShareRuleForm } from "../components/sharing/AutoShareRuleForm";
import { AutoShareRulesList } from "../components/sharing/AutoShareRulesList";
import "./FriendDetailPage.css";

export function FriendDetailPage() {
  const { friendId } = useParams<{ friendId: string }>();
  const [friendDetail, setFriendDetail] = useState<FriendDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const [isUpdating, setIsUpdating] = useState<string | null>(null);
  const [isUnsharing, setIsUnsharing] = useState<string | null>(null);

  // Auto-share rules state
  const [autoShareRules, setAutoShareRules] = useState<AutoShareRule[]>([]);
  const [isLoadingRules, setIsLoadingRules] = useState(false);
  const [rulesExpanded, setRulesExpanded] = useState(true);
  const [showRuleForm, setShowRuleForm] = useState(false);
  const [isSubmittingRule, setIsSubmittingRule] = useState(false);

  const navigate = useNavigate();
  const { language } = useLanguage();

  const loadFriendDetail = useCallback(async () => {
    if (!friendId) return;

    setIsLoading(true);
    setError("");

    try {
      const data = await getFriendDetail(friendId);
      setFriendDetail(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, [friendId]);

  const loadAutoShareRules = useCallback(async () => {
    if (!friendId) return;

    setIsLoadingRules(true);

    try {
      const rules = await getAutoShareRules(friendId);
      setAutoShareRules(rules);
    } catch (err) {
      console.error("Failed to load auto-share rules:", err);
    } finally {
      setIsLoadingRules(false);
    }
  }, [friendId]);

  useEffect(() => {
    loadFriendDetail();
    loadAutoShareRules();
  }, [loadFriendDetail, loadAutoShareRules]);

  const handleRemoveFriend = async () => {
    if (!friendId || !friendDetail) return;

    setIsRemoving(true);

    try {
      await removeFriend(friendId);
      navigate("/friends");
    } catch (err) {
      setError(getErrorMessage(err));
      setShowRemoveDialog(false);
    } finally {
      setIsRemoving(false);
    }
  };

  const handlePermissionChange = async (
    shareId: string,
    newPermission: string,
  ) => {
    setIsUpdating(shareId);

    try {
      await updateShare(shareId, {
        permission_level: newPermission as "view" | "edit" | "manage",
      });
      // Reload friend details to reflect the change
      await loadFriendDetail();
    } catch (err) {
      alert(`Error updating permission: ${getErrorMessage(err)}`);
    } finally {
      setIsUpdating(null);
    }
  };

  const handleUnshare = async (point: FriendDetail["shared_points"][0]) => {
    if (
      !confirm(
        `Are you sure you want to unshare "${point.title}" with ${friendDetail?.username}?`,
      )
    ) {
      return;
    }

    setIsUnsharing(point.share_id);

    try {
      await deleteShare(point.share_id);
      // Reload friend details to reflect the change
      await loadFriendDetail();
    } catch (err) {
      alert(`Error unsharing: ${getErrorMessage(err)}`);
    } finally {
      setIsUnsharing(null);
    }
  };

  const handleCreateRule = async (request: CreateAutoShareRuleRequest) => {
    if (!friendId) return;

    setIsSubmittingRule(true);

    try {
      await createAutoShareRule(friendId, request);
      await loadAutoShareRules();
      setShowRuleForm(false);
    } finally {
      setIsSubmittingRule(false);
    }
  };

  const handleUpdateRule = async (
    ruleId: string,
    request: UpdateAutoShareRuleRequest,
  ) => {
    if (!friendId) return;

    await updateAutoShareRule(friendId, ruleId, request);
    await loadAutoShareRules();
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!friendId) return;

    await deleteAutoShareRule(friendId, ruleId);
    await loadAutoShareRules();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (isLoading) {
    return <LoadingSpinner size="large" message="Loading friend details..." />;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error loading friend details</h2>
        <p>{error}</p>
        <button onClick={loadFriendDetail} className="btn-primary">
          Retry
        </button>
        <button onClick={() => navigate("/friends")} className="btn-secondary">
          Back to Friends
        </button>
      </div>
    );
  }

  if (!friendDetail) {
    return null;
  }

  const totalShares =
    friendDetail.shares_sent_count + friendDetail.shares_received_count;

  return (
    <div className="friend-detail-page">
      {/* Header */}
      <div className="friend-detail-header">
        <button onClick={() => navigate("/friends")} className="back-button">
          ← Back to Friends
        </button>

        <div className="friend-header-content">
          <div className="friend-detail-title">
            <div className="friend-avatar-large">
              {friendDetail.username.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1>{friendDetail.username}</h1>
              <p className="friend-since">
                Friends since {formatDate(friendDetail.friendship_created_at)}
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowRemoveDialog(true)}
            className="btn-danger"
          >
            Remove Friend
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div className="friend-stats-row">
        <div className="stat-card">
          <span className="stat-value">{friendDetail.shares_sent_count}</span>
          <span className="stat-label">Points shared with them</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">
            {friendDetail.shares_received_count}
          </span>
          <span className="stat-label">Points received from them</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{totalShares}</span>
          <span className="stat-label">Total shared points</span>
        </div>
      </div>

      {/* Auto-Share Rules Section */}
      <div className="auto-share-rules-section">
        <div className="section-header">
          <h2>
            <button
              className="collapsible-toggle"
              onClick={() => setRulesExpanded(!rulesExpanded)}
            >
              {rulesExpanded ? "▼" : "▶"} Auto-Share Rules{" "}
              {autoShareRules.length > 0 && (
                <span className="rule-count">({autoShareRules.length})</span>
              )}
            </button>
          </h2>
          {rulesExpanded && !showRuleForm && (
            <button
              className="btn-primary"
              onClick={() => setShowRuleForm(true)}
            >
              + Add Rule
            </button>
          )}
        </div>

        {rulesExpanded && (
          <div className="section-content">
            <p className="section-description">
              Automatically share newly created points with{" "}
              {friendDetail.username} based on type and tag filters
            </p>

            {showRuleForm && (
              <div className="rule-form-container">
                <AutoShareRuleForm
                  onSubmit={handleCreateRule}
                  onCancel={() => setShowRuleForm(false)}
                  isSubmitting={isSubmittingRule}
                />
              </div>
            )}

            {isLoadingRules ? (
              <div className="loading-rules">Loading rules...</div>
            ) : (
              <AutoShareRulesList
                rules={autoShareRules}
                onUpdateRule={handleUpdateRule}
                onDeleteRule={handleDeleteRule}
              />
            )}
          </div>
        )}
      </div>

      {/* Shared Points List */}
      <div className="shared-points-section">
        <h2>Points Shared with {friendDetail.username}</h2>

        {friendDetail.shared_points.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📍</div>
            <h3>No points shared yet</h3>
            <p>You haven't shared any points with {friendDetail.username}.</p>
            <button onClick={() => navigate("/points")} className="btn-primary">
              Go to Points
            </button>
          </div>
        ) : (
          <div className="shared-points-table">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Tags</th>
                  <th>Location</th>
                  <th>Permission</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {friendDetail.shared_points.map((point) => (
                  <tr key={point.id}>
                    <td className="point-title">{point.title}</td>
                    <td className="point-type">
                      {point.type && (
                        <span className="type-badge">
                          {point.type.icon &&
                            point.type.icon !== "/icons/default.svg" &&
                            (point.type.icon.startsWith("http") ||
                            point.type.icon.startsWith("/") ||
                            point.type.icon.startsWith("data:") ? (
                              <img
                                src={point.type.icon}
                                alt=""
                                className="type-icon"
                              />
                            ) : (
                              <span className="type-icon-emoji">
                                {point.type.icon}
                              </span>
                            ))}
                          {getPointTypeName(point.type, language)}
                        </span>
                      )}
                    </td>
                    <td className="point-tags">
                      {point.tags.length > 0 ? (
                        point.tags.length <= 2 ? (
                          // Show individual tags if there are 1-2 tags
                          <div className="tags-list">
                            {point.tags.map((tag) => (
                              <span key={tag.id} className="tag-badge">
                                {tag.name}
                              </span>
                            ))}
                          </div>
                        ) : (
                          // Show only count if there are 3+ tags to avoid wrapping
                          <span className="tag-more">
                            {point.tags.length} tags
                          </span>
                        )
                      ) : (
                        <span className="text-muted">No tags</span>
                      )}
                    </td>
                    <td className="point-location">
                      {point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}
                    </td>
                    <td>
                      <select
                        value={point.permission_level}
                        onChange={(e) =>
                          handlePermissionChange(point.share_id, e.target.value)
                        }
                        className={`permission-select ${point.permission_level}`}
                        disabled={isUpdating === point.share_id}
                      >
                        <option value="view">View</option>
                        <option value="edit">Edit</option>
                        <option value="manage">Manage</option>
                      </select>
                    </td>
                    <td className="point-date">
                      {formatDate(point.created_at)}
                    </td>
                    <td className="point-actions">
                      <button
                        onClick={() => navigate(`/points/${point.id}`)}
                        className="btn-small btn-primary"
                      >
                        View Details
                      </button>
                      <button
                        onClick={() => handleUnshare(point)}
                        className="btn-small btn-danger"
                        disabled={
                          isUnsharing === point.share_id ||
                          isUpdating === point.share_id
                        }
                      >
                        {isUnsharing === point.share_id
                          ? "Unsharing..."
                          : "Unshare"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Remove Friend Confirmation Dialog */}
      {showRemoveDialog && (
        <div
          className="dialog-backdrop"
          onClick={() => setShowRemoveDialog(false)}
        >
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h2>Remove {friendDetail.username}?</h2>
            <p>
              This will remove {friendDetail.username} from your friends list
              and revoke all shared points in both directions.
            </p>
            <div className="dialog-stats">
              <p>
                <strong>{friendDetail.shares_sent_count}</strong> points you
                shared with them will be unshared
              </p>
              <p>
                <strong>{friendDetail.shares_received_count}</strong> points
                they shared with you will be unshared
              </p>
            </div>
            <p className="warning-text">This action cannot be undone.</p>
            <div className="dialog-actions">
              <button
                onClick={() => setShowRemoveDialog(false)}
                className="btn-secondary"
                disabled={isRemoving}
              >
                Cancel
              </button>
              <button
                onClick={handleRemoveFriend}
                className="btn-danger"
                disabled={isRemoving}
              >
                {isRemoving ? "Removing..." : "Remove Friend"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
