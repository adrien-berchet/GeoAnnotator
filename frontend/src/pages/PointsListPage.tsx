/**
 * Points list page.
 *
 * Displays all user's points in a list/grid view with search and filters.
 */

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getPoints, searchPointsByTags, getTags } from '../api/points';
import { getErrorMessage } from '../api/client';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { TagFilterPanel } from '../components/common/TagFilterPanel';
import type { GPSPoint, Tag } from '../types/point';
import './PointsListPage.css';

export function PointsListPage() {
  const [points, setPoints] = useState<GPSPoint[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [error, setError] = useState('');
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState('');
  const [selectedTagNames, setSelectedTagNames] = useState<string[]>([]);
  const navigate = useNavigate();

  const searchQuery = searchParams.get('search') || '';
  const tagsFilter = searchParams.get('tags') || '';
  const isFilterPanelOpen = searchParams.get('filterOpen') === 'true';

  useEffect(() => {
    loadTags();
  }, []);

  useEffect(() => {
    loadPoints();
  }, [searchQuery, tagsFilter]);

  useEffect(() => {
    // Sync selectedTagNames with URL params
    if (tagsFilter) {
      setSelectedTagNames(tagsFilter.split(',').map(t => t.trim()));
    } else {
      setSelectedTagNames([]);
    }
  }, [tagsFilter]);

  useEffect(() => {
    // Sync searchInput with URL params
    setSearchInput(searchQuery);
  }, [searchQuery]);

  const loadTags = async () => {
    try {
      const tags = await getTags();
      setAvailableTags(tags);
    } catch (err) {
      console.error('Error loading tags:', err);
    }
  };

  const loadPoints = async () => {
    setIsLoading(true);
    setError('');

    try {
      let data: GPSPoint[];

      if (tagsFilter) {
        // Filter by tags using the dedicated endpoint
        const tagNames = tagsFilter.split(',').map(t => t.trim());
        data = await searchPointsByTags(tagNames);
      } else if (searchQuery) {
        // Search by text
        const filters = { search: searchQuery };
        data = await getPoints(filters);
      } else {
        // Get all points
        data = await getPoints();
      }

      setPoints(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
      setIsInitialLoad(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSearchParams({ search: searchInput.trim() });
    } else {
      // Si la recherche est vide, enlever le paramètre
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('search');
      setSearchParams(newParams);
    }
  };

  const handleOpenFilterPanel = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('filterOpen', 'true');
    setSearchParams(newParams);
  };

  const handleClearFilters = () => {
    setSearchParams({});
  };

  const handleCloseFilterPanel = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete('filterOpen');
    setSearchParams(newParams);
  };

  const handleToggleTag = (tagName: string) => {
    const newSelectedTags = selectedTagNames.includes(tagName)
      ? selectedTagNames.filter(t => t !== tagName)
      : [...selectedTagNames, tagName];

    const newParams = new URLSearchParams(searchParams);

    if (newSelectedTags.length > 0) {
      newParams.set('tags', newSelectedTags.join(','));
    } else {
      newParams.delete('tags');
    }

    // Garder le panneau ouvert
    newParams.set('filterOpen', 'true');

    setSearchParams(newParams);
  };  const clearFilters = () => {
    setSearchParams({});
    setSearchInput('');
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isInitialLoad) {
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

        {/* Search and Filters */}
        <div className="filters-container">
          {/* Search Bar */}
          <form onSubmit={handleSearchSubmit} className="search-form">
            <input
              type="text"
              className="search-input"
              placeholder="Search points by title or description..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
            <button type="submit" className="search-button">
              🔍 Search
            </button>
            {searchQuery && (
              <button type="button" onClick={clearFilters} className="clear-button">
                ✕
              </button>
            )}
          </form>

          {/* Tags Filter Button */}
          {availableTags.length > 0 && (
            <button
              type="button"
              className={`filter-toggle-button ${isFilterPanelOpen ? 'active' : ''}`}
              onClick={handleOpenFilterPanel}
              title="Filter by tags"
            >
              🏷️ Filter Tags {selectedTagNames.length > 0 && `(${selectedTagNames.length})`}
              {isLoading && <span className="loading-indicator">⟳</span>}
            </button>
          )}
        </div>

        {/* Tags Filter Panel (Drawer) */}
        <TagFilterPanel
          isOpen={isFilterPanelOpen}
          availableTags={availableTags}
          selectedTags={selectedTagNames}
          onClose={handleCloseFilterPanel}
          onToggleTag={handleToggleTag}
          onClearAll={handleClearFilters}
        />

        {/* Results Info */}
        {(searchQuery || tagsFilter) && (
          <div className="results-info">
            {searchQuery && (
              <span>
                Search: <strong>"{searchQuery}"</strong>
              </span>
            )}
            {tagsFilter && (
              <span>
                Tags: <strong>{tagsFilter}</strong>
              </span>
            )}
            <span className="results-count">
              {points.length} {points.length === 1 ? 'result' : 'results'}
            </span>
            <button onClick={clearFilters} className="clear-filters-link">
              Clear all filters
            </button>
          </div>
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
