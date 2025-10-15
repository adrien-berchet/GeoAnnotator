/**
 * TrashPage component.
 *
 * Displays trashed points and annotations with 30-day retention.
 * Two separate sections to distinguish between:
 * - Points deleted (all annotations are deleted with it)
 * - Annotations deleted individually (point remains active)
 */

import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { TrashPointCard } from '../components/trash/TrashPointCard';
import { TrashAnnotationCard } from '../components/trash/TrashAnnotationCard';
import { getAllTrashData, emptyPointTrash, emptyAnnotationTrash } from '../api/trash';
import type { TrashPoint, TrashAnnotation, TrashStats } from '../types/trash';
import './TrashPage.css';

export function TrashPage() {
  const location = useLocation();
  const [pointsTrash, setPointsTrash] = useState<TrashPoint[]>([]);
  const [annotationsTrash, setAnnotationsTrash] = useState<TrashAnnotation[]>([]);
  const [pointsStats, setPointsStats] = useState<TrashStats>({
    total_items: 0,
    expiring_soon: 0,
    oldest_item_age_days: 0,
  });
  const [annotationsStats, setAnnotationsStats] = useState<TrashStats>({
    total_items: 0,
    expiring_soon: 0,
    oldest_item_age_days: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'points' | 'annotations'>('points');

  useEffect(() => {
    loadTrashData();
  }, []);

  // Handle hash navigation to specific annotation
  useEffect(() => {
    const hash = location.hash;
    if (hash.startsWith('#annotation-')) {
      // Switch to annotations tab
      setActiveTab('annotations');

      // Wait for the tab content to render, then scroll to the annotation
      setTimeout(() => {
        const annotationId = hash.substring(1); // Remove the '#'
        const element = document.getElementById(annotationId);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          // Add a highlight effect
          element.classList.add('highlight-annotation');
          setTimeout(() => {
            element.classList.remove('highlight-annotation');
          }, 2000);
        }
      }, 100);
    }
  }, [location.hash, annotationsTrash]);

  const loadTrashData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getAllTrashData();

      // Ensure data is in the correct format
      setPointsTrash(Array.isArray(data.points) ? data.points : []);
      setAnnotationsTrash(Array.isArray(data.annotations) ? data.annotations : []);
      setPointsStats(data.pointsStats || {
        total_items: 0,
        expiring_soon: 0,
        oldest_item_age_days: 0,
      });
      setAnnotationsStats(data.annotationsStats || {
        total_items: 0,
        expiring_soon: 0,
        oldest_item_age_days: 0,
      });
    } catch (err) {
      console.error('Failed to load trash data:', err);
      setError('Échec du chargement des données de la corbeille');
      // Set empty arrays to avoid map errors
      setPointsTrash([]);
      setAnnotationsTrash([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmptyPointsTrash = async () => {
    if (
      !confirm(
        `Supprimer définitivement tous les ${pointsStats.total_items} points de la corbeille ? Cette action est irréversible.`
      )
    ) {
      return;
    }

    try {
      await emptyPointTrash();
      await loadTrashData();
    } catch (err) {
      console.error('Failed to empty points trash:', err);
      alert('Échec de la suppression des points');
    }
  };

  const handleEmptyAnnotationsTrash = async () => {
    if (
      !confirm(
        `Supprimer définitivement toutes les ${annotationsStats.total_items} annotations de la corbeille ? Cette action est irréversible.`
      )
    ) {
      return;
    }

    try {
      await emptyAnnotationTrash();
      await loadTrashData();
    } catch (err) {
      console.error('Failed to empty annotations trash:', err);
      alert('Échec de la suppression des annotations');
    }
  };

  if (isLoading) {
    return (
      <div className="trash-page">
        <div className="loading">Chargement de la corbeille...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="trash-page">
        <div className="error">{error}</div>
        <button className="btn btn-retry" onClick={loadTrashData}>
          Réessayer
        </button>
      </div>
    );
  }

  const currentStats = activeTab === 'points' ? pointsStats : annotationsStats;
  const currentCount = activeTab === 'points' ? pointsTrash.length : annotationsTrash.length;

  return (
    <div className="trash-page">
      <header className="trash-header">
        <h1>🗑️ Corbeille</h1>
        <p className="trash-subtitle">
          Les éléments supprimés sont conservés pendant 30 jours avant suppression définitive.
        </p>
      </header>

      <div className="trash-tabs">
        <button
          className={`tab-button ${activeTab === 'points' ? 'active' : ''}`}
          onClick={() => setActiveTab('points')}
        >
          📍 Points supprimés
          {pointsTrash.length > 0 && (
            <span className="tab-badge">{pointsTrash.length}</span>
          )}
        </button>
        <button
          className={`tab-button ${activeTab === 'annotations' ? 'active' : ''}`}
          onClick={() => setActiveTab('annotations')}
        >
          📝 Annotations supprimées
          {annotationsTrash.length > 0 && (
            <span className="tab-badge">{annotationsTrash.length}</span>
          )}
        </button>
      </div>

      {currentCount > 0 && (
        <div className="trash-stats">
          <div className="stat-item">
            <span className="stat-value">{currentStats.total_items}</span>
            <span className="stat-label">Total</span>
          </div>
          <div className="stat-item warning">
            <span className="stat-value">{currentStats.expiring_soon}</span>
            <span className="stat-label">Expire bientôt (&lt; 7 jours)</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{currentStats.oldest_item_age_days}</span>
            <span className="stat-label">Âge du plus ancien (jours)</span>
          </div>
        </div>
      )}

      {activeTab === 'points' && (
        <div className="trash-section">
          <div className="section-header">
            <h2>Points supprimés</h2>
            {pointsTrash.length > 0 && (
              <button className="btn btn-empty" onClick={handleEmptyPointsTrash}>
                Vider la corbeille des points
              </button>
            )}
          </div>

          {pointsTrash.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📍</div>
              <h3>Aucun point dans la corbeille</h3>
              <p>
                Les points supprimés apparaîtront ici et seront conservés pendant 30 jours.
              </p>
            </div>
          ) : (
            <>
              <div className="info-box">
                <strong>⚠️ Important :</strong> Lorsqu'un point est supprimé, toutes ses
                annotations et partages sont également supprimés avec lui. Après restauration,
                les partages seront réactivés si possible.
              </div>

              <div className="trash-list">
                {pointsTrash.map((item) => (
                  <TrashPointCard
                    key={item.id}
                    item={item}
                    onRestore={loadTrashData}
                    onDelete={loadTrashData}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === 'annotations' && (
        <div className="trash-section">
          <div className="section-header">
            <h2>Annotations supprimées</h2>
            {annotationsTrash.length > 0 && (
              <button className="btn btn-empty" onClick={handleEmptyAnnotationsTrash}>
                Vider la corbeille des annotations
              </button>
            )}
          </div>

          {annotationsTrash.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📝</div>
              <h3>Aucune annotation dans la corbeille</h3>
              <p>
                Les annotations supprimées individuellement apparaîtront ici et seront
                conservées pendant 30 jours.
              </p>
            </div>
          ) : (
            <>
              <div className="info-box">
                <strong>ℹ️ À noter :</strong> Ces annotations ont été supprimées individuellement.
                Les points auxquels elles sont associées restent actifs. Seules les annotations
                seront supprimées définitivement après 30 jours.
              </div>

              <div className="trash-list">
                {annotationsTrash.map((item) => (
                  <TrashAnnotationCard
                    key={item.id}
                    item={item}
                    onRestore={loadTrashData}
                    onDelete={loadTrashData}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
