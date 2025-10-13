/**
 * Annotation preview modal component.
 *
 * Displays annotations in a full-screen preview mode.
 */

import { useEffect, useState } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { downloadAnnotation } from '../../api/annotations';
import type { Annotation } from '../../types/annotation';
import './AnnotationPreview.css';

interface AnnotationPreviewProps {
  annotation: Annotation;
  pointId: string;
  onClose: () => void;
}

export function AnnotationPreview({ annotation, pointId, onClose }: AnnotationPreviewProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load file for preview (PDF, images, etc.)
    const loadFile = async () => {
      if (annotation.type === 'text') return;
      if (!annotation.file) return;

      // For images, PDF and other files, download via authenticated API
      if (annotation.type === 'image' || annotation.file.mime_type?.includes('pdf') || annotation.type === 'document' || annotation.type === 'file') {
        setIsLoading(true);
        setError(null);

        try {
          const blob = await downloadAnnotation(pointId, annotation.id);
          const url = window.URL.createObjectURL(blob);
          setBlobUrl(url);
        } catch (err) {
          setError('Failed to load file for preview');
          console.error('Preview load error:', err);
        } finally {
          setIsLoading(false);
        }
      }
    };

    loadFile();

    // Cleanup blob URL on unmount
    return () => {
      if (blobUrl) {
        window.URL.revokeObjectURL(blobUrl);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [annotation.id, pointId]); // Only re-run if annotation or pointId changes

  useEffect(() => {
    // Close on Escape key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  useEffect(() => {
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  const renderPreview = () => {
    if (annotation.type === 'text' && annotation.text_content) {
      return (
        <div className="preview-text" data-color-mode="light">
          <MDEditor.Markdown source={annotation.text_content} />
        </div>
      );
    }

    if (annotation.type === 'image' && annotation.file) {
      if (isLoading) {
        return (
          <div className="preview-loading">
            <div className="loading-spinner">⏳</div>
            <p>Loading image...</p>
          </div>
        );
      }

      if (error) {
        return (
          <div className="preview-unavailable">
            <div className="unavailable-icon">❌</div>
            <h3>Preview Error</h3>
            <p>{error}</p>
            <p className="file-name">{annotation.file.file_name}</p>
          </div>
        );
      }

      if (blobUrl) {
        return (
          <div className="preview-image-container">
            <img
              src={blobUrl}
              alt={annotation.file.file_name || 'Image preview'}
              className="preview-image"
            />
          </div>
        );
      }
    }

    if (annotation.type === 'document' && annotation.file) {
      // Check if it's a PDF
      if (annotation.file.mime_type?.includes('pdf')) {
        if (isLoading) {
          return (
            <div className="preview-loading">
              <div className="loading-spinner">⏳</div>
              <p>Loading PDF...</p>
            </div>
          );
        }

        if (error) {
          return (
            <div className="preview-unavailable">
              <div className="unavailable-icon">❌</div>
              <h3>Preview Error</h3>
              <p>{error}</p>
              <p className="file-name">{annotation.file.file_name}</p>
            </div>
          );
        }

        if (blobUrl) {
          return (
            <div className="preview-pdf">
              <iframe
                src={blobUrl}
                title={annotation.file.file_name || 'Document preview'}
                className="pdf-viewer"
              />
            </div>
          );
        }
      }

      // For other documents, show download message
      return (
        <div className="preview-unavailable">
          <div className="unavailable-icon">📄</div>
          <h3>Preview not available</h3>
          <p>This document type cannot be previewed directly.</p>
          <p className="file-name">{annotation.file.file_name}</p>
        </div>
      );
    }

    if (annotation.type === 'file' && annotation.file) {
      return (
        <div className="preview-unavailable">
          <div className="unavailable-icon">📎</div>
          <h3>Preview not available</h3>
          <p>This file type cannot be previewed directly.</p>
          <p className="file-name">{annotation.file.file_name}</p>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="annotation-preview-overlay" onClick={onClose}>
      <div className="annotation-preview-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="preview-header">
          <div className="preview-title">
            <span className="preview-type-badge">
              {annotation.type === 'text' && '📝 Text'}
              {annotation.type === 'image' && '🖼️ Image'}
              {annotation.type === 'document' && '📄 Document'}
              {annotation.type === 'file' && '📎 File'}
            </span>
            {annotation.file?.file_name && (
              <span className="preview-file-name">{annotation.file.file_name}</span>
            )}
          </div>
          <button onClick={onClose} className="preview-close-button" title="Close (Esc)">
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="preview-content">
          {renderPreview()}
        </div>
      </div>
    </div>
  );
}
