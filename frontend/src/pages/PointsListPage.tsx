/**
 * Points list page.
 *
 * Displays all user's points in a list/grid view with search and filters.
 */

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getPoints, searchPointsByTags, getTags } from '../api/points';
import { getPointTypes } from '../api/types';
import { getErrorMessage } from '../api/client';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { FilterPanel } from '../components/common/FilterPanel';
import { useLanguage } from '../contexts/LanguageContext';
import type { GPSPoint, Tag, PointType } from '../types/point';
import './PointsListPage.css';

export function PointsListPage() {
  const { t } = useLanguage();
  const [points, setPoints] = useState<GPSPoint[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [availableTypes, setAvailableTypes] = useState<PointType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [error, setError] = useState('');
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState('');
  const [selectedTagNames, setSelectedTagNames] = useState<string[]>([]);
  const [selectedTypeIds, setSelectedTypeIds] = useState<string[]>([]);
  const navigate = useNavigate();

  const searchQuery = searchParams.get('search') || '';
  const tagsFilter = searchParams.get('tags') || '';
  const typesFilter = searchParams.get('types') || '';
  const isFilterPanelOpen = searchParams.get('filterOpen') === 'true';

  useEffect(() => {
    loadTags();
    loadTypes();
  }, []);

  useEffect(() => {
    loadPoints();
  }, [searchQuery, tagsFilter, typesFilter]);

  useEffect(() => {
    // Sync selectedTagNames with URL params
    if (tagsFilter) {
      setSelectedTagNames(tagsFilter.split(',').map(t => t.trim()));
    } else {
      setSelectedTagNames([]);
    }
  }, [tagsFilter]);

  useEffect(() => {
    // Sync selectedTypeIds with URL params
    if (typesFilter) {
      setSelectedTypeIds(typesFilter.split(',').map(t => t.trim()));
    } else {
      setSelectedTypeIds([]);
    }
  }, [typesFilter]);

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

  const loadTypes = async () => {
    try {
      const types = await getPointTypes();
      setAvailableTypes(types);
    } catch (err) {
      console.error('Error loading types:', err);
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

      // Apply type filter client-side
      if (typesFilter) {
        const typeIds = typesFilter.split(',').map(t => t.trim());
        data = data.filter(point =>
          point.type && typeIds.includes(point.type.id)
        );
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

    // Keep types filter if present
    if (selectedTypeIds.length > 0) {
      newParams.set('types', selectedTypeIds.join(','));
    }

    // Garder le panneau ouvert
    newParams.set('filterOpen', 'true');

    setSearchParams(newParams);
  };

  const handleToggleType = (typeId: string) => {
    const newSelectedTypes = selectedTypeIds.includes(typeId)
      ? selectedTypeIds.filter(t => t !== typeId)
      : [...selectedTypeIds, typeId];

    const newParams = new URLSearchParams(searchParams);

    if (newSelectedTypes.length > 0) {
      newParams.set('types', newSelectedTypes.join(','));
    } else {
      newParams.delete('types');
    }

    // Keep tags filter if present
    if (selectedTagNames.length > 0) {
      newParams.set('tags', selectedTagNames.join(','));
    }

    // Garder le panneau ouvert
    newParams.set('filterOpen', 'true');

    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setSearchParams({});
    setSearchInput('');
  };

  const formatDate = (dateString: string) => {
    const locale = t('common.locale', 'en-US');
    return new Date(dateString).toLocaleDateString(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isInitialLoad) {
    return <LoadingSpinner size="large" message={t('points.loadingPoints', 'Loading points...')} />;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>{t('points.errorLoading', 'Error loading points')}</h2>
        <p>{error}</p>
        <button onClick={loadPoints} className="btn-primary">
          {t('common.retry', 'Retry')}
        </button>
      </div>
    );
  }

  return (
    <div className="points-list-page">
      <div className="points-list-header">
        <h1>{t('nav.points', 'Points')}</h1>

        {/* Search and Filters */}
        <div className="filters-container">
          {/* Search Bar */}
          <form onSubmit={handleSearchSubmit} className="search-form">
            <input
              type="text"
              className="search-input"
              placeholder={t('points.searchPlaceholder', 'Search points by title or description...')}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
            <button type="submit" className="search-button">
              🔍 {t('common.search', 'Search')}
            </button>
            {searchQuery && (
              <button type="button" onClick={clearFilters} className="clear-button">
                ✕
              </button>
            )}
          </form>

          {/* Filter Button */}
          {(availableTags.length > 0 || availableTypes.length > 0) && (
            <button
              type="button"
              className={`filter-toggle-button ${isFilterPanelOpen ? 'active' : ''}`}
              onClick={handleOpenFilterPanel}
              title={t('points.filterByTagsTypes', 'Filter by tags and types')}
            >
              🔍 {t('common.filter', 'Filters')} {(selectedTagNames.length + selectedTypeIds.length) > 0 && `(${selectedTagNames.length + selectedTypeIds.length})`}
              {isLoading && <span className="loading-indicator">⟳</span>}
            </button>
          )}
        </div>

        {/* Filter Panel (Drawer) */}
        <FilterPanel
          isOpen={isFilterPanelOpen}
          availableTags={availableTags}
          availableTypes={availableTypes}
          selectedTags={selectedTagNames}
          selectedTypes={selectedTypeIds}
          onClose={handleCloseFilterPanel}
          onToggleTag={handleToggleTag}
          onToggleType={handleToggleType}
          onClearAll={handleClearFilters}
        />

        {/* Results Info */}
        {(searchQuery || tagsFilter || typesFilter) && (
          <div className="results-info">
            {searchQuery && (
              <span>
                {t('common.search', 'Search')}: <strong>"{searchQuery}"</strong>
              </span>
            )}
            {tagsFilter && (
              <span>
                {t('nav.tags', 'Tags')}: <strong>{tagsFilter}</strong>
              </span>
            )}
            {typesFilter && (
              <span>
                {t('points.typeFilter', 'Type Filter')}: <strong>{t('points.active', 'Active')}</strong>
              </span>
            )}
            <span className="results-count">
              {points.length} {points.length === 1 ? t('points.result', 'result') : t('points.results', 'results')}
            </span>
            <button onClick={clearFilters} className="clear-filters-link">
              {t('points.clearAllFilters', 'Clear all filters')}
            </button>
          </div>
        )}

        <div className="points-list-stats">
          <span>{points.length} {points.length !== 1 ? t('map.points', 'points') : t('map.point', 'point')}</span>
        </div>
      </div>

      {points.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📍</div>
          <h2>{t('points.noPoints', 'No points yet')}</h2>
          <p>{t('points.noPointsDesc', 'Click on the map to create your first GPS point')}</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            {t('points.goToMap', 'Go to Map')}
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

              {point.type && (
                <div className="point-card-type">
                  🏷️ {point.type.name}
                </div>
              )}

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
