/**
 * Point Sharing Management Page.
 *
 * Allows the point owner to manage who has access to the point.
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getPoint } from "../api/points";
import { getPointShares, deleteShare, updateShare } from "../api/sharing";
import { batchSharePoints } from "../api/friends";
import { getErrorMessage } from "../api/client";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { SharePanel } from "../components/sharing/SharePanel";
import type { GPSPoint } from "../types/point";
import type { Share } from "../api/sharing";
import "./PointSharingPage.css";

export function PointSharingPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [point, setPoint] = useState<GPSPoint | null>(null);
  const [shares, setShares] = useState<Share[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [isSharePanelOpen, setIsSharePanelOpen] = useState(false);
  const [isUnsharing, setIsUnsharing] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState<string | null>(null);

  const loadData = async () => {
    if (!id) return;

    setIsLoading(true);
    setError("");

    try {
      const [pointData, sharesData] = await Promise.all([
        getPoint(id),
        getPointShares(id),
      ]);

      setPoint(pointData);
      setShares(sharesData);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleUnshare = async (share: Share) => {
    const recipientName =
      share.recipient_user?.username || share.recipient_email;

    if (
      !confirm(
        `Are you sure you want to unshare this point with ${recipientName}?`
      )
    ) {
      return;
    }

    setIsUnsharing(share.id);

    try {
      await deleteShare(share.id);
      // Reload shares to reflect the change
      const updatedShares = await getPointShares(id!);
      setShares(updatedShares);
    } catch (err) {
      alert(`Error unsharing: ${getErrorMessage(err)}`);
    } finally {
      setIsUnsharing(null);
    }
  };

  const handlePermissionChange = async (share: Share, newPermission: string) => {
    setIsUpdating(share.id);

    try {
      await updateShare(share.id, {
        permission_level: newPermission as "view" | "edit" | "manage",
      });
      // Reload shares to reflect the change
      const updatedShares = await getPointShares(id!);
      setShares(updatedShares);
    } catch (err) {
      alert(`Error updating permission: ${getErrorMessage(err)}`);
    } finally {
      setIsUpdating(null);
    }
  };

  const handleShare = async (usernames: string[], permissionLevel: string) => {
    if (!id) return;

    setError("");

    try {
      const result = await batchSharePoints({
        point_ids: [id],
        usernames,
        permission_level: permissionLevel as "view" | "edit" | "manage",
      });

      // Show success/error summary
      if (result.error_count === 0) {
        alert(`Successfully shared with ${result.success_count} user(s)`);
      } else if (result.success_count === 0) {
        alert(`Failed to share: ${result.error_count} errors`);
      } else {
        alert(
          `Partially successful: ${result.success_count} succeeded, ${result.error_count} failed`
        );
      }

      // Close panel and reload shares
      setIsSharePanelOpen(false);
      const updatedShares = await getPointShares(id);
      setShares(updatedShares);
    } catch (err) {
      setError(getErrorMessage(err));
      alert(`Error sharing point: ${getErrorMessage(err)}`);
    }
  };

  if (isLoading) {
    return (
      <LoadingSpinner size="large" message="Loading sharing settings..." />
    );
  }

  if (error || !point || !id) {
    return (
      <div className="error-container">
        <h2>Error loading point</h2>
        <p>{error || "Point not found"}</p>
        <button onClick={() => navigate(`/points/${id}`)} className="btn-primary">
          Back to Point
        </button>
      </div>
    );
  }

  // Check if user owns this point
  if (point.shared_by) {
    return (
      <div className="error-container">
        <h2>Access Denied</h2>
        <p>Only the point owner can manage sharing.</p>
        <button onClick={() => navigate(`/points/${id}`)} className="btn-primary">
          Back to Point
        </button>
      </div>
    );
  }

  return (
    <div className="point-sharing-page">
      {/* Header */}
      <div className="sharing-header">
        <button
          onClick={() => navigate(`/points/${id}`)}
          className="btn-ghost back-button"
        >
          ← Back to Point
        </button>

        <div className="header-content">
          <h1>Manage Sharing</h1>
          <h2 className="point-title">{point.title || "Untitled Point"}</h2>
        </div>

        <button
          onClick={() => setIsSharePanelOpen(true)}
          className="btn-primary"
        >
          🤝 Share with More Users
        </button>
      </div>

      {/* Current Shares */}
      <div className="shares-section">
        <h3>Shared With ({shares.length})</h3>

        {shares.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🔒</div>
            <p>This point is not shared with anyone yet.</p>
            <p className="empty-hint">
              Click "Share with More Users" to share this point with friends.
            </p>
          </div>
        ) : (
          <div className="shares-table">
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Permission</th>
                  <th>Shared On</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {shares.map((share) => (
                  <tr key={share.id}>
                    <td className="username-cell">
                      {share.recipient_user?.username || (
                        <span className="text-muted">Not registered</span>
                      )}
                    </td>
                    <td>
                      <select
                        value={share.permission_level}
                        onChange={(e) => handlePermissionChange(share, e.target.value)}
                        className={`permission-select ${share.permission_level}`}
                        disabled={isUpdating === share.id}
                      >
                        <option value="view">View</option>
                        <option value="edit">Edit</option>
                        <option value="manage">Manage</option>
                      </select>
                    </td>
                    <td className="date-cell">
                      {new Date(share.created_at).toLocaleDateString()}
                    </td>
                    <td className="actions-cell">
                      <button
                        onClick={() => handleUnshare(share)}
                        className="btn-small btn-danger"
                        disabled={isUnsharing === share.id || isUpdating === share.id}
                      >
                        {isUnsharing === share.id ? "Unsharing..." : "Unshare"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Share Panel */}
      <SharePanel
        isOpen={isSharePanelOpen}
        selectedPointIds={[id]}
        onClose={() => setIsSharePanelOpen(false)}
        onShare={handleShare}
      />
    </div>
  );
}
