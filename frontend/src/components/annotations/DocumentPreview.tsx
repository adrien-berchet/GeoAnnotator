/**
 * Document annotation preview component.
 *
 * Displays document files with download and metadata.
 */

import { downloadAnnotation } from '../../api/annotations';
import { getErrorMessage } from '../../api/client';
import type { Annotation } from '../../types/annotation';

interface DocumentPreviewProps {
  annotation: Annotation;
  pointId: string;
}

/**
 * Document annotation preview component.
 */
export function DocumentPreview({ annotation, pointId }: DocumentPreviewProps) {
  if ((annotation.type !== 'document' && annotation.type !== 'file') || !annotation.file) {
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

  /**
   * Get file extension.
   */
  const getFileExtension = (filename: string | null): string => {
    if (!filename) return 'file';
    const parts = filename.split('.');
    return parts.length > 1 ? parts[parts.length - 1].toUpperCase() : 'FILE';
  };

  /**
   * Get file icon based on extension.
   */
  const getFileIcon = (filename: string | null): string => {
    const ext = filename?.toLowerCase().split('.').pop();

    switch (ext) {
      case 'pdf':
        return '📕';
      case 'doc':
      case 'docx':
        return '📘';
      case 'xls':
      case 'xlsx':
        return '📗';
      case 'ppt':
      case 'pptx':
        return '📙';
      case 'txt':
      case 'md':
        return '📄';
      case 'zip':
      case 'rar':
      case '7z':
        return '📦';
      default:
        return '📎';
    }
  };

  /**
   * Handle file download.
   */
  const handleDownload = async () => {
    try {
      const blob = await downloadAnnotation(pointId, annotation.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = annotation.file?.file_name || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Download error: ${getErrorMessage(err)}`);
    }
  };

  return (
    <div className="document-preview">
      <div className="preview-header">
        <span className="preview-icon">
          {getFileIcon(annotation.file?.file_name || null)}
        </span>
        <div className="preview-info">
          <h4>{annotation.file?.file_name || 'Untitled Document'}</h4>
          <span className="preview-date">
            {formatDate(annotation.created_at)}
          </span>
        </div>
      </div>

      <div className="document-info">
        <div className="file-badge">
          <span className="file-extension">
            {getFileExtension(annotation.file?.file_name || null)}
          </span>
        </div>

        <div className="file-details">
          <div className="detail-item">
            <span className="label">Size:</span>
            <span className="value">{formatFileSize(annotation.file?.file_size || null)}</span>
          </div>
          {annotation.file?.mime_type && (
            <div className="detail-item">
              <span className="label">Type:</span>
              <span className="value">{annotation.file.mime_type}</span>
            </div>
          )}
        </div>
      </div>

      <div className="document-actions">
        <button
          onClick={handleDownload}
          className="btn btn-primary btn-sm"
        >
          📥 Download
        </button>
      </div>
    </div>
  );
}
