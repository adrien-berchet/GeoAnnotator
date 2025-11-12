/**
 * Blue dot component for displaying device position on the map.
 *
 * Shows the user's current location as a blue pulsing marker.
 * Clicking the marker opens the point creation panel with the device position pre-filled.
 */

import { useEffect, useRef } from "react";
import { Marker, Circle, Polygon } from "react-leaflet";
import L from "leaflet";
import type { DevicePosition } from "../../hooks/useDevicePosition";
import "./BlueDot.css";

/**
 * Create custom blue dot icon for the marker.
 */
const createBlueDotIcon = () => {
  return L.divIcon({
    className: "blue-dot-icon",
    html: `
      <div class="blue-dot-outer" data-testid="blue-dot">
        <div class="blue-dot-inner"></div>
      </div>
    `,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

/**
 * Calculate the coordinates for a directional cone.
 *
 * @param lat - Center latitude
 * @param lng - Center longitude
 * @param heading - Compass direction in degrees (0-360)
 * @param distance - Distance from center to cone tip in meters
 * @param angle - Cone spread angle in degrees (default 45)
 * @returns Array of [lat, lng] points forming the cone
 */
const calculateConeCoordinates = (
  lat: number,
  lng: number,
  heading: number,
  distance: number = 50,
  angle: number = 45,
): [number, number][] => {
  // Convert heading to radians (0 degrees is north, clockwise)
  const headingRad = (heading * Math.PI) / 180;
  const halfAngleRad = (angle / 2) * (Math.PI / 180);

  // Earth radius in meters
  const R = 6371000;

  // Calculate tip of the cone
  const tipLat = lat + (distance / R) * Math.cos(headingRad) * (180 / Math.PI);
  const tipLng =
    lng +
    ((distance / R) * Math.sin(headingRad) * (180 / Math.PI)) /
      Math.cos((lat * Math.PI) / 180);

  // Calculate left edge of the cone
  const leftHeading = headingRad - halfAngleRad;
  const leftLat =
    lat + (distance / R) * Math.cos(leftHeading) * (180 / Math.PI);
  const leftLng =
    lng +
    ((distance / R) * Math.sin(leftHeading) * (180 / Math.PI)) /
      Math.cos((lat * Math.PI) / 180);

  // Calculate right edge of the cone
  const rightHeading = headingRad + halfAngleRad;
  const rightLat =
    lat + (distance / R) * Math.cos(rightHeading) * (180 / Math.PI);
  const rightLng =
    lng +
    ((distance / R) * Math.sin(rightHeading) * (180 / Math.PI)) /
      Math.cos((lat * Math.PI) / 180);

  // Return the cone as a triangle: center, left, tip, right, back to center
  return [
    [lat, lng],
    [leftLat, leftLng],
    [tipLat, tipLng],
    [rightLat, rightLng],
    [lat, lng],
  ];
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
  const { latitude, longitude, accuracy, heading } = position;
  const markerRef = useRef<L.Marker>(null);

  // Add custom data attributes to the marker element
  useEffect(() => {
    const marker = markerRef.current;
    if (marker) {
      const element = marker.getElement();
      if (element) {
        element.setAttribute("data-lat", latitude.toString());
        element.setAttribute("data-lng", longitude.toString());
      }
    }
  }, [latitude, longitude]);

  // Calculate cone coordinates if heading is available
  const coneCoordinates =
    heading !== null && heading >= 0
      ? calculateConeCoordinates(latitude, longitude, heading)
      : null;

  return (
    <>
      {/* Accuracy circle */}
      <Circle
        center={[latitude, longitude]}
        radius={accuracy}
        pathOptions={{
          color: "#4285F4",
          fillColor: "#4285F4",
          fillOpacity: 0.1,
          weight: 1,
        }}
      />

      {/* Directional cone (only shown when heading is available) */}
      {coneCoordinates && (
        <Polygon
          positions={coneCoordinates}
          pathOptions={{
            color: "#4285F4",
            fillColor: "#4285F4",
            fillOpacity: 0.3,
            weight: 2,
          }}
        />
      )}

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
