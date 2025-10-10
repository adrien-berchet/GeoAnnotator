/**
 * Map page.
 *
 * Main map view with points and creation functionality.
 */

import { useState, useEffect } from 'react';
import type { Map as LeafletMap } from 'leaflet';
import { MapView } from '../components/map/MapView';
import { PointMarker } from '../components/map/PointMarker';
import { CreatePointModal } from '../components/map/CreatePointModal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { getPoints } from '../api/points';
import { getErrorMessage } from '../api/client';
import type { GPSPoint } from '../types/point';

/**
 * Map page component.
 */
export function MapPage() {
  const [points, setPoints] = useState<GPSPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Create point modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newPointLocation, setNewPointLocation] = useState<[number, number] | null>(null);

  /**
   * Load points on mount.
   */
  useEffect(() => {
    loadPoints();
  }, []);

  /**
   * Load points from API.
   */
  const loadPoints = async () => {
    setIsLoading(true);
    setError('');

    try {
      const data = await getPoints();
      setPoints(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
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
        </div>
      </div>
    </div>
  );
}
