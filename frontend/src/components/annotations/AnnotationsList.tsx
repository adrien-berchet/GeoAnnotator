/**
 * Annotations list component.
 *
 * Displays all annotations for a point with preview and actions.
 */

import { useState, useEffect } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { deleteAnnotation, downloadAnnotation, reorderAnnotations } from '../../api/annotations';
import { getErrorMessage } from '../../api/client';
import type { Annotation } from '../../types/annotation';
import { AnnotationPreview } from './AnnotationPreview';
import { SortableAnnotationItem } from './SortableAnnotationItem';
import { useLanguage } from '../../contexts/LanguageContext';
import './AnnotationsList.css';

interface AnnotationsListProps {
  pointId: string;
  annotations: Annotation[];
  onAnnotationDeleted: (annotationId: string) => void;
  onAnnotationUpdated?: (annotation: Annotation) => void;
  onAnnotationsReordered?: (annotations: Annotation[]) => void;
}

export function AnnotationsList({
  pointId,
  annotations,
  onAnnotationDeleted,
  onAnnotationUpdated,
  onAnnotationsReordered,
}: AnnotationsListProps) {
  const { t } = useLanguage();
  console.log('🚀 AnnotationsList component loaded for point:', pointId);
  console.log('📥 Received annotations:', annotations);
  console.log('📊 Trashed annotations:', annotations.filter(a => a.is_trashed));

  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [previewAnnotation, setPreviewAnnotation] = useState<Annotation | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [imageBlobUrls, setImageBlobUrls] = useState<Record<string, string>>({});
  const [localAnnotations, setLocalAnnotations] = useState<Annotation[]>(annotations);
  const [isReorderMode, setIsReorderMode] = useState(false);

  // Sync local annotations with props
  useEffect(() => {
    setLocalAnnotations(annotations);
  }, [annotations]);

  // Configure drag sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Load images as blob URLs for authenticated preview
  useEffect(() => {
    const loadImages = async () => {
      const imageAnnotations = annotations.filter(a => a.type === 'image' && a.file);
      const blobUrls: Record<string, string> = {};

      for (const annotation of imageAnnotations) {
        try {
          const blob = await downloadAnnotation(pointId, annotation.id);
          const url = window.URL.createObjectURL(blob);
          blobUrls[annotation.id] = url;
        } catch (err) {
          console.error(`Failed to load image ${annotation.id}:`, err);
        }
      }

      setImageBlobUrls(blobUrls);
    };

    loadImages();

    // Cleanup blob URLs on unmount or when annotations change
    return () => {
      Object.values(imageBlobUrls).forEach(url => {
        window.URL.revokeObjectURL(url);
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [annotations, pointId]);

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    const oldIndex = localAnnotations.findIndex((a) => a.id === active.id);
    const newIndex = localAnnotations.findIndex((a) => a.id === over.id);

    if (oldIndex === -1 || newIndex === -1) {
      return;
    }

    // Reorder locally first for immediate UI feedback
    const reordered = arrayMove(localAnnotations, oldIndex, newIndex);

    // Update order property for each annotation
    const reorderedWithOrder = reordered.map((annotation: Annotation, index: number) => ({
      ...annotation,
      order: index,
    }));

    setLocalAnnotations(reorderedWithOrder);

    // Update order numbers and save to server
    const updates = reorderedWithOrder.map((annotation: Annotation, index: number) => ({
      id: annotation.id,
      order: index,
    }));

    try {
      await reorderAnnotations(pointId, updates);
      // Notify parent component of the new order
      if (onAnnotationsReordered) {
        onAnnotationsReordered(reorderedWithOrder);
      }
    } catch (err) {
      console.error('Failed to save order:', err);
      setError(getErrorMessage(err));
      // Revert on error
      setLocalAnnotations(annotations);
    }
  };

  const handleDelete = async (annotationId: string) => {
    if (!confirm(t('annotations.confirmDelete', 'Are you sure you want to delete this annotation?'))) {
      return;
    }

    console.log('🗑️ Deleting annotation:', annotationId);
    setDeletingId(annotationId);
    setError('');

    try {
      await deleteAnnotation(pointId, annotationId);
      console.log('✅ Annotation deleted successfully');

      // IMPORTANT: Ne pas retirer l'annotation, juste notifier le parent
      // Le parent devra recharger les annotations pour voir l'état "trashed"
      onAnnotationDeleted(annotationId);
    } catch (err) {
      const errorMsg = getErrorMessage(err);
      console.error('❌ Delete error:', errorMsg);

      // Check if already in trash
      if (errorMsg.includes('ALREADY_IN_TRASH') || errorMsg.includes('already in trash')) {
        setError(t('annotations.alreadyInTrash', 'This annotation is already in the trash. Please use the restore button to recover it.'));
      } else {
        setError(errorMsg);
      }
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
    const locale = t('common.locale', 'en-US');
    return new Date(dateString).toLocaleDateString(locale, {
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

  if (localAnnotations.length === 0) {
    return (
      <div className="annotations-empty">
        <div className="empty-icon">📝</div>
        <p>{t('annotations.noAnnotationsYet', 'No annotations yet')}</p>
        <p className="empty-hint">{t('annotations.addFirstAnnotation', 'Add your first annotation above')}</p>
      </div>
    );
  }

  return (
    <div className="annotations-list">
      {error && <div className="error-message">{error}</div>}

      {/* Reorder Mode Toggle */}
      <div className="annotations-toolbar">
        <button
          onClick={() => setIsReorderMode(!isReorderMode)}
          className={`reorder-toggle-button ${isReorderMode ? 'active' : ''}`}
          title={isReorderMode ? t('annotations.exitReorderMode', 'Exit reorder mode') : t('annotations.reorderAnnotations', 'Reorder annotations')}
        >
          {isReorderMode ? `✓ ${t('annotations.doneReordering', 'Done reordering')}` : `↕️ ${t('annotations.reorder', 'Reorder')}`}
        </button>
        {isReorderMode && (
          <span className="reorder-hint">{t('annotations.reorderHint', 'Drag and drop to reorder annotations')}</span>
        )}
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={localAnnotations.map((a) => a.id)}
          strategy={verticalListSortingStrategy}
        >
          {localAnnotations.map((annotation) => (
            <SortableAnnotationItem
              key={annotation.id}
              annotation={annotation}
              pointId={pointId}
              imageBlobUrl={imageBlobUrls[annotation.id]}
              isDeleting={deletingId === annotation.id}
              isDownloading={downloadingId === annotation.id}
              isEditing={editingId === annotation.id}
              isReorderMode={isReorderMode}
              onDelete={handleDelete}
              onDownload={handleDownload}
              onPreview={setPreviewAnnotation}
              onEditStart={() => setEditingId(annotation.id)}
              onEditSave={(updatedAnnotation) => {
                setEditingId(null);
                if (onAnnotationUpdated) {
                  onAnnotationUpdated(updatedAnnotation);
                }
              }}
              onEditCancel={() => setEditingId(null)}
              formatDate={formatDate}
              formatFileSize={formatFileSize}
            />
          ))}
        </SortableContext>
      </DndContext>

      {/* Preview Modal */}
      {previewAnnotation && (
        <AnnotationPreview
          annotation={previewAnnotation}
          pointId={pointId}
          onClose={() => setPreviewAnnotation(null)}
        />
      )}
    </div>
  );
}
