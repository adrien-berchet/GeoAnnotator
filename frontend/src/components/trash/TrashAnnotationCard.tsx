/**
 * TrashAnnotationCard component.
 *
 * Displays a trashed annotation with its associated point (which remains active).
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { TrashAnnotation } from '../../types/trash';
import { restoreAnnotation, permanentlyDeleteAnnotation } from '../../api/trash';
import './TrashCard.css';

interface TrashAnnotationCardProps {
  item: TrashAnnotation;
  onRestore: () => void;
  onDelete: () => void;
}

export function TrashAnnotationCard({
  item,
  onRestore,
  onDelete,
}: TrashAnnotationCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleRestore = async () => {
    if (!confirm('Restaurer cette annotation depuis la corbeille ?')) return;

    setIsLoading(true);
    try {
      await restoreAnnotation(item.annotation.id);
      onRestore();
    } catch (error) {
      console.error('Failed to restore annotation:', error);
      alert("Échec de la restauration de l'annotation");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (
      !confirm(
        "Supprimer définitivement cette annotation ? Cette action est irréversible."
      )
    ) {
      return;
    }

    setIsLoading(true);
    try {
      await permanentlyDeleteAnnotation(item.annotation.id);
      onDelete();
    } catch (error) {
      console.error('Failed to delete annotation:', error);
      alert("Échec de la suppression de l'annotation");
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewPoint = () => {
    navigate(`/points/${item.gps_point.id}`);
  };

  const getDaysRemainingClass = () => {
    if (item.days_remaining <= 7) return 'critical';
    if (item.days_remaining <= 14) return 'warning';
    return 'normal';
  };

  const renderAnnotationPreview = () => {
    const { annotation } = item;

    if (annotation.type === 'text') {
      return (
        <div className="annotation-preview-content text">
          <span className="icon">📝</span>
          <div
            className="text-preview"
            dangerouslySetInnerHTML={{
              __html: annotation.text_content?.substring(0, 150) + '...' || '',
            }}
          />
        </div>
      );
    }

    return (
      <div className="annotation-preview-content file">
        <span className="icon">
          {annotation.type === 'image'
            ? '🖼️'
            : annotation.type === 'document'
            ? '📄'
            : '📎'}
        </span>
        <div className="file-info">
          <div className="file-name">{annotation.file?.file_name}</div>
          <div className="file-meta">
            <span className="file-type">{annotation.type}</span>
            {annotation.file?.file_size && (
              <span className="file-size">
                {(annotation.file.file_size / 1024).toFixed(2)} KB
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="trash-card trash-annotation-card">
      <div className="trash-card-header">
        <div className="trash-card-info">
          <h3 className="trash-card-title">
            Annotation supprimée
          </h3>
          <div className="trash-card-meta">
            <span className="deleted-by">
              Supprimée par {item.deleted_by.email}
            </span>
            <span className="deleted-at">
              le {new Date(item.deleted_at).toLocaleDateString('fr-FR')}
            </span>
          </div>
        </div>
        <div className={`days-remaining ${getDaysRemainingClass()}`}>
          {item.days_remaining} jour{item.days_remaining > 1 ? 's' : ''} restant
          {item.days_remaining > 1 ? 's' : ''}
        </div>
      </div>

      <div className="annotation-preview">{renderAnnotationPreview()}</div>

      <div className="associated-point">
        <div className="associated-point-header">
          <h4>Point associé (actif)</h4>
          <button className="btn-link" onClick={handleViewPoint}>
            Voir le point →
          </button>
        </div>
        <div className="point-info">
          <span className="icon">📍</span>
          <span className="point-title">{item.gps_point.title}</span>
        </div>
        <p className="point-note">
          ℹ️ Le point reste actif. Seule cette annotation sera supprimée
          définitivement après {item.days_remaining} jour
          {item.days_remaining > 1 ? 's' : ''}.
        </p>
      </div>

      <div className="trash-card-actions">
        <button
          className="btn btn-restore"
          onClick={handleRestore}
          disabled={isLoading || item.is_expired}
        >
          ↺ Restaurer
        </button>
        <button
          className="btn btn-delete"
          onClick={handleDelete}
          disabled={isLoading}
        >
          🗑️ Supprimer définitivement
        </button>
      </div>

      {item.is_expired && (
        <div className="expired-notice">
          ⚠️ Cette annotation a expiré et sera supprimée automatiquement.
        </div>
      )}
    </div>
  );
}
