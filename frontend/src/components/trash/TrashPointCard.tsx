/**
 * TrashPointCard component.
 *
 * Displays a trashed point with its annotations and shares.
 */

import { useState } from 'react';
import type { TrashPoint } from '../../types/trash';
import { restorePoint, permanentlyDeletePoint } from '../../api/trash';
import { useLanguage } from '../../contexts/LanguageContext';
import './TrashCard.css';

interface TrashPointCardProps {
  item: TrashPoint;
  onRestore: () => void;
  onDelete: () => void;
}

export function TrashPointCard({ item, onRestore, onDelete }: TrashPointCardProps) {
  const { t } = useLanguage();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleRestore = async () => {
    if (!confirm('Restaurer ce point depuis la corbeille ?')) return;

    setIsLoading(true);
    try {
      await restorePoint(item.gps_point.id);
      onRestore();
    } catch (error) {
      console.error('Failed to restore point:', error);
      alert('Échec de la restauration du point');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (
      !confirm(
        'Supprimer définitivement ce point ? Cette action est irréversible et supprimera également toutes les annotations associées.'
      )
    ) {
      return;
    }

    setIsLoading(true);
    try {
      await permanentlyDeletePoint(item.gps_point.id);
      onDelete();
    } catch (error) {
      console.error('Failed to delete point:', error);
      alert('Échec de la suppression du point');
    } finally {
      setIsLoading(false);
    }
  };

  const getDaysRemainingClass = () => {
    if (item.days_remaining <= 7) return 'critical';
    if (item.days_remaining <= 14) return 'warning';
    return 'normal';
  };

  return (
    <div className="trash-card trash-point-card">
      <div className="trash-card-header">
        <div className="trash-card-info">
          <h3 className="trash-card-title">
            <span className="icon">📍</span>
            {item.gps_point.title}
          </h3>
          <div className="trash-card-meta">
            <span className="deleted-by">
              Supprimé par {item.deleted_by.email}
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

      {item.gps_point.description && (
        <p className="trash-card-description">{item.gps_point.description}</p>
      )}

      <div className="trash-card-details">
        <div className="detail-item">
          <span className="icon">📝</span>
          <span>{item.annotations.length} annotation(s)</span>
        </div>
        <div className="detail-item">
          <span className="icon">👥</span>
          <span>{item.shares.length} partage(s)</span>
        </div>
        <div className="detail-item">
          <span className="icon">🏷️</span>
          <span>{item.gps_point.tags.length} tag(s)</span>
        </div>
      </div>

      <button
        className="toggle-details-btn"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? '▼ Masquer les détails' : '▶ Afficher les détails'}
      </button>

      {isExpanded && (
        <div className="trash-card-expanded">
          {item.annotations.length > 0 && (
            <div className="expanded-section">
              <h4>Annotations associées</h4>
              <div className="annotations-list">
                {item.annotations.map((annotation) => (
                  <div key={annotation.id} className="annotation-item">
                    {annotation.type === 'text' ? (
                      <>
                        <span className="icon">📝</span>
                        <span className="annotation-preview">
                          {annotation.text_content?.substring(0, 50)}...
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="icon">
                          {annotation.type === 'image'
                            ? '🖼️'
                            : annotation.type === 'document'
                            ? '📄'
                            : '📎'}
                        </span>
                        <span className="annotation-preview">
                          {annotation.file?.file_name || 'Fichier'}
                        </span>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {item.shares.length > 0 && (
            <div className="expanded-section">
              <h4>Partages (désactivés)</h4>
              <div className="shares-list">
                {item.shares.map((share) => (
                  <div key={share.id} className="share-item">
                    <span className="icon">👤</span>
                    <span className="share-email">{share.recipient_email}</span>
                    <span className="share-permission">{share.permission}</span>
                  </div>
                ))}
              </div>
              <p className="shares-note">
                ℹ️ Ces personnes n'ont plus accès au point et à ses annotations.
              </p>
            </div>
          )}

          {item.gps_point.tags.length > 0 && (
            <div className="expanded-section">
              <h4>Tags</h4>
              <div className="tags-list">
                {item.gps_point.tags.map((tag) => (
                  <span key={tag.id} className="tag">
                    {tag.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="trash-card-actions">
        <button
          className="btn btn-restore"
          onClick={handleRestore}
          disabled={isLoading || item.is_expired}
        >
          ↺ {t('trash.restore', 'Restaurer')}
        </button>
        <button
          className="btn btn-delete"
          onClick={handleDelete}
          disabled={isLoading}
        >
          🗑️ {t('trash.deletePermanently', 'Supprimer définitivement')}
        </button>
      </div>

      {item.is_expired && (
        <div className="expired-notice">
          ⚠️ Ce point a expiré et sera supprimé automatiquement.
        </div>
      )}
    </div>
  );
}
