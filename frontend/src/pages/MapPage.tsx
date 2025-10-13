/**
 * Map page.
 *
 * Main map view with points and creation functionality.
 */

import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { Map as LeafletMap } from 'leaflet';
import { MapView } from '../components/map/MapView';
import { PointMarker } from '../components/map/PointMarker';
import { CreatePointModal } from '../components/map/CreatePointModal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { getPoints, searchPointsByTags, getTags } from '../api/points';
import { getErrorMessage } from '../api/client';
import type { GPSPoint, Tag } from '../types/point';
import './MapPage.css';

/**
 * Map page component.
 */
export function MapPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [points, setPoints] = useState<GPSPoint[]>([]);
  const [allPoints, setAllPoints] = useState<GPSPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Tags filter state
  const [tags, setTags] = useState<Tag[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Create point modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newPointLocation, setNewPointLocation] = useState<[number, number] | null>(null);

  /**
   * Load tags and points on mount, and restore filter from URL.
   */
  useEffect(() => {
    loadTags();
    loadPoints();

    // Restore filter from URL
    const tagsParam = searchParams.get('tags');
    if (tagsParam) {
      setSelectedTags(tagsParam.split(',').map(t => t.trim()));
      setIsFilterOpen(true);
    }
  }, []);

  /**
   * Apply filter when selected tags change.
   */
  useEffect(() => {
    if (selectedTags.length > 0) {
      filterPoints();
      // Update URL
      setSearchParams({ tags: selectedTags.join(',') });
    } else {
      setPoints(allPoints);
      // Clear URL params
      setSearchParams({});
    }
  }, [selectedTags, allPoints]);

  /**
   * Load tags from API.
   */
  const loadTags = async () => {
    try {
      const data = await getTags();
      setTags(data);
    } catch (err) {
      console.error('Error loading tags:', err);
    }
  };

  /**
   * Load points from API.
   */
  const loadPoints = async () => {
    setIsLoading(true);
    setError('');

    try {
      const data = await getPoints();
      setAllPoints(data);
      setPoints(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Filter points by selected tags.
   */
  const filterPoints = async () => {
    if (selectedTags.length === 0) {
      setPoints(allPoints);
      return;
    }

    try {
      const filtered = await searchPointsByTags(selectedTags);
      setPoints(filtered);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /**
   * Toggle tag selection.
   */
  const toggleTag = (tagName: string) => {
    setSelectedTags(prev =>
      prev.includes(tagName)
        ? prev.filter(t => t !== tagName)
        : [...prev, tagName]
    );
  };

  /**
   * Clear all filters.
   */
  const clearFilters = () => {
    setSelectedTags([]);
  };

  /**
   * Handle map ready.
   */
  const handleMapReady = (mapInstance: LeafletMap) => {
    // Add click handler to create points
    mapInstance.on('click', (e) => {
      setNewPointLocation([e.latlng.lat, e.latlng.lng]);
      setIsCreateModalOpen(true);
    });
  };

  /**
   * Handle point created.
   */
  const handlePointCreated = (point: GPSPoint) => {
    setAllPoints([...allPoints, point]);
    setPoints([...points, point]);
  };

  /**
   * Handle point click.
   */
  const handlePointClick = (point: GPSPoint) => {
    // TODO: Navigate to point detail page
    console.log('Point clicked:', point);
  };

  if (isLoading) {
    return <LoadingSpinner size="large" message="Loading map..." />;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error loading map</h2>
        <p>{error}</p>
        <button onClick={loadPoints} className="btn-primary">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="map-page">
      <MapView onMapReady={handleMapReady}>
        {/* Render point markers */}
        {points.map((point) => (
          <PointMarker
            key={point.id}
            point={point}
            onClick={handlePointClick}
          />
        ))}
      </MapView>

      {/* Create point modal */}
      {newPointLocation && (
        <CreatePointModal
          latitude={newPointLocation[0]}
          longitude={newPointLocation[1]}
          isOpen={isCreateModalOpen}
          onClose={() => {
            setIsCreateModalOpen(false);
            setNewPointLocation(null);
          }}
          onPointCreated={handlePointCreated}
        />
      )}

      {/* Map controls */}
      <div className="map-controls">
        <div className="points-count">
          {points.length} point{points.length !== 1 ? 's' : ''}
          {selectedTags.length > 0 && ` (filtered by ${selectedTags.length} tag${selectedTags.length > 1 ? 's' : ''})`}
        </div>

        {/* Filter toggle button */}
        <button
          className={`filter-toggle-button ${isFilterOpen ? 'active' : ''}`}
          onClick={() => setIsFilterOpen(!isFilterOpen)}
          title="Filter by tags"
        >
          🏷️ Filter Tags {selectedTags.length > 0 && `(${selectedTags.length})`}
        </button>
      </div>

      {/* Backdrop overlay */}
      {isFilterOpen && (
        <div
          className={`filter-backdrop ${isFilterOpen ? 'open' : ''}`}
          onClick={() => setIsFilterOpen(false)}
        />
      )}

      {/* Tags filter panel - Drawer style */}
      <div className={`tags-filter-panel ${isFilterOpen ? 'open' : ''}`}>
        <div className="filter-panel-header">
          <h3>Filter by Tags</h3>
          <button
            className="close-panel-button"
            onClick={() => setIsFilterOpen(false)}
            aria-label="Close filter panel"
          >
            ✕
          </button>
        </div>

        {selectedTags.length > 0 && (
          <div className="filter-panel-actions">
            <button
              className="clear-filters-button"
              onClick={clearFilters}
            >
              Clear All Filters
            </button>
            <div className="selected-count">
              {selectedTags.length} tag{selectedTags.length > 1 ? 's' : ''} selected
            </div>
          </div>
        )}

        <div className="tags-list">
          {tags.length === 0 ? (
            <p className="no-tags">No tags available</p>
          ) : (
            tags.map(tag => (
              <label key={tag.id} className="tag-checkbox">
                <input
                  type="checkbox"
                  checked={selectedTags.includes(tag.name)}
                  onChange={() => toggleTag(tag.name)}
                />
                <span className="tag-label">{tag.name}</span>
              </label>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
