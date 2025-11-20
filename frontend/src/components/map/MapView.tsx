/**
 * Map view component.
 *
 * Displays interactive Leaflet map with tile layer, viewport management, and clustering.
 */

import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, useMap, ScaleControl } from "react-leaflet";
import type { Map as LeafletMap } from "leaflet";
import "leaflet/dist/leaflet.css";
import { initializeLeaflet } from "../../utils/leaflet-config";
import type { TileLayer as TileLayerType } from "./MapLayerSelector";

// Initialize Leaflet configuration
initializeLeaflet();

interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  onMapReady?: (map: LeafletMap) => void;
  children?: React.ReactNode;
  tileLayer?: TileLayerType;
}

/**
 * Component to handle map instance after initialization.
 */
function MapEventHandler({
  onMapReady,
}: {
  onMapReady?: (map: LeafletMap) => void;
}) {
  const map = useMap();

  useEffect(() => {
    if (onMapReady) {
      onMapReady(map);
    }
  }, [map, onMapReady]);

  return null;
}

/**
 * Map view component.
 */
export function MapView({
  center = [48.8566, 2.3522], // Default to Paris
  zoom = 13,
  onMapReady,
  children,
  tileLayer,
}: MapViewProps) {
  const mapRef = useRef<LeafletMap | null>(null);

  // Default tile layer (OpenStreetMap)
  const defaultLayer = {
    id: "osm",
    name: "Street Map",
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 22,
  };

  const activeLayer = tileLayer || defaultLayer;

  return (
    <div className="map-view-container">
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: "100%", width: "100%" }}
        ref={mapRef}
      >
        {/* Dynamic tile layer */}
        <TileLayer
          key={activeLayer.id}
          attribution={activeLayer.attribution}
          url={activeLayer.url}
          maxZoom={activeLayer.maxZoom}
        />

        {/* Map event handler */}
        <MapEventHandler onMapReady={onMapReady} />

        {/* Scale bar (bottom left) */}
        <ScaleControl position="bottomleft" />

        {/* Additional children (markers, popups, etc.) */}
        {children}
      </MapContainer>
    </div>
  );
}
