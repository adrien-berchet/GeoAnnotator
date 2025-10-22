/**
 * Point detail page.
 *
 * Displays point information with annotations management.
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPoint, deletePoint } from '../api/points';
import { getAnnotations } from '../api/annotations';
import { getErrorMessage } from '../api/client';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { AnnotationForm, type AnnotationType } from '../components/annotations/AnnotationForm';
import { AnnotationsList } from '../components/annotations/AnnotationsList';
import { useLanguage } from '../contexts/LanguageContext';
import type { GPSPoint } from '../types/point';
import type { Annotation } from '../types/annotation';
import './PointDetailPage.css';

export function PointDetailPage() {
  const { t, language } = useLanguage();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [point, setPoint] = useState<GPSPoint | null>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [selectedAnnotationType, setSelectedAnnotationType] = useState<AnnotationType | null>(null);

  useEffect(() => {
    if (id) {
      loadPointData();
    }
  }, [id]);

  const loadPointData = async () => {
    if (!id) return;

    setIsLoading(true);
    setError('');

    try {
      const [pointData, annotationsData] = await Promise.all([
        getPoint(id),
        getAnnotations(id),
      ]);

      setPoint(pointData);
      setAnnotations(annotationsData);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnnotationCreated = (annotation: Annotation) => {
    setAnnotations([...annotations, annotation]);
    setSelectedAnnotationType(null);
  };

  const handleAnnotationDeleted = async (annotationId: string) => {
    console.log('🔄 Annotation deleted, reloading all annotations...');

    // Reload all annotations to get the updated trash status
    if (!id) return;

    try {
      const annotationsData = await getAnnotations(id);
      console.log('📥 Reloaded annotations:', annotationsData);
      console.log('📊 Trashed annotations after delete:', annotationsData.filter(a => a.is_trashed));
      setAnnotations(annotationsData);
    } catch (err) {
      console.error('❌ Failed to reload annotations:', err);
      // Fallback: just filter out the annotation
      setAnnotations(annotations.filter((a) => a.id !== annotationId));
    }
  };

  const handleAnnotationUpdated = (updatedAnnotation: Annotation) => {
    setAnnotations(annotations.map((a) => a.id === updatedAnnotation.id ? updatedAnnotation : a));
  };

  const handleAnnotationsReordered = (reorderedAnnotations: Annotation[]) => {
    setAnnotations(reorderedAnnotations);
  };

  const handleDeletePoint = async () => {
    if (!id || !point) return;

    const message = t('pointDetail.confirmDelete', 'Are you sure you want to delete "{title}"?')
      .replace('{title}', point.title || t('pointDetail.thisPoint', 'this point'));

    if (!confirm(message)) {
      return;
    }

    setIsDeleting(true);

    try {
      await deletePoint(id);
      navigate('/points');
    } catch (err) {
      alert(getErrorMessage(err));
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString: string) => {
    const locale = t('common.locale', 'en-US');
    return new Date(dateString).toLocaleDateString(locale, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return <LoadingSpinner size="large" message={t('pointDetail.loadingPoint', 'Loading point...')} />;
  }

  if (error || !point || !id) {
    return (
      <div className="error-container">
        <h2>{t('pointDetail.errorLoading', 'Error loading point')}</h2>
        <p>{error || t('pointDetail.notFound', 'Point not found')}</p>
        <button onClick={() => navigate('/points')} className="btn btn-primary">
          {t('pointDetail.backToPoints', 'Back to Points')}
        </button>
      </div>
    );
  }

  return (
    <div className="point-detail-page">
      {/* Header */}
      <div className="point-detail-header">
        <button onClick={() => navigate('/points')} className="btn btn-ghost">
          ← {t('pointDetail.backToPoints', 'Back to Points')}
        </button>
        <div className="header-actions">
          <button onClick={() => navigate(`/points/${id}/edit`)} className="btn btn-secondary">
            ✏️ {t('common.edit', 'Edit')}
          </button>
          <button
            onClick={handleDeletePoint}
            className="btn btn-danger"
            disabled={isDeleting}
          >
            {isDeleting ? `🗑️ ${t('pointDetail.deleting', 'Deleting...')}` : `🗑️ ${t('common.delete', 'Delete')}`}
          </button>
        </div>
      </div>

      {/* Point Info */}
      <div className="point-info-card">
        <div className="point-info-header">
          <h1>{point.title || t('pointDetail.untitledPoint', 'Untitled Point')}</h1>
          {point.is_public && <span className="public-badge">🌐 {t('pointDetail.public', 'Public')}</span>}
        </div>

        <div className="point-metadata">
          <div className="metadata-item">
            <span className="metadata-label">📍 {t('pointDetail.location', 'Location')}</span>
            <span className="metadata-value">
              {point.latitude.toFixed(6)}, {point.longitude.toFixed(6)}
            </span>
          </div>

          {point.type && (
            <div className="metadata-item">
              <span className="metadata-label">🏷️ {t('points.type', 'Type')}</span>
              <span className="metadata-value">
                {point.type.icon && (
                  <img
                    src={point.type.icon}
                    alt=""
                    style={{ width: '16px', height: '16px', marginRight: '4px', verticalAlign: 'middle' }}
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                )}
                {point.type.names[language] || point.type.names[point.type.creation_language]}
              </span>
            </div>
          )}

          <div className="metadata-item">
            <span className="metadata-label">📅 {t('pointDetail.created', 'Created')}</span>
            <span className="metadata-value">{formatDate(point.created_at)}</span>
          </div>

          {point.updated_at !== point.created_at && (
            <div className="metadata-item">
              <span className="metadata-label">🔄 {t('pointDetail.updated', 'Updated')}</span>
              <span className="metadata-value">{formatDate(point.updated_at)}</span>
            </div>
          )}
        </div>

        {point.description && (
          <div className="point-description">
            <h3>{t('points.description', 'Description')}</h3>
            <p>{point.description}</p>
          </div>
        )}

        {point.tags && point.tags.length > 0 && (
          <div className="point-tags">
            <h3>{t('points.tags', 'Tags')}</h3>
            <div className="tags-list">
              {point.tags.map((tag) => (
                <span key={tag.id} className="tag">
                  {tag.name}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Annotations Section */}
      <div className="annotations-section">
        <h2>{t('pointDetail.annotations', 'Annotations')} ({annotations.length})</h2>

        {/* Add Annotation Buttons - Always Visible */}
        <div className="add-annotation-buttons">
          <button
            type="button"
            className={`annotation-type-button ${selectedAnnotationType === 'text' ? 'active' : ''}`}
            onClick={() => setSelectedAnnotationType(selectedAnnotationType === 'text' ? null : 'text')}
          >
            📝 {t('annotations.text', 'Text')}
          </button>
          <button
            type="button"
            className={`annotation-type-button ${selectedAnnotationType === 'image' ? 'active' : ''}`}
            onClick={() => setSelectedAnnotationType(selectedAnnotationType === 'image' ? null : 'image')}
          >
            🖼️ {t('annotations.image', 'Image')}
          </button>
          <button
            type="button"
            className={`annotation-type-button ${selectedAnnotationType === 'document' ? 'active' : ''}`}
            onClick={() => setSelectedAnnotationType(selectedAnnotationType === 'document' ? null : 'document')}
          >
            📄 {t('annotations.document', 'Document')}
          </button>
          <button
            type="button"
            className={`annotation-type-button ${selectedAnnotationType === 'file' ? 'active' : ''}`}
            onClick={() => setSelectedAnnotationType(selectedAnnotationType === 'file' ? null : 'file')}
          >
            📎 {t('annotations.file', 'File')}
          </button>
        </div>

        <div className="annotations-container">
          {/* Add Annotation Form */}
          {selectedAnnotationType && (
            <div className="add-annotation-section">
              <AnnotationForm
                pointId={id}
                onAnnotationCreated={handleAnnotationCreated}
                onCancel={() => setSelectedAnnotationType(null)}
                initialType={selectedAnnotationType}
              />
            </div>
          )}

          {/* Annotations List */}
          <div className="annotations-list-section">
            <AnnotationsList
              pointId={id}
              annotations={annotations}
              onAnnotationDeleted={handleAnnotationDeleted}
              onAnnotationUpdated={handleAnnotationUpdated}
              onAnnotationsReordered={handleAnnotationsReordered}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
