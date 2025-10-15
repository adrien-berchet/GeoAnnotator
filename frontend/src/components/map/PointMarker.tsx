/**
 * Point marker component.
 *
 * Displays GPS point as a marker on the map with custom icon and popup.
 */

import { Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import { Link } from 'react-router-dom';
import type { GPSPoint } from '../../types/point';
import './PointMarker.css';

interface PointMarkerProps {
  point: GPSPoint;
  onClick?: (point: GPSPoint) => void;
}

/**
 * Create custom marker icon.
 */
const createMarkerIcon = (isPublic: boolean) => {
  const color = isPublic ? '#28a745' : '#007bff';

  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
        <path fill="${color}" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
      </svg>
    `)}`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  });
};

/**
 * Point marker component.
 */
export function PointMarker({ point, onClick }: PointMarkerProps) {
  const icon = createMarkerIcon(point.is_public);

  const handleClick = () => {
    if (onClick) {
      onClick(point);
    }
  };

  return (
    <Marker
      position={[point.latitude, point.longitude]}
      icon={icon}
      eventHandlers={{
        click: handleClick,
      }}
    >
      <Popup>
        <div className="point-popup">
          {/* Header with title */}
          <div className="point-popup-header">
            <h3>{point.title}</h3>
          </div>

          {/* Description if present */}
          {point.description && (
            <div
              className="point-popup-description"
              dangerouslySetInnerHTML={{ __html: point.description }}
            />
          )}

          {/* Meta information */}
          <div className="point-popup-meta">
            {/* Tags */}
            {point.tags.length > 0 && (
              <div className="point-popup-tags">
                {point.tags.map((tag) => (
                  <span key={tag.id} className="tag">
                    {tag.name}
                  </span>
                ))}
              </div>
            )}

            {/* Stats */}
            <div className="point-popup-stats">
              <span className="point-popup-stats-item">
                📝 {point.annotation_count} annotation{point.annotation_count !== 1 ? 's' : ''}
              </span>
              {point.is_public && (
                <span className="point-popup-badge-public">Public</span>
              )}
            </div>
          </div>

          {/* Action button */}
          <div className="point-popup-actions">
            <Link to={`/points/${point.id}`} className="point-popup-link">
              View details →
            </Link>
          </div>
        </div>
      </Popup>
    </Marker>
  );
}
