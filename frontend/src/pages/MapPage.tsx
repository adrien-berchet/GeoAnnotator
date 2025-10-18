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
import { FilterPanel } from '../components/common/FilterPanel';
import { MapSearchBar } from '../components/map/MapSearchBar';
import { MapLayerSelector, TILE_LAYERS, type TileLayer } from '../components/map/MapLayerSelector';
import { getPoints, searchPointsByTags, getTags } from '../api/points';
import { getPointTypes } from '../api/types';
import { getErrorMessage } from '../api/client';
import type { GPSPoint, Tag, PointType } from '../types/point';
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

  // Search state
  const [searchQuery, setSearchQuery] = useState('');

  // Filter state
  const [tags, setTags] = useState<Tag[]>([]);
  const [types, setTypes] = useState<PointType[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Create point modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newPointLocation, setNewPointLocation] = useState<[number, number] | null>(null);

  // Map layer state
  const [currentTileLayer, setCurrentTileLayer] = useState<TileLayer>(TILE_LAYERS[0]);

  /**
   * Load tags, types, and points on mount, and restore filter from URL.
   */
  useEffect(() => {
    loadTags();
    loadTypes();
    loadPoints();

    // Restore filter from URL
    const tagsParam = searchParams.get('tags');
    const typesParam = searchParams.get('types');

    if (tagsParam) {
      setSelectedTags(tagsParam.split(',').map(t => t.trim()));
    }

    if (typesParam) {
      setSelectedTypes(typesParam.split(',').map(t => t.trim()));
    }
  }, []);

  /**
   * Apply filter when selected tags or types change.
   */
  useEffect(() => {
    applyFilters();
  }, [selectedTags, selectedTypes, searchQuery, allPoints]);

  /**
   * Apply tag, type, and search filters to points.
   */
  const applyFilters = async () => {
    let filteredPoints = allPoints;

    // Apply tag filter if tags are selected
    if (selectedTags.length > 0) {
      try {
        filteredPoints = await searchPointsByTags(selectedTags);
      } catch (err) {
        setError(getErrorMessage(err));
        return;
      }
    }

    // Apply type filter if types are selected
    if (selectedTypes.length > 0) {
      filteredPoints = filteredPoints.filter(point =>
        point.type && selectedTypes.includes(point.type.id)
      );
    }

    // Apply search filter if search query exists
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filteredPoints = filteredPoints.filter(point => {
        // Search in title, description, and tags
        const titleMatch = point.title?.toLowerCase().includes(query);
        const descMatch = point.description?.toLowerCase().includes(query);
        const tagsMatch = point.tags?.some(tag =>
          tag.name.toLowerCase().includes(query)
        );
        return titleMatch || descMatch || tagsMatch;
      });
    }

    setPoints(filteredPoints);

    // Update URL with filters
    const params: Record<string, string> = {};
    if (selectedTags.length > 0) {
      params.tags = selectedTags.join(',');
    }
    if (selectedTypes.length > 0) {
      params.types = selectedTypes.join(',');
    }
    if (searchQuery) {
      params.search = searchQuery;
    }
    setSearchParams(params);
  };

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
   * Load types from API.
   */
  const loadTypes = async () => {
    try {
      const data = await getPointTypes();
      setTypes(data);
    } catch (err) {
      console.error('Error loading types:', err);
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
   * Handle search query changes.
   */
  const handleSearch = (query: string) => {
    setSearchQuery(query);
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
   * Toggle type selection.
   */
  const toggleType = (typeId: string) => {
    setSelectedTypes(prev =>
      prev.includes(typeId)
        ? prev.filter(t => t !== typeId)
        : [...prev, typeId]
    );
  };

  /**
   * Clear all filters.
   */
  const clearAllFilters = () => {
    setSelectedTags([]);
    setSelectedTypes([]);
  };

  /**
   * Handle map ready.
   */
  const handleMapReady = (mapInstance: LeafletMap) => {
    let popupJustClosed = false;

    // Track when popups are closed
    mapInstance.on('popupclose', () => {
      popupJustClosed = true;
      // Reset the flag after a short delay
      setTimeout(() => {
        popupJustClosed = false;
      }, 100);
    });

    // Add click handler to create points
    mapInstance.on('click', (e) => {
      // Don't open create modal if a popup was just closed
      if (!popupJustClosed) {
        setNewPointLocation([e.latlng.lat, e.latlng.lng]);
        setIsCreateModalOpen(true);
      }
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
      <MapView onMapReady={handleMapReady} tileLayer={currentTileLayer}>
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
        {/* Search bar */}
        <MapSearchBar onSearch={handleSearch} />

        {/* Map layer selector */}
        <MapLayerSelector
          currentLayerId={currentTileLayer.id}
          onLayerChange={setCurrentTileLayer}
        />

        {/* Filter toggle button */}
        <button
          className={`filter-toggle-button ${isFilterOpen ? 'active' : ''}`}
          onClick={() => setIsFilterOpen(!isFilterOpen)}
          title="Filter points"
        >
          🔍 Filters {(selectedTags.length + selectedTypes.length) > 0 && `(${selectedTags.length + selectedTypes.length})`}
        </button>

        <div className="points-count">
          {points.length} point{points.length !== 1 ? 's' : ''}
          {selectedTags.length > 0 && ` (filtered by ${selectedTags.length} tag${selectedTags.length > 1 ? 's' : ''})`}
          {selectedTypes.length > 0 && ` (filtered by ${selectedTypes.length} type${selectedTypes.length > 1 ? 's' : ''})`}
          {searchQuery && ` (search: "${searchQuery}")`}
        </div>
      </div>

      {/* Filter Panel */}
      <FilterPanel
        isOpen={isFilterOpen}
        availableTags={tags}
        availableTypes={types}
        selectedTags={selectedTags}
        selectedTypes={selectedTypes}
        onClose={() => setIsFilterOpen(false)}
        onToggleTag={toggleTag}
        onToggleType={toggleType}
        onClearAll={clearAllFilters}
      />
    </div>
  );
}
