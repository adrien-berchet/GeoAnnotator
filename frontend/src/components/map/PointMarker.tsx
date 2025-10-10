/**
 * Point marker component.
 *
 * Displays GPS point as a marker on the map with custom icon and popup.
 */

import { Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import type { GPSPoint } from '../../types/point';

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
          <h3>{point.title}</h3>
          {point.description && (
            <div
              className="point-description"
              dangerouslySetInnerHTML={{ __html: point.description }}
            />
          )}
          <div className="point-meta">
            <div className="point-tags">
              {point.tags.map((tag) => (
                <span key={tag.id} className="tag">
                  {tag.name}
                </span>
              ))}
            </div>
            <div className="point-stats">
              <span>{point.annotation_count} annotations</span>
              {point.is_public && <span className="badge-public">Public</span>}
            </div>
          </div>
        </div>
      </Popup>
    </Marker>
  );
}
