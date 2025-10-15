/**
 * Point detail component.
 *
 * Displays point details with annotations and edit functionality.
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPoint, deletePoint, acquireLock, releaseLock } from '../../api/points';
import { getErrorMessage } from '../../api/client';
import { LoadingSpinner } from '../common/LoadingSpinner';
import type { GPSPoint } from '../../types/point';

interface PointDetailProps {
  pointId?: string;
  onEdit?: (point: GPSPoint) => void;
  onDelete?: () => void;
}

/**
 * Point detail component.
 */
export function PointDetail({ pointId: propPointId, onEdit, onDelete }: PointDetailProps) {
  const { id: paramPointId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const pointId = propPointId || paramPointId;

  const [point, setPoint] = useState<GPSPoint | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [hasLock, setHasLock] = useState(false);

  /**
   * Load point on mount.
   */
  useEffect(() => {
    if (pointId) {
      loadPoint();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pointId]);

  /**
   * Load point from API.
   */
  const loadPoint = async () => {
    if (!pointId) return;

    setIsLoading(true);
    setError('');

    try {
      const data = await getPoint(pointId);
      setPoint(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle edit click.
   */
  const handleEdit = async () => {
    if (!point || !pointId) return;

    try {
      // Try to acquire lock
      await acquireLock(pointId);
      setHasLock(true);

      if (onEdit) {
        onEdit(point);
      } else {
        // Navigate to edit mode or show edit form
        console.log('Edit mode:', point);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /**
   * Handle delete click.
   */
  const handleDelete = async () => {
    if (!point || !pointId) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete "${point.title}"? It will be moved to trash.`
    );

    if (!confirmed) return;

    setIsDeleting(true);

    try {
      await deletePoint(pointId);

      if (onDelete) {
        onDelete();
      } else {
        navigate('/map');
      }
    } catch (err) {
      setError(getErrorMessage(err));
      setIsDeleting(false);
    }
  };

  /**
   * Release lock on unmount.
   */
  useEffect(() => {
    return () => {
      if (hasLock && pointId) {
        releaseLock(pointId).catch(console.error);
      }
    };
  }, [hasLock, pointId]);

  /**
   * Format date.
   */
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return <LoadingSpinner size="large" message="Loading point..." />;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error loading point</h2>
        <p className="error-message">{error}</p>
        <button onClick={loadPoint} className="btn btn-primary">
          Retry
        </button>
      </div>
    );
  }

  if (!point) {
    return (
      <div className="empty-state">
        <p>Point not found</p>
      </div>
    );
  }

  return (
    <div className="point-detail">
      {/* Header */}
      <div className="point-detail-header">
        <div className="point-detail-title-section">
          <h1>{point.title}</h1>
          {point.is_public && (
            <span className="badge badge-public">Public</span>
          )}
          {point.editing_lock_user && (
            <span className="badge badge-locked">
              Locked by {point.editing_lock_user.email}
            </span>
          )}
        </div>

        <div className="point-detail-actions">
          <button
            onClick={handleEdit}
            className="btn btn-secondary"
            disabled={!!point.editing_lock_user && !hasLock}
          >
            Edit
          </button>
          <button
            onClick={handleDelete}
            className="btn btn-danger"
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>

      {/* Description */}
      {point.description && (
        <div className="point-detail-section">
          <h2>Description</h2>
          <div
            className="point-description"
            dangerouslySetInnerHTML={{ __html: point.description }}
          />
        </div>
      )}

      {/* Location */}
      <div className="point-detail-section">
        <h2>Location</h2>
        <div className="point-coordinates">
          <div className="coordinate-item">
            <span className="coordinate-label">Latitude:</span>
            <span className="coordinate-value">{point.latitude.toFixed(6)}</span>
          </div>
          <div className="coordinate-item">
            <span className="coordinate-label">Longitude:</span>
            <span className="coordinate-value">{point.longitude.toFixed(6)}</span>
          </div>
        </div>
      </div>

      {/* Tags */}
      {point.tags.length > 0 && (
        <div className="point-detail-section">
          <h2>Tags</h2>
          <div className="point-tags">
            {point.tags.map((tag) => (
              <span key={tag.id} className="tag">
                {tag.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="point-detail-section">
        <h2>Information</h2>
        <div className="point-metadata">
          <div className="metadata-item">
            <span className="metadata-label">Owner:</span>
            <span className="metadata-value">{point.owner.email}</span>
          </div>
          <div className="metadata-item">
            <span className="metadata-label">Annotations:</span>
            <span className="metadata-value">{point.annotation_count}</span>
          </div>
          <div className="metadata-item">
            <span className="metadata-label">Created:</span>
            <span className="metadata-value">{formatDate(point.created_at)}</span>
          </div>
          <div className="metadata-item">
            <span className="metadata-label">Updated:</span>
            <span className="metadata-value">{formatDate(point.updated_at)}</span>
          </div>
        </div>
      </div>

      {/* Annotations section - to be implemented */}
      <div className="point-detail-section">
        <h2>Annotations ({point.annotation_count})</h2>
        <p className="text-muted">Annotation components will be added here</p>
      </div>
    </div>
  );
}
