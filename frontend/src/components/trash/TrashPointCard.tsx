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
    if (!confirm(t('trash.confirmRestorePoint', 'Restore this point from trash?'))) return;

    setIsLoading(true);
    try {
      await restorePoint(item.gps_point.id);
      onRestore();
    } catch (error) {
      console.error('Failed to restore point:', error);
      alert(t('trash.restorePointFailed', 'Failed to restore point'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (
      !confirm(
        t('trash.confirmDeletePoint', 'Permanently delete this point? This action is irreversible and will also delete all associated annotations.')
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
      alert(t('trash.deletePointFailed', 'Failed to delete point'));
    } finally {
      setIsLoading(false);
    }
  };

  const getDaysRemainingClass = () => {
    if (item.days_remaining <= 7) return 'critical';
    if (item.days_remaining <= 14) return 'warning';
    return 'normal';
  };

  const formatDate = (dateString: string) => {
    const locale = t('common.locale', 'en-US');
    return new Date(dateString).toLocaleDateString(locale);
  };

  const getDaysRemainingText = (days: number) => {
    if (days === 1) {
      return t('trash.oneDayRemaining', '1 day remaining');
    }
    return t('trash.daysRemaining', '{count} days remaining').replace('{count}', String(days));
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
              {t('trash.deletedBy', 'Deleted by {email}').replace('{email}', item.deleted_by.email)}
            </span>
            <span className="deleted-at">
              {t('trash.on', 'on')} {formatDate(item.deleted_at)}
            </span>
          </div>
        </div>
        <div className={`days-remaining ${getDaysRemainingClass()}`}>
          {getDaysRemainingText(item.days_remaining)}
        </div>
      </div>

      {item.gps_point.description && (
        <p className="trash-card-description">{item.gps_point.description}</p>
      )}

      <div className="trash-card-details">
        <div className="detail-item">
          <span className="icon">📝</span>
          <span>
            {item.annotations.length} {item.annotations.length === 1
              ? t('trash.annotation', 'annotation')
              : t('trash.annotations', 'annotations')}
          </span>
        </div>
        <div className="detail-item">
          <span className="icon">👥</span>
          <span>
            {item.shares.length} {item.shares.length === 1
              ? t('trash.share', 'share')
              : t('trash.shares', 'shares')}
          </span>
        </div>
        <div className="detail-item">
          <span className="icon">🏷️</span>
          <span>
            {item.gps_point.tags.length} {item.gps_point.tags.length === 1
              ? t('common.tag', 'tag')
              : t('common.tags', 'tags')}
          </span>
        </div>
      </div>

      <button
        className="toggle-details-btn"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded
          ? `▼ ${t('trash.hideDetails', 'Hide details')}`
          : `▶ ${t('trash.showDetails', 'Show details')}`}
      </button>

      {isExpanded && (
        <div className="trash-card-expanded">
          {item.annotations.length > 0 && (
            <div className="expanded-section">
              <h4>{t('trash.associatedAnnotations', 'Associated annotations')}</h4>
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
                          {annotation.file?.file_name || t('trash.file', 'File')}
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
              <h4>{t('trash.sharesDeactivated', 'Shares (deactivated)')}</h4>
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
                ℹ️ {t('trash.sharesNoAccessNote', 'These people no longer have access to the point and its annotations.')}
              </p>
            </div>
          )}

          {item.gps_point.tags.length > 0 && (
            <div className="expanded-section">
              <h4>{t('common.tags', 'Tags')}</h4>
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
          ↺ {t('trash.restore', 'Restore')}
        </button>
        <button
          className="btn btn-delete"
          onClick={handleDelete}
          disabled={isLoading}
        >
          🗑️ {t('trash.deletePermanently', 'Delete permanently')}
        </button>
      </div>

      {item.is_expired && (
        <div className="expired-notice">
          ⚠️ {t('trash.pointExpiredNotice', 'This point has expired and will be automatically deleted.')}
        </div>
      )}
    </div>
  );
}
