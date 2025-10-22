/**
 * Image annotation preview component.
 *
 * Displays image thumbnails with metadata and full-size modal.
 */

import { useState } from 'react';
import { getPreviewUrl } from '../../api/annotations';
import type { Annotation } from '../../types/annotation';

interface ImagePreviewProps {
  annotation: Annotation;
}

/**
 * Image annotation preview component.
 */
export function ImagePreview({ annotation }: ImagePreviewProps) {
  const [showModal, setShowModal] = useState(false);
  const [imageError, setImageError] = useState(false);

  if (annotation.type !== 'image' || !annotation.file) {
    return null;
  }

  /**
   * Format file size.
   */
  const formatFileSize = (bytes: number | null): string => {
    if (!bytes) return 'Unknown size';
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

  const previewUrl = getPreviewUrl(annotation.id);

  return (
    <>
      <div className="image-preview">
        <div className="preview-header">
          <span className="preview-icon">🖼️</span>
          <div className="preview-info">
            <h4>{annotation.file.file_name || 'Untitled Image'}</h4>
            <span className="preview-date">
              {formatDate(annotation.created_at)}
            </span>
          </div>
        </div>

        <div
          className="image-thumbnail"
          onClick={() => setShowModal(true)}
        >
          {!imageError ? (
            <img
              src={previewUrl}
              alt={annotation.file.file_name || 'Image preview'}
              onError={() => setImageError(true)}
              loading="lazy"
            />
          ) : (
            <div className="image-error">
              <span>❌</span>
              <p>Failed to load image</p>
            </div>
          )}
        </div>

        <div className="preview-meta">
          <span className="file-size">
            {formatFileSize(annotation.file.file_size)}
          </span>
          {annotation.file.mime_type && (
            <span className="mime-type">
              {annotation.file.mime_type}
            </span>
          )}
        </div>
      </div>

      {/* Full-size modal */}
      {showModal && !imageError && (
        <div
          className="image-modal"
          onClick={() => setShowModal(false)}
        >
          <div className="modal-overlay" />
          <div className="modal-content">
            <button
              className="modal-close"
              onClick={() => setShowModal(false)}
              aria-label="Close modal"
            >
              ✕
            </button>
            <img
              src={annotation.file.url}
              alt={annotation.file.file_name || 'Image'}
              className="modal-image"
            />
            <div className="modal-caption">
              <h3>{annotation.file.file_name}</h3>
              <p>{formatFileSize(annotation.file.file_size)} • {formatDate(annotation.created_at)}</p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
