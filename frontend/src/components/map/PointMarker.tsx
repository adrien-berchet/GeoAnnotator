/**
 * Point marker component.
 *
 * Displays GPS point as a marker on the map with custom icon and popup.
 */

import { Marker, Popup } from 'react-leaflet';
import { Icon, DivIcon } from 'leaflet';
import { Link } from 'react-router-dom';
import type { GPSPoint } from '../../types/point';
import { getPointTypeName } from '../../utils/pointTypeUtils';
import { useLanguage } from '../../contexts/LanguageContext';
import './PointMarker.css';

interface PointMarkerProps {
  point: GPSPoint;
  onClick?: (point: GPSPoint) => void;
}

/**
 * Create custom marker icon based on point type.
 */
const createMarkerIcon = (point: GPSPoint, typeName: string) => {
  // Always use custom marker with either icon or emoji
  const hasCustomIcon = point.type?.icon && point.type.icon !== '/icons/default.svg';
  const isUrlIcon = hasCustomIcon && (point.type.icon.startsWith('http') || point.type.icon.startsWith('/') || point.type.icon.startsWith('data:'));

  return new DivIcon({
    html: `
      <div class="custom-marker">
        <div class="marker-icon-container">
          ${hasCustomIcon
            ? isUrlIcon
              ? `<img src="${point.type.icon}" alt="${typeName}" class="marker-type-icon" />`
              : `<span class="marker-type-emoji">${point.type.icon}</span>`
            : '<span class="marker-type-emoji">📍</span>'
          }
        </div>
        <div class="marker-crosshair"></div>
      </div>
    `,
    className: 'custom-marker-wrapper',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40],
  });
};

/**
 * Point marker component.
 */
export function PointMarker({ point, onClick }: PointMarkerProps) {
  const { currentLanguage } = useLanguage();
  const typeName = point.type ? getPointTypeName(point.type, currentLanguage) : 'Point';
  const icon = createMarkerIcon(point, typeName);

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
                  point.type.icon.startsWith('http') || point.type.icon.startsWith('/') || point.type.icon.startsWith('data:') ? (
                    <img src={point.type.icon} alt="" className="type-icon-small" />
                  ) : (
                    <span className="type-icon-emoji">{point.type.icon}</span>
                  )
                )}
                <span className="type-name">{typeName}</span>
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
