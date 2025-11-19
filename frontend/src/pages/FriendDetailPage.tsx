/**
 * Friend Detail Page
 *
 * Shows details of a specific friend and points shared with them.
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getFriendDetail, removeFriend, type FriendDetail } from "../api/friends";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { useLanguage } from "../contexts/LanguageContext";
import { getPointTypeName } from "../utils/pointTypeUtils";
import "./FriendDetailPage.css";

export function FriendDetailPage() {
  const { friendId } = useParams<{ friendId: string }>();
  const [friendDetail, setFriendDetail] = useState<FriendDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [isRemoving, setIsRemoving] = useState(false);
  const navigate = useNavigate();
  const { language } = useLanguage();

  const loadFriendDetail = async () => {
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
  };

  useEffect(() => {
    loadFriendDetail();
  }, [friendId]);

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
          <span className="stat-value">{friendDetail.shares_received_count}</span>
          <span className="stat-label">Points received from them</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{totalShares}</span>
          <span className="stat-label">Total shared points</span>
        </div>
      </div>

      {/* Shared Points List */}
      <div className="shared-points-section">
        <h2>Points Shared with {friendDetail.username}</h2>

        {friendDetail.shared_points.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📍</div>
            <h3>No points shared yet</h3>
            <p>
              You haven't shared any points with {friendDetail.username}.
            </p>
            <button
              onClick={() => navigate("/points")}
              className="btn-primary"
            >
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
                        <div className="tags-list">
                          {point.tags.slice(0, 2).map((tag) => (
                            <span key={tag.id} className="tag-badge">
                              {tag.name}
                            </span>
                          ))}
                          {point.tags.length > 2 && (
                            <span className="tag-more">
                              +{point.tags.length - 2}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-muted">No tags</span>
                      )}
                    </td>
                    <td className="point-location">
                      {point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}
                    </td>
                    <td className="point-date">{formatDate(point.created_at)}</td>
                    <td className="point-actions">
                      <button
                        onClick={() => navigate(`/points/${point.id}`)}
                        className="btn-small btn-primary"
                      >
                        View Details
                      </button>
                      <button
                        onClick={() => {
                          // TODO: Implement unshare functionality
                          console.log("Unshare point:", point.id);
                        }}
                        className="btn-small btn-danger"
                      >
                        Unshare
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
        <div className="dialog-backdrop" onClick={() => setShowRemoveDialog(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h2>Remove {friendDetail.username}?</h2>
            <p>
              This will remove {friendDetail.username} from your friends list and
              revoke all shared points in both directions.
            </p>
            <div className="dialog-stats">
              <p>
                <strong>{friendDetail.shares_sent_count}</strong> points you shared
                with them will be unshared
              </p>
              <p>
                <strong>{friendDetail.shares_received_count}</strong> points they
                shared with you will be unshared
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
