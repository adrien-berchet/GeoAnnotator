/**
 * Point marker component.
 *
 * Displays GPS point as a marker on the map with custom icon and popup.
 */

import { Marker, Popup } from 'react-leaflet';
import { Icon, DivIcon } from 'leaflet';
import { Link } from 'react-router-dom';
import type { GPSPoint } from '../../types/point';
import './PointMarker.css';

interface PointMarkerProps {
  point: GPSPoint;
  onClick?: (point: GPSPoint) => void;
}

/**
 * Create custom marker icon based on point type.
 */
const createMarkerIcon = (point: GPSPoint) => {
  // Always use custom marker with either icon or emoji
  const hasCustomIcon = point.type?.icon && point.type.icon !== '/icons/default.svg';

  return new DivIcon({
    html: `
      <div class="custom-marker">
        <div class="marker-icon-container">
          ${hasCustomIcon
            ? `<img src="${point.type.icon}" alt="${point.type.name}" class="marker-type-icon" />`
            : '<span class="marker-type-emoji">📍</span>'
          }
        </div>
        <div class="marker-crosshair"></div>
      </div>
    `,
    className: 'custom-marker-wrapper',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -20],
  });
};

/**
 * Point marker component.
 */
export function PointMarker({ point, onClick }: PointMarkerProps) {
  const icon = createMarkerIcon(point);

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
            {point.type && (
              <div className="point-popup-type">
                {point.type.icon && point.type.icon !== '/icons/default.svg' && (
                  <img src={point.type.icon} alt="" className="type-icon-small" />
                )}
                <span className="type-name">{point.type.name}</span>
              </div>
            )}
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
