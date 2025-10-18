/**
 * Blue dot component for displaying device position on the map.
 *
 * Shows the user's current location as a blue pulsing marker.
 * Clicking the marker opens the point creation panel with the device position pre-filled.
 */

import { useEffect, useRef } from 'react';
import { Marker, Circle } from 'react-leaflet';
import L from 'leaflet';
import type { DevicePosition } from '../../hooks/useDevicePosition';
import './BlueDot.css';

/**
 * Create custom blue dot icon for the marker.
 */
const createBlueDotIcon = () => {
  return L.divIcon({
    className: 'blue-dot-icon',
    html: `
      <div class="blue-dot-outer" data-testid="blue-dot">
        <div class="blue-dot-inner"></div>
      </div>
    `,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

interface BlueDotProps {
  position: DevicePosition;
  onClick: () => void;
}

/**
 * Blue dot marker component showing device position.
 *
 * @param position - Device position coordinates
 * @param onClick - Callback when marker is clicked
 */
export function BlueDot({ position, onClick }: BlueDotProps) {
  const { latitude, longitude, accuracy } = position;
  const markerRef = useRef<L.Marker>(null);

  // Add custom data attributes to the marker element
  useEffect(() => {
    const marker = markerRef.current;
    if (marker) {
      const element = marker.getElement();
      if (element) {
        element.setAttribute('data-lat', latitude.toString());
        element.setAttribute('data-lng', longitude.toString());
      }
    }
  }, [latitude, longitude]);

  return (
    <>
      {/* Accuracy circle */}
      <Circle
        center={[latitude, longitude]}
        radius={accuracy}
        pathOptions={{
          color: '#4285F4',
          fillColor: '#4285F4',
          fillOpacity: 0.1,
          weight: 1,
        }}
      />

      {/* Blue dot marker */}
      <Marker
        ref={markerRef}
        position={[latitude, longitude]}
        icon={createBlueDotIcon()}
        eventHandlers={{
          click: onClick,
        }}
      >
        {/* No popup - clicking opens point creation panel */}
      </Marker>
    </>
  );
}
