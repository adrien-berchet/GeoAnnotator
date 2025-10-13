/**
 * TrashedAnnotationBanner component.
 *
 * Displays a banner for annotations in the trash with restore option.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Annotation } from '../../types/annotation';
import { restoreAnnotation } from '../../api/trash';
import './TrashedAnnotationBanner.css';

interface TrashedAnnotationBannerProps {
  annotation: Annotation;
  onRestore?: () => void;
}

export function TrashedAnnotationBanner({
  annotation,
  onRestore,
}: TrashedAnnotationBannerProps) {
  const [isRestoring, setIsRestoring] = useState(false);
  const navigate = useNavigate();

  if (!annotation.is_trashed) {
    return null;
  }

  const handleRestore = async () => {
    if (!confirm('Restore this annotation from trash?')) {
      return;
    }

    setIsRestoring(true);
    try {
      await restoreAnnotation(annotation.id);
      if (onRestore) {
        onRestore();
      }
    } catch (error) {
      console.error('Failed to restore annotation:', error);
      alert('Failed to restore annotation');
    } finally {
      setIsRestoring(false);
    }
  };

  const handleViewTrash = () => {
    navigate('/trash');
  };

  const getDaysRemainingClass = () => {
    const days = annotation.trash_days_remaining || 0;
    if (days <= 7) return 'critical';
    if (days <= 14) return 'warning';
    return 'normal';
  };

  return (
    <div className={`trashed-annotation-banner ${getDaysRemainingClass()}`}>
      <div className="banner-icon">🗑️</div>
      <div className="banner-content">
        <div className="banner-title">
          Trashed
        </div>
        <div className="banner-info">
          {annotation.trash_days_remaining !== null && (
            <span className="days-remaining">
              {annotation.trash_days_remaining} day{annotation.trash_days_remaining > 1 ? 's' : ''} left
            </span>
          )}
        </div>
      </div>
      <div className="banner-actions">
        <button
          className="btn btn-restore"
          onClick={handleRestore}
          disabled={isRestoring}
        >
          {isRestoring ? 'Restoring...' : '↺ Restore'}
        </button>
        <button className="btn btn-view-trash" onClick={handleViewTrash}>
          View Trash →
        </button>
      </div>
    </div>
  );
}
