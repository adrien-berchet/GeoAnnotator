/**
 * Points list page.
 * 
 * Displays all user's points in a list/grid view with search and filters.
 */

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getPoints } from '../api/points';
import { getErrorMessage } from '../api/client';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import type { GPSPoint } from '../types/point';
import './PointsListPage.css';

export function PointsListPage() {
  const [points, setPoints] = useState<GPSPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const searchQuery = searchParams.get('search') || '';

  useEffect(() => {
    loadPoints();
  }, [searchQuery]);

  const loadPoints = async () => {
    setIsLoading(true);
    setError('');

    try {
      const filters = searchQuery ? { search: searchQuery } : undefined;
      const data = await getPoints(filters);
      setPoints(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isLoading) {
    return <LoadingSpinner size="large" message="Loading points..." />;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error loading points</h2>
        <p>{error}</p>
        <button onClick={loadPoints} className="btn-primary">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="points-list-page">
      <div className="points-list-header">
        <h1>My Points</h1>
        {searchQuery && (
          <p className="search-results-info">
            Search results for "{searchQuery}" ({points.length} {points.length === 1 ? 'result' : 'results'})
          </p>
        )}
        <div className="points-list-stats">
          <span>{points.length} point{points.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {points.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📍</div>
          <h2>No points yet</h2>
          <p>Click on the map to create your first GPS point</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            Go to Map
          </button>
        </div>
      ) : (
        <div className="points-grid">
          {points.map((point) => (
            <div
              key={point.id}
              className="point-card"
              onClick={() => navigate(`/points/${point.id}`)}
            >
              <div className="point-card-header">
                <h3 className="point-card-title">{point.title || 'Untitled Point'}</h3>
                {point.is_public && (
                  <span className="point-badge public">🌐 Public</span>
                )}
              </div>

              <div className="point-card-location">
                📍 {point.latitude.toFixed(6)}, {point.longitude.toFixed(6)}
              </div>

              {point.description && (
                <p className="point-card-description">
                  {point.description.length > 100
                    ? `${point.description.substring(0, 100)}...`
                    : point.description}
                </p>
              )}

              {point.tags && point.tags.length > 0 && (
                <div className="point-card-tags">
                  {point.tags.slice(0, 3).map((tag) => (
                    <span key={tag.id} className="tag">
                      {tag.name}
                    </span>
                  ))}
                  {point.tags.length > 3 && (
                    <span className="tag-more">+{point.tags.length - 3}</span>
                  )}
                </div>
              )}

              <div className="point-card-footer">
                <span className="point-card-date">
                  📅 {formatDate(point.created_at)}
                </span>
                {point.annotation_count !== undefined && (
                  <span className="point-card-annotations">
                    📝 {point.annotation_count} annotation{point.annotation_count !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
