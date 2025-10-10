/**
 * Annotation list component.
 *
 * Displays all annotations for a GPS point with download and delete actions.
 */

import { useState, useEffect } from 'react';
import { getAnnotations, downloadAnnotation, deleteAnnotation } from '../../api/annotations';
import { getErrorMessage } from '../../api/client';
import { LoadingSpinner } from '../common/LoadingSpinner';
import type { Annotation } from '../../types/annotation';

interface AnnotationListProps {
  pointId: string;
  onAnnotationDeleted?: () => void;
}

/**
 * Annotation list component.
 */
export function AnnotationList({ pointId, onAnnotationDeleted }: AnnotationListProps) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  /**
   * Load annotations for the point.
   */
  const loadAnnotations = async () => {
    setIsLoading(true);
    setError('');

    try {
      const data = await getAnnotations(pointId);
      setAnnotations(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle annotation download.
   */
  const handleDownload = async (annotation: Annotation) => {
    try {
      await downloadAnnotation(annotation.id);
    } catch (err) {
      alert(`Download error: ${getErrorMessage(err)}`);
    }
  };

  /**
   * Handle annotation deletion.
   */
  const handleDelete = async (annotationId: string) => {
    if (!confirm('Are you sure you want to delete this annotation?')) {
      return;
    }

    setDeletingId(annotationId);

    try {
      await deleteAnnotation(pointId, annotationId);
      setAnnotations(prev => prev.filter(a => a.id !== annotationId));

      if (onAnnotationDeleted) {
        onAnnotationDeleted();
      }
    } catch (err) {
      alert(`Delete error: ${getErrorMessage(err)}`);
    } finally {
      setDeletingId(null);
    }
  };

  /**
   * Format file size.
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  /**
   * Format date.
   */
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  /**
   * Get annotation icon based on type.
   */
  const getAnnotationIcon = (annotation: Annotation): string => {
    if (annotation.type === 'text') {
      return '📝';
    }
    if (annotation.type === 'image') {
      return '🖼️';
    }
    if (annotation.type === 'document') {
      return '📄';
    }
    return '📎';
  };

  // Load annotations on mount
  useEffect(() => {
    loadAnnotations();
  }, [pointId]);

  if (isLoading) {
    return <LoadingSpinner message="Loading annotations..." />;
  }

  if (error) {
    return (
      <div className="error-message" role="alert">
        Error loading annotations: {error}
        <button onClick={loadAnnotations} className="btn-secondary">
          Retry
        </button>
      </div>
    );
  }

  if (annotations.length === 0) {
    return (
      <div className="empty-state">
        <p>No annotations yet</p>
        <p className="empty-state-hint">
          Upload files or add text notes to this point
        </p>
      </div>
    );
  }

  return (
    <div className="annotation-list">
      <h3>Annotations ({annotations.length})</h3>

      <div className="annotations-grid">
        {annotations.map(annotation => (
          <div key={annotation.id} className="annotation-card">
            <div className="annotation-header">
              <span className="annotation-icon">
                {getAnnotationIcon(annotation)}
              </span>
              <div className="annotation-info">
                <h4>
                  {annotation.type === 'text' ? 'Text Note' : annotation.file_name || 'Untitled'}
                </h4>
                <span className="annotation-type">
                  {annotation.type}
                </span>
              </div>
            </div>

            {annotation.type === 'text' && annotation.text_content && (
              <p className="annotation-description">
                {annotation.text_content.substring(0, 150)}
                {annotation.text_content.length > 150 && '...'}
              </p>
            )}

            <div className="annotation-meta">
              <span className="annotation-date">
                {formatDate(annotation.created_at)}
              </span>
              {annotation.file_size && (
                <span className="annotation-size">
                  {formatFileSize(annotation.file_size)}
                </span>
              )}
            </div>

            <div className="annotation-actions">
              {annotation.file && (
                <button
                  onClick={() => handleDownload(annotation)}
                  className="btn-secondary btn-small"
                >
                  Download
                </button>
              )}
              <button
                onClick={() => handleDelete(annotation.id)}
                disabled={deletingId === annotation.id}
                className="btn-danger btn-small"
              >
                {deletingId === annotation.id ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
