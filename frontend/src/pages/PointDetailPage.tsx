/**
 * Point detail page.
 *
 * Displays point information with annotations management.
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPoint, deletePoint } from '../api/points';
import { getAnnotations } from '../api/annotations';
import { getErrorMessage } from '../api/client';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { AnnotationForm } from '../components/annotations/AnnotationForm';
import { AnnotationsList } from '../components/annotations/AnnotationsList';
import type { GPSPoint } from '../types/point';
import type { Annotation } from '../types/annotation';
import './PointDetailPage.css';

export function PointDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [point, setPoint] = useState<GPSPoint | null>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (id) {
      loadPointData();
    }
  }, [id]);

  const loadPointData = async () => {
    if (!id) return;

    setIsLoading(true);
    setError('');

    try {
      const [pointData, annotationsData] = await Promise.all([
        getPoint(id),
        getAnnotations(id),
      ]);

      setPoint(pointData);
      setAnnotations(annotationsData);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnnotationCreated = (annotation: Annotation) => {
    setAnnotations([...annotations, annotation]);
  };

  const handleAnnotationDeleted = (annotationId: string) => {
    setAnnotations(annotations.filter((a) => a.id !== annotationId));
  };

  const handleDeletePoint = async () => {
    if (!id || !point) return;

    if (!confirm(`Are you sure you want to delete "${point.title || 'this point'}"?`)) {
      return;
    }

    setIsDeleting(true);

    try {
      await deletePoint(id);
      navigate('/points');
    } catch (err) {
      alert(getErrorMessage(err));
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
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

  if (error || !point || !id) {
    return (
      <div className="error-container">
        <h2>Error loading point</h2>
        <p>{error || 'Point not found'}</p>
        <button onClick={() => navigate('/points')} className="btn-primary">
          Back to Points
        </button>
      </div>
    );
  }

  return (
    <div className="point-detail-page">
      {/* Header */}
      <div className="point-detail-header">
        <button onClick={() => navigate('/points')} className="back-button">
          ← Back to Points
        </button>
        <div className="header-actions">
          <button onClick={() => navigate(`/points/${id}/edit`)} className="btn-secondary">
            ✏️ Edit
          </button>
          <button
            onClick={handleDeletePoint}
            className="btn-danger"
            disabled={isDeleting}
          >
            {isDeleting ? '🗑️ Deleting...' : '🗑️ Delete'}
          </button>
        </div>
      </div>

      {/* Point Info */}
      <div className="point-info-card">
        <div className="point-info-header">
          <h1>{point.title || 'Untitled Point'}</h1>
          {point.is_public && <span className="public-badge">🌐 Public</span>}
        </div>

        <div className="point-metadata">
          <div className="metadata-item">
            <span className="metadata-label">📍 Location</span>
            <span className="metadata-value">
              {point.latitude.toFixed(6)}, {point.longitude.toFixed(6)}
            </span>
          </div>

          <div className="metadata-item">
            <span className="metadata-label">📅 Created</span>
            <span className="metadata-value">{formatDate(point.created_at)}</span>
          </div>

          {point.updated_at !== point.created_at && (
            <div className="metadata-item">
              <span className="metadata-label">🔄 Updated</span>
              <span className="metadata-value">{formatDate(point.updated_at)}</span>
            </div>
          )}
        </div>

        {point.description && (
          <div className="point-description">
            <h3>Description</h3>
            <p>{point.description}</p>
          </div>
        )}

        {point.tags && point.tags.length > 0 && (
          <div className="point-tags">
            <h3>Tags</h3>
            <div className="tags-list">
              {point.tags.map((tag) => (
                <span key={tag.id} className="tag">
                  {tag.name}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Annotations Section */}
      <div className="annotations-section">
        <h2>Annotations ({annotations.length})</h2>

        <div className="annotations-container">
          {/* Add Annotation Form */}
          <div className="add-annotation-section">
            <AnnotationForm
              pointId={id}
              onAnnotationCreated={handleAnnotationCreated}
            />
          </div>

          {/* Annotations List */}
          <div className="annotations-list-section">
            <AnnotationsList
              pointId={id}
              annotations={annotations}
              onAnnotationDeleted={handleAnnotationDeleted}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
