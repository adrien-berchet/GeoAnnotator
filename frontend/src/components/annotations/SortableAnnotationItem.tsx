/**
 * Sortable annotation item with drag-and-drop support.
 */

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import MDEditor from '@uiw/react-md-editor';
import type { Annotation } from '../../types/annotation';
import { TextAnnotationEditor } from './TextAnnotationEditor';

interface SortableAnnotationItemProps {
  annotation: Annotation;
  pointId: string;
  imageBlobUrl?: string;
  isDeleting: boolean;
  isDownloading: boolean;
  isEditing: boolean;
  isReorderMode: boolean;
  onDelete: (id: string) => void;
  onDownload: (annotation: Annotation) => void;
  onPreview: (annotation: Annotation) => void;
  onEditStart: () => void;
  onEditSave: (annotation: Annotation) => void;
  onEditCancel: () => void;
  formatDate: (date: string) => string;
  formatFileSize: (bytes: number) => string;
}

export function SortableAnnotationItem({
  annotation,
  pointId,
  imageBlobUrl,
  isDeleting,
  isDownloading,
  isEditing,
  isReorderMode,
  onDelete,
  onDownload,
  onPreview,
  onEditStart,
  onEditSave,
  onEditCancel,
  formatDate,
  formatFileSize,
}: SortableAnnotationItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: annotation.id,
    disabled: !isReorderMode,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="annotation-item"
    >
      {/* Drag Handle - only visible in reorder mode */}
      {isReorderMode && (
        <div className="drag-handle" {...attributes} {...listeners} title="Drag to reorder">
          ⋮⋮
        </div>
      )}

      <div className="annotation-content-wrapper">
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
            <>
              {isEditing ? (
                <TextAnnotationEditor
                  annotation={annotation}
                  pointId={pointId}
                  onSave={onEditSave}
                  onCancel={onEditCancel}
                />
              ) : (
                <div className="text-annotation-display">
                  <div
                    className="text-preview clickable"
                    onClick={() => onPreview(annotation)}
                    title="Click to preview"
                    data-color-mode="light"
                  >
                    <MDEditor.Markdown source={annotation.text_content} />
                  </div>
                  <button
                    onClick={onEditStart}
                    className="edit-text-button"
                    title="Edit text"
                  >
                    ✏️ Edit
                  </button>
                </div>
              )}
            </>
          )}

          {/* Image Annotation */}
          {annotation.type === 'image' && annotation.file && (
            <div className="image-annotation">
              {imageBlobUrl ? (
                <img
                  src={imageBlobUrl}
                  alt={annotation.file.file_name || 'Image'}
                  className="annotation-image clickable"
                  onClick={() => onPreview(annotation)}
                  title="Click to preview full size"
                />
              ) : (
                <div className="image-loading">⏳ Loading image...</div>
              )}
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
                  onClick={() => onDownload(annotation)}
                  className="download-button"
                  disabled={isDownloading}
                >
                  {isDownloading ? '⏳ Downloading...' : '⬇️ Download'}
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
              <div className="file-actions">
                <button
                  onClick={() => onPreview(annotation)}
                  className="preview-button"
                  title="Preview"
                >
                  👁️ Preview
                </button>
                <button
                  onClick={() => onDownload(annotation)}
                  className="download-button"
                  disabled={isDownloading}
                >
                  {isDownloading ? '⏳ Downloading...' : '⬇️ Download'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="annotation-actions">
          <button
            onClick={() => onDelete(annotation.id)}
            className="delete-button"
            disabled={isDeleting}
          >
            {isDeleting ? '🗑️ Deleting...' : '🗑️ Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}
