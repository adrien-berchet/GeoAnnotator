/**
 * Annotations list component.
 *
 * Displays all annotations for a point with preview and actions.
 */

import { useState } from 'react';
import { deleteAnnotation, downloadAnnotation, getPreviewUrl } from '../../api/annotations';
import { getErrorMessage } from '../../api/client';
import type { Annotation } from '../../types/annotation';
import './AnnotationsList.css';

interface AnnotationsListProps {
  pointId: string;
  annotations: Annotation[];
  onAnnotationDeleted: (annotationId: string) => void;
  onAnnotationUpdated?: (annotation: Annotation) => void;
}

export function AnnotationsList({
  pointId,
  annotations,
  onAnnotationDeleted,
}: AnnotationsListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const handleDelete = async (annotationId: string) => {
    if (!confirm('Are you sure you want to delete this annotation?')) {
      return;
    }

    setDeletingId(annotationId);
    setError('');

    try {
      await deleteAnnotation(pointId, annotationId);
      onAnnotationDeleted(annotationId);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  };

  const handleDownload = async (annotation: Annotation) => {
    setDownloadingId(annotation.id);
    setError('');

    try {
      const blob = await downloadAnnotation(pointId, annotation.id);
      
      // Create a temporary URL for the blob
      const url = window.URL.createObjectURL(blob);
      
      // Create a temporary link and trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = annotation.file?.file_name || 'download';
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDownloadingId(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  if (annotations.length === 0) {
    return (
      <div className="annotations-empty">
        <div className="empty-icon">📝</div>
        <p>No annotations yet</p>
        <p className="empty-hint">Add your first annotation above</p>
      </div>
    );
  }

  return (
    <div className="annotations-list">
      {error && <div className="error-message">{error}</div>}

      {annotations.map((annotation) => (
        <div key={annotation.id} className="annotation-item">
          <div className="annotation-header">
            <div className="annotation-type-badge">
              {annotation.type === 'text' && '📝 Text'}
              {annotation.type === 'image' && '🖼️ Image'}
              {annotation.type === 'document' && '📄 Document'}
              {annotation.type === 'file' && '📎 File'}
            </div>
            <div className="annotation-date">{formatDate(annotation.created_at)}</div>
          </div>

          <div className="annotation-content">
            {/* Text Annotation */}
            {annotation.type === 'text' && annotation.text_content && (
              <div className="text-annotation">
                <p>{annotation.text_content}</p>
              </div>
            )}

            {/* Image Annotation */}
            {annotation.type === 'image' && annotation.file && (
              <div className="image-annotation">
                <img
                  src={getPreviewUrl(annotation.id)}
                  alt={annotation.file.file_name || 'Image'}
                  className="annotation-image"
                />
                <div className="image-info">
                  {annotation.file.file_name && (
                    <div className="file-info">
                      <span className="file-name">{annotation.file.file_name}</span>
                      {annotation.file.file_size && (
                        <span className="file-size">
                          {formatFileSize(annotation.file.file_size)}
                        </span>
                      )}
                    </div>
                  )}
                  <button
                    onClick={() => handleDownload(annotation)}
                    className="download-button"
                    disabled={downloadingId === annotation.id}
                  >
                    {downloadingId === annotation.id ? '⏳ Downloading...' : '⬇️ Download'}
                  </button>
                </div>
              </div>
            )}

            {/* Document/File Annotation */}
            {(annotation.type === 'document' || annotation.type === 'file') && annotation.file && (
              <div className="file-annotation">
                <div className="file-icon-large">
                  {annotation.type === 'document' ? '📄' : '📎'}
                </div>
                <div className="file-details">
                  <div className="file-name">{annotation.file.file_name || 'Unnamed file'}</div>
                  {annotation.file.mime_type && (
                    <div className="file-type">{annotation.file.mime_type}</div>
                  )}
                  {annotation.file.file_size && (
                    <div className="file-size">{formatFileSize(annotation.file.file_size)}</div>
                  )}
                </div>
                <button
                  onClick={() => handleDownload(annotation)}
                  className="download-button"
                  disabled={downloadingId === annotation.id}
                >
                  {downloadingId === annotation.id ? '⏳ Downloading...' : '⬇️ Download'}
                </button>
              </div>
            )}
          </div>

          <div className="annotation-actions">
            <button
              onClick={() => handleDelete(annotation.id)}
              className="delete-button"
              disabled={deletingId === annotation.id}
            >
              {deletingId === annotation.id ? '🗑️ Deleting...' : '🗑️ Delete'}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
