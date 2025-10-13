/**
 * Shared points list component.
 *
 * Displays all shares for a GPS point with revoke actions.
 */

import { useState, useEffect } from 'react';
import { getPointShares, deleteShare, updateShare } from '../../api/sharing';
import type { Share, UpdateShareData } from '../../api/sharing';
import { getErrorMessage } from '../../api/client';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { PermissionSelector } from './PermissionSelector';
import type { Permission } from '../../types/sharing';

interface SharedPointsListProps {
  pointId: string;
}

/**
 * Shared points list component.
 */
export function SharedPointsList({ pointId }: SharedPointsListProps) {
  const [shares, setShares] = useState<Share[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);

  /**
   * Load shares for the point.
   */
  const loadShares = async () => {
    setIsLoading(true);
    setError('');

    try {
      const data = await getPointShares(pointId);
      setShares(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle permission update.
   */
  const handleUpdatePermission = async (shareId: string, permission: Permission) => {
    setEditingId(shareId);

    try {
      const updatedShare = await updateShare(shareId, {
        permission_level: permission,
      } as UpdateShareData);

      setShares(prev => prev.map(s => s.id === shareId ? updatedShare : s));
      setEditingId(null);
    } catch (err) {
      alert(`Update error: ${getErrorMessage(err)}`);
      setEditingId(null);
    }
  };

  /**
   * Handle share revocation.
   */
  const handleRevoke = async (shareId: string) => {
    if (!confirm('Are you sure you want to revoke this share?')) {
      return;
    }

    setRevokingId(shareId);

    try {
      await deleteShare(shareId);
      setShares(prev => prev.filter(s => s.id !== shareId));
    } catch (err) {
      alert(`Revoke error: ${getErrorMessage(err)}`);
    } finally {
      setRevokingId(null);
    }
  };

  /**
   * Format date.
   */
  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  /**
   * Get share status badge.
   */
  const getStatusBadge = (share: Share): React.ReactNode => {
    if (!share.is_active) {
      return <span className="status-badge inactive">Revoked</span>;
    }
    if (share.accepted_at) {
      return <span className="status-badge active">Active</span>;
    }
    return <span className="status-badge pending">Pending</span>;
  };

  // Load shares on mount
  useEffect(() => {
    loadShares();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pointId]);

  if (isLoading) {
    return <LoadingSpinner message="Loading shares..." />;
  }

  if (error) {
    return (
      <div className="error-message" role="alert">
        Error loading shares: {error}
        <button onClick={loadShares} className="btn-secondary">
          Retry
        </button>
      </div>
    );
  }

  if (shares.length === 0) {
    return (
      <div className="empty-state">
        <p>This point is not shared</p>
        <p className="empty-state-hint">
          Click "Share Point" to invite others
        </p>
      </div>
    );
  }

  return (
    <div className="shared-points-list">
      <h3>Shared With ({shares.length})</h3>

      <div className="shares-table">
        <table>
          <thead>
            <tr>
              <th>User</th>
              <th>Permission</th>
              <th>Status</th>
              <th>Invited</th>
              <th>Accepted</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {shares.map(share => (
              <tr key={share.id} className={!share.is_active ? 'revoked' : ''}>
                <td>
                  <div className="user-info">
                    <strong>{share.recipient_email}</strong>
                    {share.recipient_user && (
                      <small className="user-id">ID: {share.recipient_user.id}</small>
                    )}
                  </div>
                </td>
                <td>
                  {editingId === share.id ? (
                    <PermissionSelector
                      value={share.permission_level}
                      onChange={(permission) => handleUpdatePermission(share.id, permission)}
                      disabled={false}
                    />
                  ) : (
                    <div className="permission-display">
                      <span className="permission-badge">
                        {share.permission_level}
                      </span>
                      {share.is_active && (
                        <button
                          onClick={() => setEditingId(share.id)}
                          className="btn-link btn-small"
                        >
                          Edit
                        </button>
                      )}
                    </div>
                  )}
                </td>
                <td>{getStatusBadge(share)}</td>
                <td>{formatDate(share.invitation_sent_at)}</td>
                <td>{formatDate(share.accepted_at)}</td>
                <td>
                  {share.is_active && (
                    <button
                      onClick={() => handleRevoke(share.id)}
                      disabled={revokingId === share.id}
                      className="btn-danger btn-small"
                    >
                      {revokingId === share.id ? 'Revoking...' : 'Revoke'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
